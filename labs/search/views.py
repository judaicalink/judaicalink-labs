import logging

import requests
import math
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from data.models import Dataset
import pysolr
import json
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT

# Create your views here.

# see labs/urls.py def index to access root with http://localhost:8000
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

# import SEARCH_URL from settings.py
SOLR_SERVER = settings.SOLR_SERVER
SOLR_INDEX = "judaicalink"


# setup logging
logger = logging.getLogger(__name__)


@cache_page(CACHE_TTL)
def error_400(request, exception):
    print("Error 400", exception)
    return render(request, 'search/400.html', {})


@cache_page(CACHE_TTL)
def error_404(request, exception):
    print("Error 404", exception)
    return render(request, 'search/404.html', {})


@cache_page(CACHE_TTL)
def error_403(request, exception):
    print("Error 403", exception)
    return render(request, 'search/403.html', {})


@cache_page(CACHE_TTL)
def error_500(request):
    return render(request, 'search/500.html', {})


@cache_page(CACHE_TTL)
def index(request):
    return HttpResponse(Dataset.objects.all())
    # return render(request, "search/root.html")


@cache_page(CACHE_TTL)
def search_index(request):
    return render(request, "search/search_index.html")


@cache_page(CACHE_TTL)
def all_search_nav(request):
    return render(request, "search/all_search_nav.html")


def load(request):
    with open('../data/textfile-djh.json', 'rb') as f:
        data = f.read()
        print(data)
        headers = {'content-type': 'application/json'}
        response = requests.post(f'http://localhost:8389/{settings.JUDAICALINK_INDEX}/doc/_bulk?pretty', data=data,
                                 headers=headers)
        return HttpResponse(response)


def search(request):
    # for key, value in request.GET.items():
    #    print(f'Key: {key}')
    #    print(f'Value: {value}')

    # if user is changing between pages and search query stays the same
    # 'paging' is used as an indicator to check that
    if request.GET.get('paging') is not None:
        # search query gets processed by solr again, but this time with the corresponding page
        submitted_search = request.GET.get('paging').replace("'", '"')
        query = create_query_str(json.loads(submitted_search))
    # if new search query is generated
    else:
        query = create_query_str(get_query(request))

    alert = create_alert(query["submitted_search"])
    page = int(request.GET.get('page'))
    context = process_query(query, page, alert)
    if context is None:
        alert = "No results found"

    return render(request, 'search/search_result.html', context)


def create_query_str(submitted_search):
    """
    Creates strings that contain the search query in a format that solr can process and stores them in a dictionary
    :param submitted_search:  that contains the submitted search (either simple or advanced search query)
    :return: query_dic: dictionary with query strings
    """

    query_str = ""
    simple_search_input = ""
    for dictionary in submitted_search:
        for entry in dictionary:
            query_str = query_str + dictionary[entry]

    if query_str.startswith((" AND ", " OR ", " NOT ")):
        query_str = query_str.strip(" AND OR NOT ")

    # check if it's the simple search and if something was submitted
    if "option" not in submitted_search[0] and submitted_search != [{'input': 'error_nothing_submitted'}]:
        simple_search_input = query_str

    query_dic = {
        "simple_search_input": simple_search_input.strip(),
        "query_str": query_str.strip(),
        "submitted_search": submitted_search,
    }

    return query_dic


