"""
Generator for the beacon file.
This scripts generates the beacon file for the GND IDs.
It uses a simple  sparql query.
It should be run monthly.

(c) Benjamin Schnabel, Stuttgart Media University
schnabel@hdm-stuttgart.de
2022-06-09
"""

from django.core.management.base import BaseCommand, CommandError
import datetime
import os
from SPARQLWrapper import SPARQLWrapper, JSON
import logging

logger = logging.getLogger(__name__)


def header():
    """
    Generate the header of the beacon file with the current date.
    return: string
    """
    now = datetime.datetime.now()
    header_text = """#FORMAT: BEACON
#PREFIX: https://d-nb.info/gnd/
#TARGET: https://data.judaicalink.org/data/gnd/{ID}
#CONTACT: Benjamin Schnabel <schnabel@hdm-stuttgart.de>
#INSTITUTION: Stuttgart Media University
#MESSAGE: JudaicaLink
#FEED: https://data.judaicalink.org/dumps/beacon/current/beacon-persons.txt
#TIMESTAMP: """ + now.strftime("%Y-%m-%dT%H:%M:%SZ") + "\n#UPDATE: monthly\n"
    # print(header_text)
    return header_text


def save_file(text):
    """
    Save the beacon file to the current directory.
    return: boolean
    """
    filename = 'beacon-persons.txt'
    filename = os.path.join('/data/judaicalink/dumps/beacon/current', filename)
    if os.path.exists(filename):
        os.remove(filename)
    try:
        with open(filename, 'w') as f:
            result = f.write(text)
            logger.info("File written successfully")
            return filename
    except IOError:
        logger.error("Error writing file")
        return False


def remove_duplicates(ids):
    return list(dict.fromkeys(ids))


def get_gnd_ids():
    # get all gnd ids from the database
    gnd_ids = []

    queryString = "SELECT * WHERE { ?s ?p ?o. } LIMIT 10"
    sparql = SPARQLWrapper("https://data.judaicalink.org/sparql/query")

    sparql.setQuery("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX jl: <http://data.judaicalink.org/ontology/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    SELECT ?id
    WHERE {
        ?person a foaf:Person.
        ?person gndo:gndIdentifier ?id.
        }
    """)

    try:
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            # if result type is literal, get the value
            if result["id"]["type"] == "literal":
                gnd_ids.append(result["id"]["value"])

        gnd_ids = remove_duplicates(gnd_ids)
        #print(gnd_ids)
        #print(len(gnd_ids))
        return remove_duplicates(gnd_ids)
    except Exception as e:
        print('Error fetching data: ', e)

    return gnd_ids




class Command(BaseCommand):
    help = 'Generates the beacon file for the GND IDs.'

    def handle(self, *args, **options):

        ids = get_gnd_ids()
        header_text = header()
        beacon_text = header_text + "\n".join(ids)
        result = save_file(beacon_text)
        if result is not None:
            self.stdout.write(self.style.SUCCESS('Beacon file successfully created at "%s"' % result))
        else:
            self.stdout.write(self.style.ERROR('Error creating beacon file'))
