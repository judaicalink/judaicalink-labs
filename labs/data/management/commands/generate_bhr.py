
#Gedankengang
#1. Scrapping_Persons_01.py scraped die Daten und schreibt die CSV
#2. BHR-ID.csv mit Name, ID und GND-Link
#3. und daraus werden dann Triple gebildet vgl. EncycBHR-ID.rdf

# EncycBHR-ID.rdf
# <http://data.judaicalink.org/data/bhr/Aaron_Cerf> a foaf:Person ;
#     gndo:gndIdentifier "NA" ;
#     owl:sameAs <http://steinheim-institut.de:50580/cgi-bin/bhr?id=1953> ; ----Link fest und ID von uns (vgl. Tabelle BHR-ID.csv)
#     skos:prefLabel "Aaron , Cerf" .

#Readme lesen von Round 1 und 2

#-------DATEI Scrapping_Persons_01.py Round 1


#this code creates URL for BHR Encyc. perons based on their internal ids. Then scrapes each page to extract the GNDID and Name of the persons.

import urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON
from rdflib.namespace import RDF, FOAF , OWL
import os , glob
import csv
import re

os.chdir('C:\Users\Maral\Desktop')
#--------hier wird eine CSV-Datei erzeugt, jetzt statt CSV -> Json + JsonLines
output = open('BHR-ID.csv','w')

output.writelines([str('Name'),',',str('ID'),',',str('GND'),'\n'])



for i in range (1 , 2704):

    url = 'http://www.steinheim-institut.de:50580/cgi-bin/bhr?id=' + str(i)

    #print url

    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page)

    h1 = soup.find_all('h1')
    name = h1[1].string
    if name!= None:
        name = name.replace(',',' -')
        name = name.encode('utf-8')


    #print h1[1]

    for link in soup.find_all('a'):
        if 'gnd' in link.get('href'):
            gnd = link.get('href')
            print gnd
        else:
            gnd = 'NA'

    output.writelines([str(name),',',str(i),',',str(gnd),'\n'])


output.close()



#-----ab hier Triple

#this code creates triples from the csv file containing information extarcted from the encyclopedia
# 25/July/2017
# Maral Dadvar


import urllib2
from bs4 import BeautifulSoup
import rdflib
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , OWL
import os , glob
import csv
import re
import unidecode

os.chdir('C:\Users\Maral\Desktop')

graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
jl = Namespace("http://data.judaicalink.org/ontology/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")
gndo = Namespace("http://d-nb.info/standards/elementset/gnd#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

graph.bind('skos', skos)
graph.bind ('foaf' , foaf)
graph.bind ('jl' , jl)
graph.bind('gndo',gndo)
graph.bind ('owl' , owl)


data = csv.reader(open('C:\\Users\\Maral\\Desktop\\Encycoutput.csv'))
fields = data.next()
eventdic={}

dic={}

listuri = []

for row in data:
    i = 0

    items = zip(fields, row)
    item = {}
    for (name, value) in items:
        item[name] = value.strip()

    fn = item['fn'].strip()
    fn = fn.replace('.','')

    if '(' in fn:
        fn = fn.rsplit('(',1)[0].strip()

    fnuri = fn.replace(' ','') #the fn and ln used in person uri can not have space


    ln = item['ln'].strip()
    ln = ln.replace('.','')

    if '(' in ln:
        ln = ln.rsplit('(',1)[0].strip()

    lnuri = ln.replace(' ','')


    if ln != '':
        name = fn + ', ' + ln
        nameuri = fnuri + '_' + lnuri


    else:

        name = fn
        nameuri = fnuri


    geb = item['geb']
    gest = item['gest']
    bhr = item['BHR']

    uri0 = 'http://data.judaicalink.org/data/bhr/' + nameuri

    if uri0 not in listuri:
        listuri.append(uri0)
        uri = uri0
    else:
        i = i+1
        uri = uri0 + '-' + str(i)
        if uri not in listuri:
            listuri.append(uri)

        else:
            i = i+1
            uri = uri0 +'-'+ str(i)
            if uri not in listuri:
                listuri.append(uri)

            else:
                i = i+1
                uri = uri0 + '-'+  str(i)
                listuri.append(uri)


    graph.add((URIRef(uri), RDF.type, foaf.Person ))
    graph.add((URIRef(uri), jl.birthDate,(Literal(geb)) ))
    graph.add((URIRef(uri), jl.deathDate,(Literal(gest)) ))
   # graph.add((URIRef(uri), jl.describedAt ,(Literal(bhr)) ))
    graph.add((URIRef(uri), skos.prefLabel ,(Literal(name)) ))
    graph.add((URIRef(uri), jl.occpation ,(URIRef('http://data.judaicalink.org/data/occupation/Rabbi')) ))

graph.serialize(destination='Encyc.rdf', format="turtle")
