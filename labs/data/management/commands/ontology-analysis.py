import json
import requests
from django.core.management.base import BaseCommand

from data import models
from data import utils, sparqltools


class Command(BaseCommand):
    help = '''
    Analyses the ontology uses at the public sparql endpoint.
    '''

    def handle(self, *args, **kwargs):
        res = requests.get(
            "http://data.judaicalink.org/sparql/query?query=select+distinct+%3Fp+%3Fg+where+%7Bgraph+%3Fg+%7B%3Fs+%3Fp+%3Fo%7D%7D&default-graph-uri=&output=json&stylesheet=")
        res = json.loads(res.text)
        jl_props = {}
        other_props = {}
        for binding in res["results"]["bindings"]:
            prop = binding["p"]["value"]
            graph = binding["g"]["value"]
            graph = graph[graph.rfind('/') + 1:]
            if "judaicalink" in prop:
                props = jl_props
            else:
                props = other_props
            if prop in props:
                props[prop].append(graph)
            else:
                props[prop] = [graph]
        print('-------------------------------------------------------------')
        for props in [jl_props, other_props]:
            propslist = list(props.keys())
            propslist.sort(key=lambda p: len(props[p]), reverse=True)
            for p in propslist:
                print(f"{p}: {', '.join(props[p])}")
                print()
            print('-------------------------------------------------------------')
