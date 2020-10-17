import gzip
import rdflib
from pathlib import Path
import re
from urllib.parse import quote, unquote
from ._dataset_command import DatasetCommand, log, error
from ._dataset_command import jlo, jld, skos, dcterms, void, foaf, rdf

##############################
#Marals Script: reads csv-file, creates graph, creates turtle-file

#this code creats rdf file from the Hirsch family csv file.
# 30/10/2018
# Maral Dadvar

from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , OWL
import os , glob
import csv
import re
from urllib import request , parse

graph = Graph()


skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
edm = Namespace("http://www.europeana.eu/schemas/edm/")
dc = Namespace ("http://purl.org/dc/elements/1.1/")


graph.bind('skos', skos)
graph.bind ('foaf' , foaf)
graph.bind ('jl' , jl)
graph.bind('gndo',gndo)
graph.bind ('owl' , owl)
graph.bind('edm',edm)
graph.bind('dc',dc)

with open('hirsch_fam_davinci.csv', newline='') as csvfile:
     content = csv.reader(csvfile, delimiter=';')
     for row in content:
        print (row)
        print (len(row))

        id = row[0]
        uri = 'http://data.judaicalink.org/data/hirsch/' + id
        graph.add((URIRef(uri), RDF.type, foaf.Person ))

        names = row[2]
        names = names.replace('°','')
        names = names.strip()
        name = names.split(" ",1)
        if len(name) >1:
            prefname = name[0] + ', ' + name[1]

            graph.add((URIRef(uri), skos.prefLabel,(Literal(prefname)) ))

        if row[3] != '' :
            birthd = row[3]
            graph.add((URIRef(uri), jl.birthDate,(Literal(birthd)) ))

        if row[4]!= '':
            birthp=row[4]
            graph.add((URIRef(uri), jl.birthLocation,(Literal(birthp)) ))

        if row[5] != '':
            deathd = row[5]
            graph.add((URIRef(uri), jl.deathDate,(Literal(deathd)) ))


        if row[6]!='':
            deadthp = row[6]
            graph.add((URIRef(uri), jl.deathLocation ,(Literal(deadthp)) ))


        described = row[11]
        graph.add((URIRef(uri), jl.describedAt ,(URIRef(described)) ))


        topic = row[13]

        graph.add((URIRef(uri), dc.subject ,(Literal(topic)) ))



graph.serialize(destination='HirschFamily.ttl', format="turtle")

########################

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

#should read csv_file and parse it
def read_csv (csv_file):
    pass

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
        if not options["no_rdf"]:
            self.jsonlines_to_rdf(hirsch_rdf)
            self.add_file("hirsch.ttl")
        self.write_metadata()
