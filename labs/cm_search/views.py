from django.shortcuts import render
from django.http import HttpResponse
from elasticsearch import Elasticsearch




def index(request):
    
    return render(request, 'cm_search/search_index.html')


def result(request):
	#query = request.GET.get('query')
	#context = {'query': query}
	#return render(request, 'cm_search/search_result.html', context)

	es = Elasticsearch()
	query = request.GET.get('query')
	size = 15
	res = es.search(index='cm', body={"query": {"match": {'text': query}}, 'size': size, 'highlight': {'fields': {'text': {}}}    })

	result = []
	for doc in res['hits']['hits']:
		
		formatted_doc = {}

		# chunk the id string and build the links to cm frankfurt (journal, volume, issue)
		chunks = doc['_id'].split('_')

		journal_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/"+chunks[0]
		volume_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/"+chunks[1]
		issue_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/"+chunks[2]

		formatted_doc['jl'] = journal_link
		formatted_doc['vl'] = volume_link
		formatted_doc['il'] = issue_link
		formatted_doc['page'] = chunks[-1]

		formatted_doc['id'] = doc['_id']
		formatted_doc['score'] = round(doc['_score'], 2)
		formatted_doc['text'] = doc['_source']['text']
		formatted_doc['highlight'] = doc['highlight']['text']

		result.append(formatted_doc)

	context = {
		"result": result,
		"total_hits": res['hits']['total']['value'],
		"query": query
	}

	return render(request, 'cm_search/search_result.html', context)
	