import requests
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

def search(request, query):
    es = Elasticsearch()

    body = {
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
            'number_of_fragments': 0
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
        }
        dataset.append (data)

    context = {
        "result" : result ["hits"] ["hits"],
            #contains full search results from elasticsearch
        "dataset" : dataset
            #contains id and information from fields
    }
    return render (request, "search/search_result.html", context)

