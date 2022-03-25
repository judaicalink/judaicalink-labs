# generates the statistics for the data and puts them in json file
from django.core.management.base import BaseCommand, CommandError
import json
import os

from SPARQLWrapper import SPARQLWrapper, JSON


def sparql_query(query):
    sparql = SPARQLWrapper("https://data.judaicalink.org/sparql/query")

    sparql.setQuery(query)

    try:
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        return results

    except Exception as e:
        print('Error fetching data: ', e)

        return None

def sum_datasets():
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?g WHERE { GRAPH ?g { } }
    """
    results = sparql_query(query)

    counter = 0

    for _ in enumerate(results['results']['bindings']):
        counter += 1

    return counter - 6


def sum_entities():
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT  (count(distinct ?entity) AS ?Entities)
                      WHERE{   ?entity ?p ?o}
    """
    results = sparql_query(query)
    return results['results']['bindings'][0]['Entities']['value']


def sum_triples():
    query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT (COUNT(*) as ?Triples) WHERE { ?s ?p ?o. }
    """

    results = sparql_query(query)
    return results['results']['bindings'][0]['Triples']['value']


def generate_html_file():
    path = os.path.join('./layouts/../../layouts/partials/')

    html_string = '<div class="text-center">Currently, we provide data about <b class="counter" akhi="' + str(
        sum_entities()) + '">0</b><b> entities</b>, consisting of <b class="counter" akhi="' + str(
        sum_triples()) + '">0</b><b> triples</b>, within <b class="counter" akhi="' + str(
        sum_datasets()) + '">0</b><b> different datasets</b>.</div>'

    # if path does not exist, create it
    if not os.path.exists(path):
        os.makedirs(path)

    with open(path + 'statistics.html', 'w') as f:
        f.write(html_string)
    f.close()


def generate_statistics():
    statistics = {
        'datasets': sum_datasets(),
        'entity_pages': sum_entities(),
        'triples': sum_triples()
    }

    # path is the root of the project
    path = os.path.join('./')

    # save statistics to json file
    with open(path + '/statistics.json', 'w') as f:
        json.dump(statistics, f, indent=4)

    f.close()

class Command(BaseCommand):
    help = "Generates overall statistics and saves it to a json file"

    def handle(self, *args, **options):

        try:
            generate_statistics()

        except Exception as e:
            raise CommandError(e)



