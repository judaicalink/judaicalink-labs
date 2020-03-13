from django.conf import settings

DATA_PREFIX = 'http://data.judaicalink.org/'
LOCAL_PREFIX = settings.LABS_ROOT + 'lod/'

SPARQL_ENDPOINT = settings.FUSEKI_SERVER + 'judaicalink/query'
