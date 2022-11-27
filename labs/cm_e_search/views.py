from django.shortcuts import render
from django.http import HttpResponse
from elasticsearch import Elasticsearch
import math, json, pprint
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT



CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


def get_names():

	names = []
	es = Elasticsearch(
		hosts=[settings.ELASTICSEARCH_SERVER],
		http_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
		ca_certs=settings.ELASTICSEARCH_SERVER_CERT,
		verify_certs=False,
		timeout=30,
		max_retries=10,
		retry_on_timeout=True,
	)
	res = es.search(index='cm_entity_names', body={'size': 7000, "query": {"match_all": {}}})

	for doc in res['hits']['hits']:
		names.append(doc['_source']['name'])

	return names



@cache_page(CACHE_TTL)
def index(request):

	names = get_names()
	data = names
	print(data)
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

	names = get_names()

	es = Elasticsearch(
		hosts=[settings.ELASTICSEARCH_SERVER],
		http_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
		ca_certs=settings.ELASTICSEARCH_SERVER_CERT,
		verify_certs=False,
		timeout=30,
		max_retries=10,
		retry_on_timeout=True,)
	query = request.GET.get('query')

	res = es.search(index='cm_entities', body={"query": {"match_phrase": {'name': query}}})

	result = []
	for doc in res['hits']['hits']:
		if doc['_source']['name'] == query:

			result.append(doc['_source'])
	#print(result[0]['related_entities'][0])
	#print(type(result[0]['related_entities'][0][2]))
	print(result)
	
	context = {
		"result": result,
		"data": json.dumps(names)
	}

	return render(request, 'cm_e_search/search_result.html', context)
