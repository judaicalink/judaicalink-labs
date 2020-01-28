from django.conf import settings

DATA_PREFIX = 'http://data.judaicalink.org/'
LOCAL_PREFIX = 'http://localhost:8000/lod/'

SPARQL_ENDPOINT = settings.FUSEKI_SERVER + 'judaicalink/query'
