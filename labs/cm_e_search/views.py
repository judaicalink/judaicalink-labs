import logging
import html
from django.shortcuts import render
from django.http import HttpResponse
import pysolr
import math, json, pprint
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
SOLR_SERVER = settings.SOLR_SERVER

def get_names():
    # gets all entity names from solr
    try:
        names = []
        solr = pysolr.Solr(SOLR_SERVER + "cm_entity_names", always_commit=True, timeout=10,
                           auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
        res = solr.search('*:*', index="cm_entity_names", rows=10000)
        logger.info("Got names from solr: ")
        #print(res.hits)
        #print(res.docs)
        #print(res.debug)
        logger.info(res.debug)
        logger.info(res.hits)

        for doc in res.docs:
            names.append(doc['name'])
            #print("Doc: ", doc['name'])
            logger.info(doc['name'])
        return names
    except Exception as e:
        logger.error(e)
        print("Error:", e)
        return None
    except pysolr.SolrError as e:
        logger.error(e)
        print("Error:", e)
        return None


@cache_page(CACHE_TTL)
def index(request):
    names = get_names()
    data = names
    context = {'data': data}

    return render(request, 'cm_e_search/search_index.html', context)


@cache_page(CACHE_TTL)
def result(request):
    names = get_names()  # searches for all names in cm_entity_names
    print("Got names from solr: ")
    print(names

    query = request.GET.get('query')
    logger.info("Query: " + query)
    print("Query: " + query)

    solr = pysolr.Solr(settings.SOLR_SERVER + 'cm_entities', always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
    print("Solr: " + str(solr))
    res = solr.search(query, index='cm_entities', rows=10000)
    logger.info("Got results from solr: ")
    logger.info(res.debug)
    logger.info(res.docs)
    print("Got results from solr: ")
    print(res.debug)
    print(res.docs)
    print(res.hits)


    result = []
    for doc in res.docs:
        if doc['name'] == query:
            result.append(doc)
            print("Doc: ", doc['name'])
    # print(result[0]['related_entities'][0])
    # print(type(result[0]['related_entities'][0][2]))

    context = {
        "result": result,
        "data": json.dumps(names)
    }

    return render(request, 'cm_e_search/search_result.html', context)


def create_map(result):
    # creates a map from locations
    locations = []
    for r in result:
        if r.e_type == 'LOC':
            locations.append(r.name)
    pass


def create_timeline():
    pass


def create_graph_visualization():
    pass