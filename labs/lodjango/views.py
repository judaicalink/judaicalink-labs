from django.shortcuts import render
from django.http import HttpResponse
import SPARQLWrapper
from . import settings
from collections import defaultdict
import json
# Create your views here.

sparql = SPARQLWrapper.SPARQLWrapper(settings.SPARQL_ENDPOINT, returnFormat=SPARQLWrapper.JSON)


def value_tuple(binding, o_var, g_var, label_var):
    value = binding[o_var]['value']
    uri = None
    if binding[o_var]['type'] == 'uri':
        uri = value
        if label_var in binding:
            value = binding[label_var]['value']
    graph  = None
    if g_var in binding:
        graph = binding[g_var]['value']
    return (value, uri, graph)

def parse_bindings(bindings, s_var='s',p_var='p', o_var='o', g_var='g', label_var='olabel'):
    res = {} 
    for binding in bindings:
        if s_var is None:
            s = '_'
        else:
            s = binding[s_var]['value']
        if s not in res:
            res[s] = {}
        p = binding[p_var]['value']
        if p not in res[s]:
            res[s][p] = [] 
        res[s][p].append(value_tuple(binding, o_var, g_var, label_var))
    return res



def get(request, path):
    uri = settings.DATA_PREFIX + path
    sparql.setQuery('''
    select ?s ?p ?o ?g ?olabel  where {{GRAPH ?g {{
        ?s ?p ?o .
        }} 
        OPTIONAL {{
            ?o <http://www.w3.org/2004/02/skos/core#prefLabel> ?olabel.
        }}
        filter(?s=<{}>)
    }}
    '''.format(uri))
    res = sparql.query()
    data = parse_bindings(res.convert()['results']['bindings'])
    context = {
                'settings': settings,
                'data': data,
            }
    return render(request, 'lodjango/get.html', context=context)
