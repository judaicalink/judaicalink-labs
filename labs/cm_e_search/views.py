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
# logger.setLevel(logging.DEBUG)
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
SOLR_SERVER = settings.SOLR_SERVER


def get_names():
    """
    This function gets all the names from the solr index cm_entity_names
    :return:
    """
    # gets all entity names from solr
    try:
        names = []

        solr = pysolr.Solr(SOLR_SERVER + "cm_entity_names", always_commit=True, timeout=10,
                           auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
        res = solr.search('*:*', index="cm_entity_names", rows=10000)

        # logging
        logger.info("Got names from solr: ")
        logger.debug("Names found: ", res.hits)
        logger.info(res.debug)
        logger.info(res.hits)

        for doc in res.docs:
            # convert list to string
            doc['name'] = ''.join(map(str, doc['name']))
            names.append(doc['name'])
            logger.debug("Doc: ", doc['name'])
            logger.info(doc['name'])
        return names

    except Exception as e:
        logger.error("Error:", e)
        print("Error:", e)
        return None
    except pysolr.SolrError as e:
        logger.error("Error:", e)
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
    logger.debug("Got names from solr: ")
    logger.debug(names)

    query = request.GET.get('query')
    logger.info("Query: " + query)
    print("Query: " + query)
    # add name: to query

    solr = pysolr.Solr(SOLR_SERVER + 'cm_entities', always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))

    fields = ["name", "e_type", "related_entities", 'ep', 'id', 'journal_occs.j_name', 'journal_occs.j_id',
              'journal_occs.first', 'journal_occs.last', 'journal_occs.mentions.p_id',
              'journal_occs.mentions.spot', 'journal_occs.mentions.start', 'journal_occs.mentions.end',
              'journal_occs.mentions.p_link', 'journal_occs.mentions.date', 'journal_occs.mentions.year']
    search_fields = ["name", "journal_occs.mentions.spot"]

    # create a dict from the fields and add the query
    # create a list for the fields that should be searched and add the query
    solr_query = [field + ':"' + query + '"' for field in search_fields]

    # build the body for solr
    body = {
        "hl": "false",
        "indent": "true",
        'fl': ','.join(fields),
        "start": 0,
        "q.op": "OR",
        "rows": 1000,
        "useParams": ""
    }

    res = solr.search(q=solr_query, search_handler="/select", **body)

    logger.debug("Results found: ", res.hits)
    logger.debug("Got results from solr: ")
    logger.debug(res.docs)

    results = []
    for doc in res.docs:
        doc['name'] = ''.join(map(str, doc['name']))
        doc['e_type'] = ''.join(map(str, doc['e_type']))
        if 'ep' in doc:
            doc['ep'] = ''.join(map(str, doc['ep']))
        else:
            doc['ep'] = ''

        print("Name: ", doc['name'])

        # create a dict for the related entities
        if 'related_entities' in doc:
            #print("Related entities: ", len(doc['related_entities'])/4)
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

                    #print("Entity: ", entity)
                    related_entities.append(entity)
                    entity = {}

            # Replace the whole data
            doc['related_entities'] = related_entities
        else:
            doc['related_entities'] = []

        # FIXME: Fix the results
        # check for journal occurrences
        # check if doc has journal_occs.j_name
        if 'journal_occs.j_name' in doc:
            print("Journal occs: ", doc['journal_occs.j_name'])
            # rebuild the occurrences
            # doc['occurrences'] = []
            # occurrence = {}

            print("Journal Occs: ", len(doc['journal_occs']))
            for journal_occ in doc['journal_occs']:
                print("\tJournal Name:", journal_occ.get('j_name'))
                #occurrence.append(journal_occ.get('j_name'))
                print("\tJournal ID:", journal_occ.get('j_id'))
                #occurrence.append(journal_occ.get('j_id'))
                print("\tFirst:", journal_occ.get('first'))
                #occurrence.append(journal_occ.get('first'))
                print("\tLast:", journal_occ.get('last'))
                #occurrence.append(journal_occ.get('last'))

                # Check if 'mentions' exists in the journal_occ
                mentions = journal_occ.get('mentions', [])
                for mention in mentions:
                    print("\t\tSpot:", mention.get('spot'))
                    print("\t\tStart:", mention.get('start'))
                    print("\t\tEnd:", mention.get('end'))
                    print("\t\tP ID:", mention.get('p_id'))
                    print("\t\tP Link:", mention.get('p_link'))
                    print("\t\tDate:", mention.get('date'))
                    print("\t\tYear:", mention.get('year'))

                #print("Occurrence: ", occurrence)

                # add the data to the results
                # results.append(doc)
                #doc['occurrences'].append(occurrence)


            #print("Occurences: ", doc['occurrences'])
        results.append(doc)

    #print("Results: ", results)
    context = {
        "results": results,
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
