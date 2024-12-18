import logging
import html
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import pysolr
import math, json, pprint
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger('labs')
logger.setLevel(logging.DEBUG)
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
SOLR_SERVER = settings.SOLR_SERVER


def get_names():
    """
    This function gets all the names from the solr index cm_entity_names
    :return: list of names
    """
    # gets all entity names from solr
    try:
        names = []

        solr = pysolr.Solr(SOLR_SERVER + "cm_entity_names", always_commit=True, timeout=10,
                           auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
        res = solr.search('*:*', index="cm_entity_names", rows=10000)

        # logging
        logger.debug("Got names from solr: ")
        logger.debug("Names found: %s", res.hits)
        logger.debug(res.hits)

        for doc in res.docs:
            # convert list to string
            doc['name'] = ''.join(map(str, doc['name']))
            names.append(html.escape(doc['name']).replace("'", "\\'").replace('"', '\\"'))
            #logger.debug("Doc: %s", doc['name'])
        # sort names alphabetically
        names.sort()
        return names

    except Exception as e:
        logger.error("Error: %s", e)
        return None
    except pysolr.SolrError as e:
        logger.error("Error: %s", e)
        return None


@cache_page(CACHE_TTL)
def index(request):
    names = get_names()
    data = names
    context = {'data': data}
    return render(request, 'cm_e_search/search_index.html', context)


@cache_page(CACHE_TTL)
def result(request):
    names = get_names()

    query = request.GET.get('query', '')  # Safely get the query with a default value

    solr = pysolr.Solr(SOLR_SERVER + 'cm_entities', always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))

    fields = ["name", "e_type", "related_entities", 'ep', 'id', 'journal_occs.j_name', 'journal_occs.j_id',
              'journal_occs.first', 'journal_occs.last', 'journal_occs.mentions.p_id',
              'journal_occs.mentions.spot', 'journal_occs.mentions.start', 'journal_occs.mentions.end',
              'journal_occs.mentions.p_link', 'journal_occs.mentions.date', 'journal_occs.mentions.year']

    search_fields = ["name", "spot"]

    # Safely build the query list
    solr_query = [field + ':"' + (query or '') + '"' for field in search_fields]

    # Build Solr search body
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

    results = []
    for doc in res.docs:
        doc['name'] = ''.join(map(str, doc.get('name', '')))
        doc['e_type'] = ''.join(map(str, doc.get('e_type', '')))
        doc['ep'] = ''.join(map(str, doc.get('ep', ''))) if 'ep' in doc else ''

        related_entities = []
        if 'related_entities' in doc:
            for index in range(0, len(doc['related_entities']), 4):
                if index + 3 < len(doc['related_entities']):
                    entity = {
                        'ep': doc['related_entities'][index] or '',
                        'name': doc['related_entities'][index + 1] or '',
                        'score': doc['related_entities'][index + 2] or '',
                        'type': doc['related_entities'][index + 3] or '',
                    }
                    related_entities.append(entity)
        doc['related_entities'] = related_entities

        results.append(doc)
        
    """
    Occurs in journals
    Todo get the nested documents for:
    * docs
        * name
        * entity_type: String
        * entity_page: String (URL)
        * journal_occurrences (nested, multiple)
            * journal_name: String
            * journal_id: Int
            * first: Int
            * last: Int
            * mentions (nested, multiple)
                * person_id: Int
                * spot: String
                * start: Int
                * end: Int
                * person_link: String 
                * date: String or Date
                * year: Int
        * related_entities (nested, multiple)
            * name: String
            * url: String
            * score: Float
            * type: String
    """

    context = {
        "results": results,
        "data": json.dumps(names or [])
    }

    return render(request, 'cm_e_search/search_result.html', context)



def get_names_json(request):
    names = get_names()
    logger.debug("Names: %s", names)
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
