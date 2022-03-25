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

# see labs/urls.py def index to access root with http://localhost:8000

def custom_error_404(request, exception):
    return render(request, 'search/404.html', {})


def custom_error_500(request):
    return render(request, 'search/500.html', {})


def custom_error_400(request, exception):
    return render(request, 'search/400.html', {})


def custom_error_403(request, exception):
    return render(request, 'search/403.html', {})


def test_error_page(request):
    return render(request, 'search/404.html', {})


def index(request):
    return HttpResponse(Dataset.objects.all())
    # return render(request, "search/root.html")


def search_index(request):
    return render(request, "search/search_index.html")


def all_search_nav(request):
    return render(request, "search/all_search_nav.html")


def load(request):
    with open('../data/textfile-djh.json', 'rb') as f:
        data = f.read()
        print(data)
        headers = {'content-type': 'application/json'}
        response = requests.post(f'http://localhost:9200/{settings.JUDAICALINK_INDEX}/doc/_bulk?pretty', data=data,
                                 headers=headers)
        return HttpResponse(response)


def search(request):
    # for key, value in request.GET.items():
    #    print(f'Key: {key}')
    #    print(f'Value: {value}')

    # following pages
    if request.GET.get('paging') is not None:
        submitted_search = request.GET.get('paging').replace("'", '"')
        query = create_query_str(json.loads(submitted_search))
    # first page
    else:
        query = create_query_str(get_query(request))

    alert = create_alert(query["submitted_search"])
    page = int(request.GET.get('page'))
    context = process_query(query, page, alert)
    return render(request, 'search/search_result.html', context)


def create_query_str(submitted_search):
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
    print("--------------------------------query_str-----------------------------------------------")
    # query_str = name:Albert
    print(query_str)

    return query_dic


def get_query(request):
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

    # sorting the lists by the "html_name" in the dictionarys
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

    # create a list that holds dictionarys that hold the according operator, option and input
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

    print("--------------------------------submitted_search-----------------------------------------------")
    # submitted_search = [{'option': 'name:', 'input': 'Anders'}, {'operator': ' AND ', 'option': 'name:', 'input': ''}]
    print(submitted_search)

    cleared_submitted_search = submitted_search.copy()
    for dictionary in submitted_search:
        for entry in dictionary:
            if dictionary[entry] is None or dictionary[entry] == "":
                cleared_submitted_search.remove(dictionary)
                break

    submitted_search = cleared_submitted_search
    return submitted_search


def create_alert(submitted_search):
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
    counter = 0
    rows = []
    if "option" in submitted_search[
        0]:  # to check that it is not the simple search - only the advanced search contains the option field
        while counter != len(submitted_search):
            for part in submitted_search:
                all_operators = [" AND ", " OR ", " NOT "]
                all_options = ["name:", "Alternatives:", "Publication:", "birthDate:", "deathDate:", "birthLocation:",
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

        print("----------------- rows ---------------------")
        print(len(rows))
        print(rows)
        return rows

    # if we don't use the advanced search we still want to have displayed two empty rows in the advanced search
    # when we pass None two standard rows are generated with vue.js
    else:
        rows = None
        return rows


def process_query(query_dic, page, alert):
    page = int(page)
    es = Elasticsearch()
    size = 10
    start = (page - 1) * size
    query_str = query_dic["query_str"]

    body = {
        "from": start, "size": size,
        "query": {
            "query_string": {
                "query": query_str,
                "fields": ["name^4", "Alternatives^3", "birthDate", "birthLocation^2", "deathDate", "deathLocation^2",
                           "Abstract", "Publication"]
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
    result = es.search(index=settings.JUDAICALINK_INDEX, body=body)

    # For testing, never commit with a hardcoded path like this
    # with open('/tmp/test.json', 'w') as f:
    #     json.dump(result, f)

    dataset = []
    for d in result["hits"]["hits"]:
        data = {
            "id": d["_id"],
            "source": d["_source"],
            "highlight": d["highlight"],
        }
        dataset.append(data)

    # replace data in source with data in highlight
    for d in dataset:
        for s in d["source"]:
            if s in d["highlight"]:
                d["source"][s] = d["highlight"][s][0]

    field_order = ["name", "Alternatives", "birthDate", "birthYear", "birthLocation", "deathDate", "deathYear",
                   "deathLocation", "Abstract", "Publication"]

    dataset_objects = Dataset.objects.all()
    dataslug_to_dataset = {}
    for i in dataset_objects:
        dataslug_to_dataset[i.dataslug] = i.title

    ordered_dataset = []
    for d in dataset:
        data = []

        # linking to detailed view
        id = "<a href='" + d["id"] + "'>" + d["source"]["name"] + "</a>"
        data.append(id)

        # extracting fields (named in field_order) and ordering them like field_order
        for field in field_order:
            if field in d["source"] and d["source"][field] != "NA":
                pretty_fieldname = field.capitalize()
                temp_data = "<b>" + pretty_fieldname + ": " + "</b>" + d["source"][field]
                data.append(temp_data)

        # extracting additional fields (that are not mentioned in field_order)
        for field in d["source"]:
            if field not in field_order:
                pretty_fieldname = field.capitalize()
                temp_data = "<b>" + pretty_fieldname + ": " + "</b>" + d["source"][field]
                data.append(temp_data)
        ordered_dataset.append(data)

    total_hits = result["hits"]["total"]["value"]
    pages = math.ceil(total_hits / size)  # number of needed pages for paging
    # round up number of pages

    paging = []
    # if page = 1, paging contains -2, -1, 0, 1, 2, 3, 4

    paging.append(page - 3)
    paging.append(page - 2)
    paging.append(page - 1)
    paging.append(page)
    paging.append(page + 1)
    paging.append(page + 2)
    paging.append(page + 3)

    real_paging = []
    # if page = 1, paging contains 1, 2, 3, 4
    # -> non-existing (like -2, -1, ...) pages are removed

    for number in paging:
        if number > 1 and number < pages:
            real_paging.append(number)

    context = {
        "pages": pages,
        "paging": real_paging,
        "next": page + 1,
        "previous": page - 1,
        "total_hits": total_hits,
        "page": page,
        "submitted_search": query_dic["submitted_search"],
        "query_str": query_dic["query_str"],
        "simple_search_input": query_dic["simple_search_input"],
        "ordered_dataset": ordered_dataset,
        # "dataslug_to_dataset": dataslug_to_dataset,
        "alert": alert,
        "rows": generate_rows(query_dic["submitted_search"]),
    }

    return context
