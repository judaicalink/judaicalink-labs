from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from urllib.parse import urlencode
from django.conf import settings
from django.core.cache import cache
import requests


def solr_proxy(request, core):
    solr_params = request.query_params.dict()
    #print(f"Solr params: {solr_params}")
    default_params = {
        'wt': 'json',
        'q.op': solr_params.get('q.op', 'OR'),
        'useParams': solr_params.get('useParams', ''),
        'indent': solr_params.get('indent', 'true'),
        'rows': solr_params.get('rows', 10),
        'start': solr_params.get('start', 0),
        'fq': solr_params.get('fq', ''),
    }

    if 'q' in solr_params:
        default_params['q'] = solr_params['q']
    else:
        q_parts = []
        if 'text' in solr_params:
            q_parts.append(f"text:{solr_params['text']}\n")
            solr_params.pop('text')
        if 'name' in solr_params:
            q_parts.append(f"name:{solr_params['name']}\n")
            solr_params.pop('name')
        if 'spot' in solr_params:
            q_parts.append(f"spot:{solr_params['spot']}\n")
            solr_params.pop('spot')
        if 'uri' in solr_params:
            q_parts.append(f"uri:{solr_params['uri']}\n")
            solr_params.pop('uri')
        if 'link' in solr_params:
            q_parts.append(f"link:{solr_params['link']}\n")
            solr_params.pop('link')
        if 'Alternatives' in solr_params:
            q_parts.append(f"Alternatives:{solr_params['Alternatives']}\n")
            solr_params.pop('Alternatives')
        if 'Abstract' in solr_params:
            q_parts.append(f"Abstract:{solr_params['Abstract']}\n")
            solr_params.pop('Abstract')
        if 'date' in solr_params:
            q_parts.append(f"date:{solr_params['date']}\n")
            solr_params.pop('date')
        if 'year' in solr_params:
            q_parts.append(f"year:{solr_params['year']}\n")
            solr_params.pop('year')
        if 'birthDate' in solr_params:
            q_parts.append(f"birthDate:{solr_params['birthDate']}\n")
            solr_params.pop('birthDate')
        if 'deathDate' in solr_params:
            q_parts.append(f"birthDate:{solr_params['deathDate']}\n")
            solr_params.pop('deathDate')
        if 'birthLocation' in solr_params:
            q_parts.append(f"birthLocation:{solr_params['birthLocation']}\n")
            solr_params.pop('birthLocation')
        if 'deathLocation' in solr_params:
            q_parts.append(f"deathLocation:{solr_params['deathLocation']}\n")
            solr_params.pop('deathLocation')
        if 'dataslug' in solr_params:
            q_parts.append(f"birthDate:{solr_params['dataslug']}\n")
            solr_params.pop('dataslug')

        default_params['q'] = ' '.join(q_parts) if q_parts else '*:*'

        #return Response({'error': 'Invalid query'}, status=status.HTTP_400_BAD_REQUEST)


    solr_params.update(default_params)
    solr_query = urlencode(solr_params)
    cache_key = f"solr:{core}:{solr_query}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return Response(cached_response)
    solr_url = f"{settings.SOLR_SERVER}{core}/select/?{solr_query}"
    print(f"Proxying Solr request to {solr_url}")
    try:
        solr_response = requests.get(solr_url, timeout=10)
        solr_response.raise_for_status()
        solr_data = solr_response.json()
        cache.set(cache_key, solr_data, timeout=300)
        return Response(solr_data)
    except requests.RequestException as e:
        return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    # Add q.op to all views that use swagger_auto_schema

q_op_param = openapi.Parameter(
    'q.op', openapi.IN_QUERY,
    description="Query operator (default: OR)",
    type=openapi.TYPE_STRING,
    enum=['AND', 'OR'],
    default='OR'
)


class JudaicalinkProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Proxy Solr request to Judaicalink Search.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Name, e.g. `Aron`", type=openapi.TYPE_STRING),
            openapi.Parameter('Alternatives', openapi.IN_QUERY, description="Alternative Names, e.g. `Rabinowitsch`",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('Abstract', openapi.IN_QUERY, description="Abstract Description, e.g. `Rabbi`",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('link', openapi.IN_QUERY, description="URL, e.g. `Hirschfeld_Aron`",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('birthDate', openapi.IN_QUERY, description="Date, e.g. `1820`", type=openapi.TYPE_STRING),
            openapi.Parameter('deathDate', openapi.IN_QUERY, description="Date, e.g. `1885`", type=openapi.TYPE_STRING),
            openapi.Parameter('birthLocation', openapi.IN_QUERY, description="Place, e.g. `Hamburg`",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('deathLocation', openapi.IN_QUERY, description="Place, e.g. `Berlin`",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('fq', openapi.IN_QUERY, description="Filter query, e.g. `birthDate:1820`",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator (default: OR)",
                              type=openapi.TYPE_STRING, enum=['AND', 'OR'], default='OR'),
        ],
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "response": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "numFound": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "start": openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
                                "docs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "name": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                   items=openapi.Items(type=openapi.TYPE_STRING)),
                                            "birthDate": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                        items=openapi.Items(type=openapi.TYPE_STRING)),
                                            "id": openapi.Schema(type=openapi.TYPE_STRING),
                                            "dataslug": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                       items=openapi.Items(type=openapi.TYPE_STRING)),
                                            "link": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                   items=openapi.Items(type=openapi.TYPE_STRING)),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid query",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid query")
                    }
                )
            )
        }
    )
    def get(self, request):
        return solr_proxy(request, "judaicalink")


class CMProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request to Compact Memory for full-text search.",
        manual_parameters=[
            openapi.Parameter('text', openapi.IN_QUERY, description="Fulltext query (e.g. `Israelit`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "response": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "numFound": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "start": openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
                                "docs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_STRING),
                                            "text": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                   items=openapi.Items(type=openapi.TYPE_STRING)),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request (e.g. missing or malformed parameters)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid query")
                    }
                )
            )
        }
    )
    def get(self, request):
        return solr_proxy(request, "cm")


class CMEntitiesProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request to the Compact Memory Entities.",
        manual_parameters=[
            openapi.Parameter('spot', openapi.IN_QUERY, description="Entity mention (e.g. `Haifa`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('date', openapi.IN_QUERY, description="Full date (e.g. `1902-12-12`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('year', openapi.IN_QUERY, description="Year only (e.g. `1902`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator", type=openapi.TYPE_STRING,
                              enum=['AND', 'OR'], default='OR'),
        ],
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "response": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "numFound": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "start": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "docs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "p_id": openapi.Schema(type=openapi.TYPE_STRING),
                                            "spot": openapi.Schema(type=openapi.TYPE_STRING),
                                            "start": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "end": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "date": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                   items=openapi.Items(type=openapi.TYPE_STRING)),
                                            "year": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "id": openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid query")
                    }
                )
            )
        }
    )
    def get(self, request):
        return solr_proxy(request, "cm_entities")


class CMEntityNamesProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request to Compact Memory Entity Names.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Entity name (e.g. `Rosenzweig`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('uri', openapi.IN_QUERY, description="URI identifier (e.g. `Franz_Kafka`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator", type=openapi.TYPE_STRING,
                              enum=['AND', 'OR'], default='OR'),
        ],
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "response": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "numFound": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "start": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "docs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "name": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                   items=openapi.Items(type=openapi.TYPE_STRING)),
                                            "uri": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                  items=openapi.Items(type=openapi.TYPE_STRING)),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid query")
                    }
                )
            )
        }
    )
    def get(self, request):
        return solr_proxy(request, "cm_entity_names")

class CMMetaProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request to Compact Memory Entity Names.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Entity name (e.g. `Rosenzweig`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('uri', openapi.IN_QUERY, description="URI identifier (e.g. `Franz_Kafka`)",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator", type=openapi.TYPE_STRING,
                              enum=['AND', 'OR'], default='OR'),
        ],
        responses={
            200: openapi.Response(
                description="Successful response from the cm_entity_names core",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "response": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "numFound": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "start": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "docs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "name": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                   items=openapi.Items(type=openapi.TYPE_STRING)),
                                            "uri": openapi.Schema(type=openapi.TYPE_ARRAY,
                                                                  items=openapi.Items(type=openapi.TYPE_STRING)),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, example="Invalid query")
                    }
                )
            )
        }
    )
    def get(self, request):
        return solr_proxy(request, "cm_meta")