def get_query(request):
    """
    Creates a dictionary that contains the searched query for the advanced search
    :param request:
    :return: submitted_search: dictionary that contains search query
    """
    operators = []
    options = []
    inputs = []

    # sorting operators, options and inputs into specific lists
    for key, value in request.GET.items():
        if key.startswith("operator"):
            dictionary = {
                "html_name": key,
                "value": value
            }
            operators.append(dictionary)
        if key.startswith("option"):
            dictionary = {
                "html_name": key,
                "value": value
            }
            options.append(dictionary)
        if key.startswith("input"):
            dictionary = {
                "html_name": key,
                "value": value
            }
            inputs.append(dictionary)

    # print(operators)

    # sorting the lists by the "html_name" in the dictionaries
    # example result for inputs: ['einstein', 'herbert']
    # special treatment for operators: after sorting a placeholder is inserted
    # to keep the right order when creating the list "submitted_search"
    operators.sort(key=lambda r: r['html_name'])
    operators = [d['value'] for d in operators]
    operators.insert(0, "placeholder")
    options.sort(key=lambda r: r['html_name'])
    options = [d['value'] for d in options]
    inputs.sort(key=lambda r: r['html_name'])
    inputs = [d['value'] for d in inputs]

    # create a list that holds dictionaries that hold the according operator, option and input
    # submitted_search will look like this:
    # [{'option': 'name:', 'input': 'einstein'}, {'operator': ' OR ', 'option': 'name:', 'input': 'herbert'}]
    submitted_search = []

    # simple search: check if there is only 1 input and no option
    if len(options) == 0:
        if any(inputs):
            dictionary = {
                "input": inputs[0]
            }
            submitted_search.append(dictionary)
        else:
            submitted_search = [{'input': 'error_nothing_submitted'}]
    # advanced search
    else:
        # any is True when at least one input has been used in the search form
        # inputs=['Albert', ''] == True
        if any(inputs):
            for i in range(len(operators)):
                dictionary = {
                    "operator": operators[i],
                    "option": options[i],
                    "input": inputs[i],
                }

                # remove the placeholder when it's not needed anymore
                if dictionary["operator"] == "placeholder":
                    del dictionary["operator"]
                submitted_search.append(dictionary)

        else:
            submitted_search = [{'input': 'error_nothing_submitted'}]

    # print("--------------------------------submitted_search-----------------------------------------------")
    # submitted_search = [{'option': 'name:', 'input': 'Anders'}, {'operator': ' AND ', 'option': 'name:', 'input': ''}]
    # print(submitted_search)

    cleared_submitted_search = submitted_search.copy()
    for dictionary in submitted_search:
        for entry in dictionary:
            if dictionary[entry] is None or dictionary[entry] == "":
                cleared_submitted_search.remove(dictionary)
                break

    submitted_search = cleared_submitted_search
    return submitted_search


def create_alert(submitted_search):
    """
    Creates a string that shows the error response.
    :param submitted_search:
    :return: alert: string that contains the error response
    """

    # receives dictionary query_dic ["submitted_search"] submitted_search may look like this: [{'Option1': 'name:',
    # 'Input1': 'einstein'}, {'Operator3': ' OR ', 'Option3': 'birthDate:', 'Input3': '1900'}] creates a string for
    # each part of the query that will be stored in a list (alert)
    alert = []
    for dictionary in submitted_search:
        for entry in dictionary:
            # Operators like AND, OR, NOT will be stripped of any whitespaces and transformed into capital letters only
            if entry.startswith("operator"):
                alert.append(dictionary[entry].upper().strip())
            # Options will start with a capital letter, other letters will be transformed into lowercase
            if entry.startswith("option"):
                alert.append(dictionary[entry].capitalize())
            # User Input will be displayed exactly like the user submitted it
            if entry.startswith("input"):
                alert.append(dictionary[entry])
    # returns a list like this ["Name: ", "Einstein", "OR" "Birthdate: ", "1900"]
    if alert[0] == "AND" or alert[0] == "OR" or alert[0] == "NOT":
        del alert[0]
    return alert


def generate_rows(submitted_search):
    '''
    generates a dictionary containing the search request for an advanced search
    :param submitted_search:
    :return: rows (dictionary containing advanced search request)
    '''
    counter = 0
    rows = []
    if "option" in submitted_search[0]:
        # to check that it is not the simple search - only the advanced search contains the option field
        while counter != len(submitted_search):
            for part in submitted_search:
                all_operators = [" AND ", " OR ", " NOT "]
                all_options = ["name:", "alternatives:", "publication:", "birthDate:", "deathDate:", "birthLocation:",
                               "deathLocation:"]
                counter += 1
                row = {}

                # Operator
                # try except is needed in case no operator is provided in submitted_search
                # this is the case in the first row
                try:
                    row["operator"] = "operator" + str(counter)
                    row["selected_operator"] = part["operator"]

                    other_operators = []
                    for i in all_operators:
                        operator_dict = {}
                        operator_dict["display"] = i.strip()
                        operator_dict["fieldname"] = i
                        other_operators.append(operator_dict)
                    row["other_operators"] = other_operators
                except:
                    pass

                # Option
                row["option"] = "option" + str(counter)
                row["selected_option"] = part["option"]

                other_options = []
                for i in all_options:
                    option_dict = {}
                    option_dict["display"] = i.capitalize().strip(":")
                    option_dict["fieldname"] = i
                    other_options.append(option_dict)
                row["other_options"] = other_options

                # Input
                row["input"] = "input" + str(counter)
                row["submitted_input"] = part["input"]

                rows.append(row)

        # to make sure always two rows are the minimum to display in the search form - not one row
        # the second row has default values and empty input if only the first one was used
        if len(rows) == 1:
            row = {}

            # Operator
            row["operator"] = "operator" + "2"
            row["selected_operator"] = " AND "
            row["other_operators"] = [
                {"display": "AND",
                 "fieldname": " AND "},
                {"display": "OR",
                 "fieldname": " OR "},
                {"display": "NOT",
                 "fieldname": " NOT "}
            ]

            # Option
            all_options = ["name:", "Alternatives:", "Publication:", "birthDate:", "deathDate:", "birthLocation:",
                           "deathLocation:"]
            row["option"] = "option" + "2"
            row["selected_option"] = "name:"

            other_options = []
            for i in all_options:
                option_dict = {}
                option_dict["display"] = i.capitalize().strip(":")
                option_dict["fieldname"] = i
                other_options.append(option_dict)
            row["other_options"] = other_options

            # Input
            row["input"] = "input" + "2"
            row["submitted_input"] = ""

            rows.append(row)

        # print("----------------- rows ---------------------")
        # print(len(rows))
        # print(rows)
        return rows

    # if we don't use the advanced search we still want to have displayed two empty rows in the advanced search
    # when we pass None two standard rows are generated with vue.js
    else:
        rows = None
        return rows


