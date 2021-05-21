import requests
import math
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings

from data.models import Dataset
from elasticsearch import Elasticsearch
import json

# Create your views here.

#see labs/urls.py def index to access root with http://localhost:8000

def custom_error_404(request, exception):
    return render(request, 'search/404.html', {})

def custom_error_500(request):
    return render(request, 'search/500.html', {})

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
        response = requests.post(f'http://localhost:9200/{settings.JUDAICALINK_INDEX}/doc/_bulk?pretty', data=data, headers=headers)
        return HttpResponse(response)

def search (request):
    query = request.GET.get ('lookfor')
    page = int (request.GET.get ('page'))
    context = process_query (query, page)
    return render (request, 'search/search_result.html', context)

def process_query (query, page):
    page = int (page)
    es = Elasticsearch()
    size = 10
    start = (page - 1) * size

    body = {
        "from" : start, "size" : size,
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
                "Publication": {},
            },
            'number_of_fragments': 0,
        }
    }
    result = es.search(index=settings.JUDAICALINK_INDEX, body = body)

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


    field_order = ["name", "Alternatives", "birthDate", "birthYear", "birthLocation", "deathDate", "deathYear", "deathLocation", "Abstract", "Publication"]

    dataset_objects = Dataset.objects.all()
    dataslug_to_dataset = {}
    for i in dataset_objects:
        dataslug_to_dataset [i.dataslug] = i.title

    ordered_dataset = []
    for d in dataset:
        data = []

        #linking to detailed view
        id = "<a href='" + d ["id"] + "'>" + d ["source"] ["name"] + "</a>"
        # d ["id"] = http://data.judaicalink.org/data/dbpedia/Siegfried_Einstein
        source_dataset = '<b>' + 'Source: ' + '</b>' + '<span class ="badge badge-info">' + d ["id"].split("/")[-2] + '</span>'
        # source_dataset = dbpedia
        data.append (id)
        data.append(source_dataset)

        #extracting fields (named in field_order) and ordering them like field_order
        for field in field_order:
            if field in d ["source"] and d ["source"] [field] != "NA":
                pretty_fieldname = field.capitalize()
                temp_data = "<b>" + pretty_fieldname + ": " + "</b>" + d ["source"] [field]
                data.append (temp_data)

        #extracting additional fields (that are not mentioned in field_order)
        for field in d ["source"]:
            if field not in field_order:
                pretty_fieldname = field.capitalize()
                temp_data = "<b>" + pretty_fieldname + ": " + "</b>" + d ["source"] [field]
                data.append (temp_data)
        ordered_dataset.append (data)

    total_hits = result ["hits"] ["total"] ["value"]
    pages = math.ceil (total_hits / size)   #number of needed pages for paging
        #round up number of pages

    paging = []
    #if page = 1, paging contains -2, -1, 0, 1, 2, 3, 4

    paging.append (page - 3)
    paging.append (page - 2)
    paging.append (page - 1)
    paging.append (page)
    paging.append (page + 1)
    paging.append (page + 2)
    paging.append (page + 3)

    real_paging = []
    #if page = 1, paging contains 1, 2, 3, 4
        #-> non-existing (like -2, -1, ...) pages are removed

    for number in paging:
        if number > 1 and number < pages:
            real_paging.append (number)

    context = {
        "pages" : pages,
        "paging" : real_paging,
        "next" : page + 1,
        "previous" : page -1,
        "total_hits" : total_hits,
        "page" : page,
        "query" : query,
        "ordered_dataset" : ordered_dataset,
        "dataslug_to_dataset": dataslug_to_dataset,
    }

    return context
