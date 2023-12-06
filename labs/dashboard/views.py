from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import pysolr
import json



# Create your views here.

def test(request):
    solr = pysolr.Solr('http://localhost:8983/solr/judaicalink', always_commit=True, timeout=10)
    body = {
        "from" : 0, "size" : 1000,
        "query" : {
            "match_all" : {}
        },
        }
    result = solr.search(body = body, index = "judaicalink")
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

