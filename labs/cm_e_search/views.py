# Views for CM Entity Search
import logging
import html
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import pysolr
import math, json, pprint
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
SOLR_SERVER = settings.SOLR_SERVER


def get_names(request):
    query = request.GET.get('query', '')
    start = int(request.GET.get('start', 0))
    rows = int(request.GET.get('rows', 20))

    solr = pysolr.Solr(SOLR_SERVER + "cm_entity_names", always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
    res = solr.search(f'name:*{query}*', start=start, rows=rows)
    results = [{'id': doc['id'], 'name': doc['name']} for doc in res.docs]

    return JsonResponse({'results': results})


@cache_page(CACHE_TTL)
def index(request):
    names = get_names(request=request)
    data = names
    context = {'data': data}
    return render(request, 'cm_e_search/search_index.html', context)


@cache_page(CACHE_TTL)
def result(request):
    names = get_names(request=request)  # searches for all names in cm_entity_names
    #logger.debug("Got names from solr: %s", names)

    query = request.GET.get('query')
    #logger.info("Query: %s",  query)
    # add name: to query

    solr = pysolr.Solr(SOLR_SERVER + 'cm_entities', always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))

    fields = ["name", "e_type", "related_entities", 'ep', 'id', 'journal_occs.j_name', 'journal_occs.j_id',
              'journal_occs.first', 'journal_occs.last', 'journal_occs.mentions.p_id',
              'journal_occs.mentions.spot', 'journal_occs.mentions.start', 'journal_occs.mentions.end',
              'journal_occs.mentions.p_link', 'journal_occs.mentions.date', 'journal_occs.mentions.year']

    search_fields = ["name", "spot"]

    # create a dict from the fields and add the query
    # create a list for the fields that should be searched and add the query
    solr_query = [field + ':"' + query + '"' for field in search_fields]

    # build the body for solr
    body = {
        "hl": "false",
        "indent": "true",
        'fl': '*,[child ]',
        "start": 0,
        "q.op": "OR",
        "rows": 1000,
        "useParams": ""
    }

    res = solr.search(q=solr_query, search_handler="/select", **body)

    #logger.info("Results found: %s", res.hits)
    #logger.info("Got results from solr: %s", res.docs)

    results = []
    for doc in res.docs:
        doc['name'] = ''.join(map(str, doc['name']))
        doc['e_type'] = ''.join(map(str, doc['e_type']))
        if 'ep' in doc:
            doc['ep'] = ''.join(map(str, doc['ep']))
        else:
            doc['ep'] = ''

        logger.info("Name: %s", doc['name'])

        # create a dict for the related entities
        if 'related_entities' in doc:
            #logger.info("Related entities: ", len(doc['related_entities'])/4)
            related_entities = []
            entity = {}
            for index in range(0, len(doc['related_entities']), 4):
                if index + 3 < len(doc['related_entities']):
                    # entity is a list with 4 elements
                    # 0: ep - entity page
                    # 1: name
                    # 2: score
                    # 3: type
                    entity['ep'] = doc['related_entities'][index]
                    entity['name'] = doc['related_entities'][index + 1]
                    entity['score'] = doc['related_entities'][index + 2]
                    entity['type'] = doc['related_entities'][index + 3]

                    #logger.info("Entity: ", entity)
                    related_entities.append(entity)
                    entity = {}

            # Replace the whole data
            doc['related_entities'] = related_entities
        else:
            doc['related_entities'] = []

        # FIXME: Fix the results
        # check for journal occurrences
        # check if doc has journal_occs.j_name
        #if 'journal_occs' in doc:
        #    for occurrence in doc['journal_occs']:
        #        logger.info("Journal occs: ", occurrence['j_name'])

        results.append(doc)

    #print("Results: ", results)
    context = {
        "results": results,
        "data": json.dumps(names)
    }

    return render(request, 'cm_e_search/search_result.html', context)


def get_names_json(request):
    names = get_names()
    return JsonResponse({'names': names})


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
