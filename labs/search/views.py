import requests
from django.http import HttpResponse
from django.shortcuts import render

from backend.models import Dataset
from elasticsearch import Elasticsearch

# Create your views here.


def index(request):
    #return HttpResponse(Dataset.objects.all())
    return render(request, "labs/root.html")


def load(request):
    with open('../data/textfile-djh.json', 'rb') as f:
        data = f.read()
        print(data)
        headers = {'content-type': 'application/json'}
        response = requests.post('http://localhost:9200/judaicalink/doc/_bulk?pretty', data=data, headers=headers)
        return HttpResponse(response)

def search(request, query):
    es = Elasticsearch()
    esquery = {
               'query_string': {
                'query': query,
                },
        }
    result = es.search(index="judaicalink", body={"query": esquery})

    dataset = []
    for d in result ["hits"] ["hits"]:
        data = {
            "id" : d ["_id"],
            "source" : d ["_source"],
        }
        dataset.append (data)

    context = {
        "result" : result ["hits"] ["hits"],
        "dataset" : dataset
    }
    return render (request, "labs/search_result.html", context)

