from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
import pysolr
import math
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
SOLR_SERVER = settings.SOLR_SERVER
SOLR_INDEX = "cm_meta"


@cache_page(CACHE_TTL)
def index(request):
    return render(request, 'cm_search/search_index.html')


@cache_page(CACHE_TTL)
def result(request):
    error_message = None

    # TODO: check if these journals are still blacklisted, if not remove them
    # TODO: don't use hardcoding, use either the admin interface or a csv file
    # hardcoded list of journals that do not have external access on visual library UB Frankfurt
    blacklist = (
        '2431292', '2823768', '10112841', '4086896', '9038025', '4875667', '7938572', '8553624', '8823924', '9498581',
        '9572329', '9616703', '9620162')

    solr = pysolr.Solr(SOLR_SERVER + SOLR_INDEX, always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))

    query = request.GET.get('query')
    print("Query: ", query)
    page = int(request.GET.get('page'))
    size = 10
    # changed size from 15 to 10 to match the amount of results in judaicalink search
    start = (page - 1) * size
    # TODO: add the language, publisher and place to the query and in the index
    highlight_fields = ["page", "text", "dateIssued", "j_title", "vlid_journal", "vlid_page", "volume", "heft",
                        "aufsatz"]
    fields = ["page", "text", "dateIssued", "j_title", "volume", "vlid_journal", "vlid_page", "heft", "aufsatz", "id"]
    search_fields = ["text", "j_title", "aufsatz"]
    # create a dict from the fields and add the query
    # create a list for the fields that should be searched and add the query
    solr_query = [field + ":" + query for field in search_fields]

    # build the body for solr
    body = {
        "hl": "true",
        "indent": "true",
        'fl': ','.join(fields),
        "hl.requireFieldMatch": "true",
        "start": start,
        "q.op": "OR",
        "hl.fl": ','.join(highlight_fields),
        "rows": size,
        "useParams": ""
    }

    res = solr.search(q=solr_query, search_handler="/select", **body)
    # added 'from': start, to indicate which results should be displayed
    # 'from' is used to tell solr which results to return by index
    # -> if page = 1 then results 0-9 will be displayed
    # -> if page = 2 then results 10-19 and so on

    print("Hits: ", res.hits)
    # print(res.docs)
    print("Res: ", res.highlighting)

    if res.hits == 0:
        error_message = "No results found"
        context = {
            'error_message': error_message,
            'total_hits': 0,
            'query': query,
        }
        return render(request, 'cm_search/search_result.html', context)

    results = []

    for doc in res.docs:

        formatted_doc = doc

        # append the prefix of the url to the journal and page
        journal_link = "https://sammlungen.ub.uni-frankfurt.de/cm/periodical/titleinfo/" + ''.join(
            map(str, doc['vlid_journal']))
        page_link = "https://sammlungen.ub.uni-frankfurt.de/cm/periodical/pageview/" + ''.join(
            map(str, doc['vlid_page']))

        # check if the journal is in the blacklist
        if doc['vlid_journal'] in blacklist:
            formatted_doc['jl'] = ''
            formatted_doc['pl'] = ''
        else:
            formatted_doc['jl'] = journal_link
            formatted_doc['pl'] = page_link

        results.append(formatted_doc)

        # convert all the lists in the formatted_doc to strings
        for key in formatted_doc:
            formatted_doc[key] = ''.join(map(str, formatted_doc[key]))

        # convert all the date in formatted_doc['dateIssued'] to the format dd.mm.yyyy
        formatted_doc['dateIssued'] = datetime.strptime(formatted_doc['dateIssued'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y")

        # TODO: highlight the search term in the results
        # replace the text in formatted_doc['text'] with res.highlight[id]['text']
        #formatted_doc['text'] = res.highlighting[formatted_doc['id']]['text'][0]

        # replace text in formatted_doc['j_title'] with res.highlight[id]['j_title']
        #formatted_doc['j_title'] = res.highlighting[formatted_doc['id']]['j_title'][0]
        print("Highlighting: ", res.highlighting)

        results.append(formatted_doc)

    print("Doc: ", formatted_doc)



    # paging
    # -> almost copy from jl-search, except some variable-names

    # TODO: refactor paging
    total_hits = res.hits
    pages = math.ceil(total_hits / size)
    # pages containes necessary amount of pages for paging

    paging = []
    # if page = 1 will contain -2, -1, 0, 1, 2, 3, 4

    paging.append(page - 3)
    paging.append(page - 2)
    paging.append(page - 1)
    paging.append(page)
    paging.append(page + 1)
    paging.append(page + 2)
    paging.append(page + 3)

    real_paging = []
    # if page = 1 will contain 1, 2, 3, 4
    # -> non-existing pages are removed

    for number in paging:
        if number > 1 and number < pages:
            real_paging.append(number)

    context = {
        "results": results,
        "total_hits": total_hits,
        "query": query,
        "pages": pages,
        "previous": page - 1,
        "page": page,
        "next": page + 1,
        "paging": real_paging,
        'error_message': error_message,
    }

    return render(request, 'cm_search/search_result.html', context)
