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
            openapi.Parameter('Alternatives', openapi.IN_QUERY, description="Alternative Names, e.g. `Rabinowitsch`", type=openapi.TYPE_STRING),
            openapi.Parameter('Abstract', openapi.IN_QUERY, description="Abstract Description, e.g. `Rabbi`", type=openapi.TYPE_STRING),
            openapi.Parameter('link', openapi.IN_QUERY, description="URL, e.g. `Hirschfeld_Aron`", type=openapi.TYPE_STRING),
            openapi.Parameter('birthDate', openapi.IN_QUERY, description="Date, e.g. `1820`", type=openapi.TYPE_STRING),
            openapi.Parameter('deathDate', openapi.IN_QUERY, description="Date, e.g. `1885`", type=openapi.TYPE_STRING),
            openapi.Parameter('birthLocation', openapi.IN_QUERY, description="Place, e.g. `Hamburg`", type=openapi.TYPE_STRING),
            openapi.Parameter('deathLocation', openapi.IN_QUERY, description="Place, e.g. `Berlin`", type=openapi.TYPE_STRING),
            openapi.Parameter('fq', openapi.IN_QUERY, description="Filter query, e.g. `birthDate:1820`", type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator (default: OR)", type=openapi.TYPE_STRING, enum=['AND', 'OR'], default='OR'),
        ],
        responses={200: openapi.Response(description="Example result", examples={"application/json": {
            "response": {
                "numFound": 1,
                "start": 0,
                "docs": [{
                    "name": ["Sandfort, Paul Aron"],
                    "birthDate": ["1820"],
                    "id": "63747260-3649-427a-ac9c-aed44e801410",
                    "dataslug": ["gnd"],
                    "link": ["http://data.judaicalink.org/data/gnd/121923053"]
                }]
            }}})}
    )
    def get(self, request):
        return solr_proxy(request, "judaicalink")


class CMProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Proxy Solr request to cm core (text search only).",
        manual_parameters=[
            openapi.Parameter('text', openapi.IN_QUERY, description="Fulltext query, e.g. `Israelit`", type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
        ],
        responses={200: openapi.Response(description="Example result", examples={"application/json": {
            "response": {
                "numFound": 1,
                "start": 0,
                "docs": [{
                    "id": "92a97098-a5b6-4590-a530-827a653e42e2",
                    "text": ["128 Bayerische Israelitische Gemeindezeitung ..."]
                }]
            }}})}
    )
    def get(self, request):
        return solr_proxy(request, "cm")


class CMEntitiesProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Proxy Solr request to Compact Memory Entities.",
        manual_parameters=[
            openapi.Parameter('spot', openapi.IN_QUERY, description="Spot text (e.g. `Haifa`)", type=openapi.TYPE_STRING),
            openapi.Parameter('date', openapi.IN_QUERY, description="Date (e.g. `1902-12-12`)", type=openapi.TYPE_STRING),
            openapi.Parameter('year', openapi.IN_QUERY, description="Year (e.g. `1902`)", type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator (default: OR)",
                              type=openapi.TYPE_STRING, enum=['AND', 'OR'], default='OR'),
        ],
        responses={200: openapi.Response(description="Example result", examples={"application/json": {
            "response": {
                "numFound": 1,
                "start": 0,
                "docs": [{
                    "p_id": "2656877",
                    "spot": "Haifa",
                    "start": 4891,
                    "end": 4896,
                    "date": ["1902-12-12"],
                    "year": 1902,
                    "id": "df763...#0/mentions#0"
                }]
            }}})}
    )
    def get(self, request):
        return solr_proxy(request, "cm_entities")


class CMEntityNamesProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Proxy Solr request to Compact Memory Entity Names.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_QUERY, description="Name (e.g. `Rosenzweig`)", type=openapi.TYPE_STRING),
            openapi.Parameter('uri', openapi.IN_QUERY, description="Name (e.g. `Franz_Kafka`)", type=openapi.TYPE_STRING),
            openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator (default: OR)",
                              type=openapi.TYPE_STRING, enum=['AND', 'OR'], default='OR'),
        ],
        responses={200: openapi.Response(description="Example result", examples={"application/json": {
            "response": {
                "numFound": 1,
                "start": 0,
                "docs": [{
                    "name": ["Franz Mehring"],
                    "uri": ["http://data.judaicalink.org/data/dbpedia/Franz_Mehring"]
                }]
            }}})}
    )
    def get(self, request):
        return solr_proxy(request, "cm_entity_names")

class CMMetaProxy(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Proxy Solr request to Compact Memory Meta.",
        manual_parameters=[
            openapi.Parameter('text', openapi.IN_QUERY, description="Fulltext query in article text", type=openapi.TYPE_STRING),
            openapi.Parameter('dateIssued', openapi.IN_QUERY, description="Publication date (e.g. `1913-02-28T00:00:00Z`)", type=openapi.TYPE_STRING),
            openapi.Parameter('j_title', openapi.IN_QUERY, description="Journal title (e.g. `Die Welt`)", type=openapi.TYPE_STRING),
            openapi.Parameter('volume', openapi.IN_QUERY, description="Journal volume (e.g. `1835`)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('heft', openapi.IN_QUERY, description="Journal issue (e.g. `1913`)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('start', openapi.IN_QUERY, description="Pagination offset", type=openapi.TYPE_INTEGER),
            openapi.Parameter('q.op', openapi.IN_QUERY, description="Query operator (default: OR)",
                              type=openapi.TYPE_STRING, enum=['AND', 'OR'], default='OR'),
        ],
        responses={200: openapi.Response(description="Example result", examples={"application/json": {
            "response": {
                "numFound": 1,
                "start": 0,
                "docs": [{
                    "text": ["DIE WELT BERLIN W15, SÄCHSISCHE STR. 8. ERSCHEINT ..."],
                    "dateIssued": ["1913-02-28T00:00:00Z"],
                    "j_title": ["Die Welt"],
                    "volume": ["8 (1835)"],
                    "heft": ["9 (28.2.1913)"],
                    "id": "02f7cebf-bd41-44ae-97e6-4bfe3f10c07c"
                }]
            }}})}
    )
    def get(self, request):
        return solr_proxy(request, "cm_meta")