def process_query(query_dic, page, alert):
    """
    search query is processed here: request to solr is made, search results are received, paging is generated according to the number of search results
    paging: implemented so 10 results will be displayed per page
    :param query_dic:
    :param page: integer, representing the page the user is currently on
    :param alert: string, built from the search query in a readable form, displayed when a search was requested
    :return: context that contains all the information needed to generate the template
    """

    page = int(page)

    solr = pysolr.Solr(SOLR_SERVER + SOLR_INDEX, always_commit=True, timeout=10,
                       auth=(settings.SOLR_USER, settings.SOLR_PASSWORD))
    size = 10
    start = (page - 1) * size
    query_str = query_dic["query_str"]
    logger.debug("Query: " + query_str)

    # Fields that should be highlighted
    highlight_fields = ['name', 'birthDate', 'birthLocation', 'Alternatives', 'deathDate', 'deathLocation',
                        'dataslug']

    fields = ['name', 'birthDate', 'birthLocation', 'Alternatives', 'deathDate', 'deathLocation',
              'dataslug', "id"]

    solr_query = "\n".join(f"{field}:{query_str}" for field in fields)

    logger.debug(solr_query)

    # build the body for solr
    body = {
        "hl": "true",
        "indent": "true",
        'fl': ','.join(fields),
        "hl.requireFieldMatch": "true",
        "hl.tag.pre": "<strong>",
        "hl.tag.post": "</strong>",
        "hl.fragsize": "0",
        "start": start,
        "q.op": "OR",
        "hl.fl": ','.join(highlight_fields),
        "rows": size,
        "useParams": ""
    }

    # Perform the query with highlighting
    result = solr.search(q=solr_query, search_handler="/select", **body)
    # debug
    logger.debug("Result: ")
    logger.debug(result.hits)
    logger.debug(result.docs)
    logger.debug(result.highlighting)
    if result.hits == 0:
        return None

    data = result.docs

    # FIXME: get the correct link
    # add the lint to the source
    for entry in data:
        for key in entry:
            entry[key] = ''.join(map(str, entry[key]))
        entry['link'] = "<a href='{}'>{}</a>".format(entry["id"], entry["name"])

    # Extract the highlighting
    highlighting = result.highlighting

    for doc in data:
        doc_id = doc['id']
        if doc_id in highlighting:
            for field in highlight_fields:
                if field in highlighting[doc_id]:
                    # Replace the original field value with the flattened highlighted value
                    doc[field] = "".join(highlighting[doc_id][field])

    field_order = ["name", "Alternatives", "birthDate", "birthLocation", "deathDate", "deathLocation", "Abstract", "Publication"]

    for doc in data:
        capitalized_doc = {key.capitalize(): value for key, value in doc.items()}
        doc.pop("id", None)
        doc.clear()
        doc.update(capitalized_doc)

    total_hits = result.hits
    pages = []
    for page in range(0, math.ceil(total_hits / size)):
        # number of needed pages for paging
        # round up number of pages
        pages.append(page+1)

    context = {
        "pages": pages,  # amount of pages that need to be generated
        "total_hits": total_hits,  # amount of search results
        "current_page": page,  # page the user has selected
        "submitted_search": query_dic["submitted_search"],
        "query_str": query_dic["query_str"],
        "simple_search_input": query_dic["simple_search_input"],
        "ordered_dataset": data, # ordered_dataset,
        "alert": alert,
        "rows": json.dumps(generate_rows(query_dic["submitted_search"])),
    }
    return context
