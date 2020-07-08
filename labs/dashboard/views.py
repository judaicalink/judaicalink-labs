from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from elasticsearch import Elasticsearch
import json



# Create your views here.

def test(request):
    es = Elasticsearch()
    body = {
        "from" : 0,
        "query" : {
            "match_all" : {}
        },
        }
    result = es.search(index="judaicalink", body = body)
   # dataset = []
    #for d in result ["hits"] ["hits"]:
      #  data = {
       #     "id" : d ["_id"],
            #name
       # }
       # dataset.append (data)

    context = {
        "result":json.dumps(result)
    }

    return render(request, "dashboard/dashboard_main.html", context)

