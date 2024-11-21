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
    names = get_names(request=request)  # Searches for all names in cm_entity_names

    query = request.GET.get('query', '')  # Default to an empty string if 'query' is not provided
    if not query:
        query = ''  # Ensure 'query' is a string

    solr = pysolr.Solr(SOLR_SERVER + 'cm_entities', always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))

    fields = ["name", "e_type", "related_entities", 'ep', 'id', 'journal_occs.j_name', 'journal_occs.j_id',
              'journal_occs.first', 'journal_occs.last', 'journal_occs.mentions.p_id',
              'journal_occs.mentions.spot', 'journal_occs.mentions.start', 'journal_occs.mentions.end',
              'journal_occs.mentions.p_link', 'journal_occs.mentions.date', 'journal_occs.mentions.year']

    search_fields = ["name", "spot"]

    # Create a list for the fields that should be searched and add the query
    solr_query = [field + ':"' + query + '"' for field in search_fields if query]  # Avoid empty queries

    # Build the body for Solr
    body = {
        "hl": "false",
        "indent": "true",
        'fl': '*,[child ]',
        "start": 0,
        "q.op": "OR",
        "rows": 1000,
        "useParams": ""
    }

    try:
        res = solr.search(q=solr_query, search_handler="/select", **body)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # Process the results
    results = []
    for doc in res.docs:
        doc['name'] = ''.join(map(str, doc['name']))
        doc['e_type'] = ''.join(map(str, doc['e_type']))
        if 'ep' in doc:
            doc['ep'] = ''.join(map(str, doc['ep']))
        else:
            doc['ep'] = ''

        if 'related_entities' in doc:
            related_entities = []
            entity = {}
            for index in range(0, len(doc['related_entities']), 4):
                if index + 3 < len(doc['related_entities']):
                    entity['ep'] = doc['related_entities'][index]
                    entity['name'] = doc['related_entities'][index + 1]
                    entity['score'] = doc['related_entities'][index + 2]
                    entity['type'] = doc['related_entities'][index + 3]
                    related_entities.append(entity)
                    entity = {}

            doc['related_entities'] = related_entities
        else:
            doc['related_entities'] = []

        results.append(doc)

    context = {
        "results": results,
        "data": json.dumps(names)
    }

    return render(request, 'cm_e_search/search_result.html', context)



def get_names_json(request):
    names = get_names(request=request)
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
