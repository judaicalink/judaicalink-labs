import requests
import math
from django.http import HttpResponse
from django.shortcuts import render

from backend.models import Dataset
from elasticsearch import Elasticsearch
import json

# Create your views here.

#see labs/urls.py def index to access root with http://localhost:8000


def index(request):
    return HttpResponse(Dataset.objects.all())
    #return render(request, "search/root.html")

def search_index(request):
    return render(request, "search/search_index.html")

def load(request):
    with open('../data/textfile-djh.json', 'rb') as f:
        data = f.read()
        print(data)
        headers = {'content-type': 'application/json'}
        response = requests.post('http://localhost:9200/judaicalink/doc/_bulk?pretty', data=data, headers=headers)
        return HttpResponse(response)

def search(request, query, page):
    es = Elasticsearch()
    size = 10
    current_page = page -1

    if page > 1:
        current_page = current_page * size

    body = {
        "from" : current_page, "size" : size,
        "query" : {
            "query_string": {
                "query": query,
                "fields": ["name^4", "Alternatives^3", "birthDate", "birthLocation^2", "deathDate", "deathLocation^2", "Abstract", "Publication"]
            }

        },
        "highlight": {
            "fields": {
                "name": {},
                "Alternatives": {},
                "birthDate": {},
                "birthLocation": {},
                "deathDate": {},
                "deathLocation": {},
                "Abstract": {},
                "Publication": {}
            },
            'number_of_fragments': 0,
        }
    }
    result = es.search(index="judaicalink", body = body)
    
    # For testing, never commit with a hardcoded path like this
    # with open('/tmp/test.json', 'w') as f:
    #     json.dump(result, f)
    dataset = []
    for d in result ["hits"] ["hits"]:
        data = {
            "id" : d ["_id"],
            "source" : d ["_source"],
            "highlight" : d ["highlight"],
        }
        dataset.append (data)

    #replace data in source with data in highlight
    for d in dataset:
        for s in d ["source"]:
            if s in d ["highlight"]:
                d ["source"] [s] = d ["highlight"] [s] [0]

#    print (result)
    print (current_page)

    total_hits = result ["hits"] ["total"] ["value"]
    pages = math.ceil (total_hits / size)   #number of needed pages for paging
        #round up number of pages

    context = {
        "result" : result ["hits"] ["hits"],
            #contains full search results from elasticsearch
        "dataset" : dataset,
            #contains id and information from fields
        "pages" : pages,
        "total_hits" : total_hits,
        "range" : range (1, (pages + 1)),
        "page" : page,
        "query" : query,
    }
    return render (request, "search/search_result.html", context)

