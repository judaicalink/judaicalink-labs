from django.shortcuts import render
from django.http import HttpResponse
from elasticsearch import Elasticsearch
import math




def index(request):
    
    return render(request, 'cm_search/search_index.html')


def result(request):
	
	# hardcoded list of journals that do not have external access on visual library UB Fra
	blacklist = ('2431292', '2823768', '10112841', '4086896', '9038025', '4875667', '7938572', '8553624', '8823924', '9498581', '9572329', '9616703', '9620162')

	es = Elasticsearch()
	query = request.GET.get('query')
	page = int (request.GET.get('page'))
	size = 10
		#changed size from 15 to 10 to match the amount of results in judaicalink search
	start = (page - 1) * size
	res = es.search(index='cm', body={"query": {"match": {'text': query}}, 'size': size, 'from': start, 'highlight': {'fields': {'text': {}}}    })
		#added 'from': start, to indicate which results should be displayed
			#'from' is used to tell elasticsearch which results to return by index
		# -> if page = 1 then results 0-9 will be displayed
		# -> if page = 2 then results 10-19 and so on

	result = []
	for doc in res['hits']['hits']:
		
		formatted_doc = {}

		# chunk the id string and build the links to cm frankfurt (journal, volume, issue)
		chunks = doc['_id'].split('_')

		journal_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/"+chunks[0]
		volume_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/"+chunks[1]
		issue_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/"+chunks[2]
		page_link = "http://sammlungen.ub.uni-frankfurt.de/cm/periodical/pageview/"+chunks[-1]

		formatted_doc['jl'] = journal_link
		formatted_doc['vl'] = volume_link
		formatted_doc['il'] = issue_link


		if chunks[0] in blacklist:
			formatted_doc['plink'] = ''
		else:
			formatted_doc['plink'] = page_link

		formatted_doc['page'] = chunks[-2]
		formatted_doc['id'] = doc['_id']
		formatted_doc['score'] = round(doc['_score'], 2)
		formatted_doc['text'] = doc['_source']['text']
		formatted_doc['highlight'] = doc['highlight']['text']

		result.append(formatted_doc)

	#paging
	# -> almost copy from jl-search, except some variable-names

	total_hits = res['hits']['total'] ['value']
	pages = math.ceil (total_hits / size)
		#pages containes necessary amount of pages for paging

	paging = []
	#if page = 1 will contain -2, -1, 0, 1, 2, 3, 4

	paging.append (page - 3)
	paging.append (page - 2)
	paging.append (page - 1)
	paging.append (page)
	paging.append (page + 1)
	paging.append (page + 2)
	paging.append (page + 3)

	real_paging = []
	#if page = 1 will contain 1, 2, 3, 4
	#-> non-existing pages are removed

	for number in paging:
		if number > 1 and number < pages:
			real_paging.append (number)

	context = {
		"result": result,
		"total_hits": res['hits']['total']['value'],
		"query": query,
		"pages" : pages,
		"previous" : page - 1,
		"page" : page,
		"next" : page + 1,
		"paging" : real_paging,

	}

	return render(request, 'cm_search/search_result.html', context)
