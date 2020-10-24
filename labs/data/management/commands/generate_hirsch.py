import gzip
import rdflib
from pathlib import Path
import re
from urllib.parse import quote, unquote
from ._dataset_command import DatasetCommand, log, error
from ._dataset_command import jlo, jld, skos, dcterms, void, foaf, rdf
from rdflib import Namespace, URIRef, Graph , Literal
from rdflib.namespace import RDF
import csv
import json


metadata = {
        "title": "Eine Jüdische Familie aus Aschaffenburg",
        "example": "http://data.judaicalink.org/data/hirsch/1964",
        "slug": "hirsch", # Used as graph name and for file names, identifies this dataset.
        "namespace_slugs": [
            "hirsch"
            ],
        "creators": [
            {"name": "Sara Fischer", "url": "http://wiss.iuk.hdm-stuttgart.de/people/sara-fischer/"}
            ],
        "license": {
            "name": "CC0",
            "image": "https://mirrors.creativecommons.org/presskit/buttons/88x31/png/cc-zero.png",
            "uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            }
        }

#should read csv_file and create .jsonl file
#equivalent to scraper
    #maybe start_csv_reader() is necessary in class DatasetCommand in _dataset_command.py?
    #equivalent of 'skip-scraping' could be 'skip-reading-csv'?
def csv_to_jsonl ():
    #To-Do:
        #output file in dumps/hirsch
        #use dictreader to read csv file

    name = metadata['slug'] # Used for the file name: {name}.jsonl

    with open('hirsch_fam_davinci.csv', newline='') as csvfile:
         content = csv.reader(csvfile, delimiter=';')
         next(content)
         data = []
         for row in content:
            person = {}
            id = row[0]
            person ["id"] = id
            names = row[2]
            names = names.replace('°','')
            names = names.strip()
            name = names.split(" ",1)
            if len(name) >1:
                prefLabel = name[0] + ', ' + name[1]
                person ["prefLabel"] = prefLabel
            if row[3] != '' :
                birthDate = row[3]
                person ["birthDate"] = birthDate
            if row[4]!= '':
                birthLocation=row[4]
                person ["birthLocation"] = birthLocation
            if row[5] != '':
                deathDate = row[5]
                person ["deathDate"] = deathDate
            if row[6]!='':
                deathLocation = row[6]
                person ["deathLocation"] = deathLocation
            describedAt = row[11]
            person ["describedAt"] = describedAt
            subject = row[13]
            person ["subject"] = subject
            data.append (person)
    yield data


#should prepare part of the uri if necessary
def enforce_valid_characters(uri):
    pass

#should create jl uris
def local(uri):
    pass

#should return graph
#needs dict from csv
def hirsch_rdf(graph: rdflib.Graph, resource_dict: dict):
    pass

class Command(DatasetCommand):
    help = 'Generate the hirsch family dataset from an existing csv-file'

    def handle(self, *args, **options):
        self.gzip = options['gzip']
        self.set_metadata(metadata)
        #if not options["skip_reading"]:
        self.start_csv_reader (csv_to_jsonl)
        #if not options["no_rdf"]:
        #    self.jsonlines_to_rdf(hirsch_rdf)
        #    self.add_file("hirsch.ttl")
        #self.write_metadata()
