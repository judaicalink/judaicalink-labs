import requests
from django.http import HttpResponse
from django.shortcuts import render

from backend.models import Dataset
from elasticsearch import Elasticsearch

# Create your views here.


def index(request):
    return HttpResponse(Dataset.objects.all())


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
    res = ""
    for hit in result['hits']['hits']:
        print(hit)
        res += hit['_id']+'<br/>'
    return HttpResponse(res)

