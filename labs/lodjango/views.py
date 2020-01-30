from django.shortcuts import render
from django.http import HttpResponse
import SPARQLWrapper
from . import settings
from collections import defaultdict
import json
# Create your views here.

sparql = SPARQLWrapper.SPARQLWrapper(settings.SPARQL_ENDPOINT, returnFormat=SPARQLWrapper.JSON)


def value_tuple(binding, value_var, graph_var, label_var):
    """
    The value tuple is the basic element used in the templates. 
    It follows the "label first" principle, i.e., everthing should have 
    a label. If uri is set, it is a URI. The graph indicates the dataset
    where this value is stated for the given property and the main (fixed) 
    subject/object 
    of this page.
    """
    value = binding[value_var]['value']
    uri = None
    if binding[value_var]['type'] == 'uri':
        uri = value
        if label_var in binding:
            value = binding[label_var]['value']
    graph  = None
    if graph_var in binding:
        graph = binding[graph_var]['value']
    return (value, uri, graph)


def parse_bindings(bindings, prop_var='p', value_var='o', graph_var='g', label_var='olabel'):
    """
    Creates a lookup dictionary per property. Value depends on use case, 
    for reverse links it will be the subject of a triple, as the object 
    is fixed.
    """
    res = {} 
    for binding in bindings:
        p = binding[prop_var]['value']
        if p not in res:
            res[p] = [] 
        res[p].append(value_tuple(binding, value_var, graph_var, label_var))
    return res


def query(uri, filter_var='s', label_for='o', label_var='olabel'):
    sparql.setQuery('''
    select ?s ?p ?o ?g ?{1}  where {{GRAPH ?g {{
        ?s ?p ?o .
        }} 
        OPTIONAL {{
            ?{0} <http://www.w3.org/2004/02/skos/core#prefLabel> ?{1}.
        }}
        OPTIONAL {{
            ?{0} <http://www.w3.org/2000/01/rdf-schema#label> ?{1}.
        }}
        filter(?{2}=<{3}>)
    }}
    '''.format(label_for, label_var, filter_var, uri))
    res = sparql.query()
    return res.convert()['results']['bindings']

def get(request, path):
    uri = settings.DATA_PREFIX + path
    res = query(uri)
    data = parse_bindings(query(uri))
    context = {
                'settings': settings,
                'data': data,
                'subject': uri,
                'res': res,
            }
    return render(request, 'lodjango/get.html', context=context)


rightside_properties = [
        'http://www.w3.org/2004/02/skos/core#related',
        'http://www.w3.org/2004/02/skos/core#broader',
        'http://www.w3.org/2004/02/skos/core#narrower',
        ]


def get_grid(request, path):
    uri = settings.DATA_PREFIX + path
    data = parse_bindings(query(uri))
    right = {}
    for p in list(data.keys()):
        if p in rightside_properties:
            right[p] = data[p]
            del data[p]
    reverse = parse_bindings(
            query(uri, 'o', 's', 'slabel'),
            value_var='s',
            label_var='slabel',
            )
    context = {
                'VIEW_PATH': 'grid/',
                'settings': settings,
                'subject': uri,
                'data': data,
                'right': right,
                'reverse': reverse,
            }
    return render(request, 'lodjango/get-grid.html', context=context)
