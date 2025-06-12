import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)

# Map incoming query‐params → Solr field names
PARAM_FIELD_MAP = {
    'text':           'text',
    'name':           'name',
    'spot':           'spot',
    'uri':            'uri',
    'link':           'link',
    'alternatives':   'alternatives',
    'abstract':       'abstract',
    'date':           'date',
    'year':           'year',
    'birthDate':      'birthDate',
    'deathDate':      'deathDate',
    'birthLocation':  'birthLocation',
    'deathLocation':  'deathLocation',
    'dataslug':       'dataslug',
}

# Common Swagger Parameter definitions
Q_OP = openapi.Parameter(
    'q.op', openapi.IN_QUERY,
    description="Solr default operator", type=openapi.TYPE_STRING,
    enum=['AND','OR'], default='OR'
)
ROWS = openapi.Parameter('rows', openapi.IN_QUERY, description="Number of results", type=openapi.TYPE_INTEGER, default=10)
START= openapi.Parameter('start',openapi.IN_QUERY, description="Result offset", type=openapi.TYPE_INTEGER, default=0)
FQ   = openapi.Parameter('fq',   openapi.IN_QUERY, description="Filter query", type=openapi.TYPE_STRING)

# Build the manual_parameters list from our field map
FIELD_PARAMS = [
    openapi.Parameter(
        name=param, in_=openapi.IN_QUERY,
        description=f"{field} field search", type=openapi.TYPE_STRING
    )
    for param, field in PARAM_FIELD_MAP.items()
]

class SolrProxyBase(APIView):
    permission_classes = []
    renderer_classes = [JSONRenderer]

    def solr_proxy(self, request, core):
        # copy & pop so we don’t modify the original
        params = dict(request.query_params)
        default = {
            'wt':       'json',
            'q.op':     params.pop('q.op', ['OR'])[0],
            'useParams':params.pop('useParams', [''])[0],
            'indent':   params.pop('indent', ['true'])[0],
            'rows':     params.pop('rows', ['10'])[0],
            'start':    params.pop('start', ['0'])[0],
            'fq':       params.pop('fq', [''])[0],
        }

        # build `q`
        if 'q' in params:
            default['q'] = params.pop('q')[0]
        else:
            # assemble field:value clauses
            parts = []
            for param, field in PARAM_FIELD_MAP.items():
                if param in params:
                    parts.append(f"{field}:{params.pop(param)[0]}")
            default['q'] = " OR ".join(parts) if parts else "*:*"

        # merge back any other params (e.g. highlight, sort…)
        default.update({k: v[0] for k, v in params.items()})

        url_q = urlencode(default)
        cache_key = f"solr:{core}:{url_q}"
        if (cached := cache.get(cache_key)) is not None:
            return Response(cached)

        solr_url = f"{settings.SOLR_SERVER}{core}/select/?{url_q}"
        try:
            r = requests.get(solr_url, timeout=10)
            r.raise_for_status()
            data = r.json()
            cache.set(cache_key, data, 300)
            return Response(data)
        except requests.RequestException as e:
            logger.error(f"Solr proxy error: {e}")
            return Response(
                {'error': 'Solr proxy failure'},
                status=status.HTTP_502_BAD_GATEWAY
            )


class JudaicalinkProxy(SolrProxyBase):
    @swagger_auto_schema(
        operation_description="Search the Judaicalink core",
        manual_parameters=[*FIELD_PARAMS, Q_OP, ROWS, START, FQ],
        responses={200: openapi.Response('OK')}
    )
    def get(self, request):
        return self.solr_proxy(request, 'judaicalink')


class CMProxy(SolrProxyBase):
    @swagger_auto_schema(
        operation_description="Search the Compact Memory core",
        manual_parameters=[
            openapi.Parameter('text', openapi.IN_QUERY, "Fulltext", type=openapi.TYPE_STRING),
            ROWS, START
        ],
        responses={200: openapi.Response('OK')}
    )
    def get(self, request):
        return self.solr_proxy(request, 'cm')


class CMEntitiesProxy(SolrProxyBase):
    @swagger_auto_schema(
        operation_description="Search the CM Entities core",
        manual_parameters=[
            openapi.Parameter('spot',openapi.IN_QUERY,"Entity spot",type=openapi.TYPE_STRING),
            openapi.Parameter('date',openapi.IN_QUERY,"Full date",type=openapi.TYPE_STRING),
            openapi.Parameter('year',openapi.IN_QUERY,"Year",type=openapi.TYPE_STRING),
            ROWS, START, Q_OP
        ],
        responses={200: openapi.Response('OK')}
    )
    def get(self, request):
        return self.solr_proxy(request, 'cm_entities')


class CMEntityNamesProxy(SolrProxyBase):
    @swagger_auto_schema(
        operation_description="Search the CM Entity Names core",
        manual_parameters=[
            openapi.Parameter('name',openapi.IN_QUERY,"Entity name",type=openapi.TYPE_STRING),
            openapi.Parameter('uri', openapi.IN_QUERY,"URI",type=openapi.TYPE_STRING),
            ROWS, START, Q_OP
        ],
        responses={200: openapi.Response('OK')}
    )
    def get(self, request):
        return self.solr_proxy(request, 'cm_entity_names')


class CMMetaProxy(SolrProxyBase):
    @swagger_auto_schema(
        operation_description="Search the CM Meta core",
        manual_parameters=[
            openapi.Parameter('name',openapi.IN_QUERY,"Entity name",type=openapi.TYPE_STRING),
            openapi.Parameter('uri', openapi.IN_QUERY,"URI",type=openapi.TYPE_STRING),
            ROWS, START, Q_OP
        ],
        responses={200: openapi.Response('OK')}
    )
    def get(self, request):
        return self.solr_proxy(request, 'cm_meta')
