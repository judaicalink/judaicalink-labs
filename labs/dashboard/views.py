from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import pysolr
import json
import logging

logger = logging.getLogger(__name__)

from labs import settings


# Create your views here.

def test(request):

    SOLR_URL = f"{settings.SOLR_SERVER}{settings.JUDAICALINK_INDEX}"
    print(f"Connecting to Solr at {SOLR_URL}")
    solr = pysolr.Solr(SOLR_URL, timeout=10)

    query = "*:*"  # Default to match all documents if no query is provided
    if not query:
        # If no query is provided, return an error message
        return HttpResponse("No query provided", status=400)

    # Construct Solr parameters
    body = {
        "hl": "false",
        "indent": "true",
        'fl': '*,[child ]',
        "start": 0,
        "q.op": "OR",
        "rows": 1000,
        "useParams": ""
    }

    try:
        response = solr.search(q=query, search_handler="/select", **body)
        result = response.raw_response


    except pysolr.SolrError as e:
        logger.error(f"Solr query failed: {e}")
        logger.error(f"Request URL: {SOLR_URL}?q={query}")
        # return the error page
        return HttpResponse(f"Solr query failed: {e}", status=500)
   # dataset = []
    #for d in result ["hits"] ["hits"]:
      #  data = {
       #     "id" : d ["_id"],
            #name
       # }
       # dataset.append (data)

    context = {
        "result":result.get('response', {}).get('docs', []),
    }

    return render(request, "dashboard/index.html", context)

