import logging

from django.shortcuts import render
from django.http import HttpResponse
import pysolr
import math, json, pprint
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT



CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
SOLR_SERVER = settings.SOLR_SERVER
SOLR_INDEX = "cm_entity_names"

def get_names():
	# gets all entity names from solr
	try:
		names = []
		solr = pysolr.Solr(SOLR_SERVER + SOLR_INDEX, always_commit=True, timeout=10, auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
		res = solr.search('*.*', index=SOLR_INDEX, rows=10000)
		logging.debug("Got names from solr: ")
		logging.debug(res)

		for doc in res:
			names.append(doc['name'])
			logging.debug(doc['name'])
		return names
	except Exception as e:
		logging.error(e)
		return None
	except pysolr.SolrError as e:
		logging.error(e)
		return None


@cache_page(CACHE_TTL)
def index(request):

	names = get_names()
	data = names
	logging.DEBUG(data)
	context = {'data': data}

	return render(request, 'cm_e_search/search_index.html', context)


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

@cache_page(CACHE_TTL)
def result(request):

	names = get_names() # searches for all names in cm_entity_names
	logging.debug("Name s: \n", names)

	query = request.GET.get('query')

	solr = pysolr.Solr(settings.SOLR_SERVER + 'cm_entities', always_commit=True, timeout=10, auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))

	res = solr.search(query, index='cm_entities', rows=10000)
	logging.info("Got results from solr: ")
	logging.info(res)

	result = []
	for doc in res:
		if doc['name'] == query:

			result.append(doc)
	#print(result[0]['related_entities'][0])
	#print(type(result[0]['related_entities'][0][2]))
	print(result)
	
	context = {
		"result": result,
		"data": json.dumps(names)
	}

	return render(request, 'cm_e_search/search_result.html', context)
