#this code extracts the information about the Stolperstein from its wiki page

#origin file from judaicalink-generators
#https://github.com/wisslab/judaicalink-generators/blob/master/stolpersteine/scripts/Stein-wiki-01.py

import urllib.request as urllib2
from bs4 import BeautifulSoup #same as yivo
import rdflib #same as yivo
from rdflib import Namespace, URIRef, Graph , Literal
from SPARQLWrapper import SPARQLWrapper2, XML , RDF , JSON , TURTLE
from rdflib.namespace import RDF, FOAF , OWL
import os , glob
import csv
import re #same as yivo
import time

import scrapy.http
from urllib.parse import quote
from ._dataset_command import DatasetCommand, DatasetSpider
from ._dataset_command import owl, foaf, rdf, skos

#os.chdir('C:\\Users\\Maral\\Desktop')
# Frage wer creator, hab mich mal rein
metadata = {
        "title": "Liste der Stolpersteine in Mainz",
        "example": "https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Altstadt",
        "slug": "stolpersteine", # Used as graph name and for file names, identifies this dataset.
        "namespace_slugs": [
            "stolpersteine"
            ],
        "creators": [
            {"name": "Patricia Kaluza", "url": "http://wiss.iuk.hdm-stuttgart.de/people/patricia-kaluza/"}
            ],
        "license": {
            "name": "CC0",
            "image": "https://mirrors.creativecommons.org/presskit/buttons/88x31/png/cc-zero.png",
            "uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            }
        }


#verlinkung zu _dataset_command
graph = Graph()

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    jl = Namespace("http://data.judaicalink.org/ontology/") #--vllt jlo in dataset_command.py?
foaf = Namespace("http://xmlns.com/foaf/0.1/")
    gndo = Namespace("http://d-nb.info/standards/elementset/gnd#") #fehlt in dataset_command.py
owl = Namespace("http://www.w3.org/2002/07/owl#")
    edm = Namespace("http://www.europeana.eu/schemas/edm/") #fehlt in dataset_command.py
    dc = Namespace ("http://purl.org/dc/elements/1.1/") #--vllt dcterms in dataset_command.py?
#-------------------------------------------------------
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


page = urllib2.urlopen('https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz')
soup = BeautifulSoup(page)

stonetextlist=[]
picurllist=[]
remarktextlist=[]
namelist=[]
namelinklist1=[]
namelinklist2=[]
urilist=[]
namelistremarks=[]


body = soup.findAll('td')

pic = soup.findAll('a',attrs={"class" : "image"})

for i in range(1,len(pic),1): #extract the link to the stone pictures

    picurl = 'https://de.wikipedia.org' + str(pic[i].get('href'))
    #print (picurl)
    picurllist.append(picurl)



explain = soup.findAll('td',attrs={"align" : "center"})
for j in range(0,len(explain)):
    stonetext = explain[j].getText(' ')
    #print (stonetext)
    stonetextlist.append(stonetext)
    namecontent = explain[j].getText(',')
    namecontent = namecontent.replace('UND ARBEITETE,','')
    print (namecontent)

    if 'DR.' in namecontent:
        namecontent = namecontent.replace('DR.','')

    names = namecontent.split(',',2)[1].lstrip()
   # if ' ' not in names:
    #    print (explain[j].getText(','), '...' ,  names)
     #   names = names + ' ' + namecontent.split(',',3)[2]
      #  print (names)
    if 'JG.' not in namecontent.split(',',3)[2].lstrip() and 'GEB.' not in namecontent.split(',',3)[2].lstrip() and 'VERH.' not in namecontent.split(',',3)[2].lstrip():
        names = names + ' ' + namecontent.split(',',3)[2].lstrip()
        print (names)

    namelistremarks.append(names)
    na= names.replace(' ',', ')
    namelist.append(na)



    name1 = names.replace(' ','_')
    namelinklist1.append(name1)

    if len(names.split(' ')) == 2:
        n1 = names.split(' ')[0]
        n2 = names.split(' ')[1]
        name2 = n2 + '_' + n1
        namelinklist2.append(name2)
    elif len(names.split(' ')) == 3:
        n1 = names.split(' ')[0]
        n2 = names.split(' ')[1]
        n3 = names.split(' ')[2]
        name2 = n3 + '_' + n1 + '_' + n2
        namelinklist2.append(name2)
    else:
        print (names)
        namelinklist2.append(name2)

remarks1 = soup.findAll('td',attrs={"rowspan" : "1"})
for x in range(0,len(remarks1)):
    if '<small>' in str(remarks1[x]):
        remarktext1 = remarks1[x].getText(',')
        remarktext1 = re.sub(r'\[.*\]', ' ', remarktext1)
        remarktextlist.append(remarktext1)

remarks2 = soup.findAll('td',attrs={"rowspan" : "2"})
for x in range(0,len(remarks2)):
    if '<small>' in str(remarks2[x]):
        remarktext2 = remarks2[x].getText(',')
        remarktext2 = re.sub(r'\[.*\]', ' ', remarktext2)
        remarktextlist.append(remarktext2)


for i in range(0,len(namelinklist1)):
   for j in range(0,len(picurllist)):
        if namelinklist1[i].lower() in picurllist[j].lower():
            uri = 'http://data.judaicalink.org/data/stolpersteine/' + namelinklist1[i].title()
            urilist.append(uri)
            graph.add((URIRef(uri), RDF.type, foaf.Person ))
            graph.add((URIRef(uri), skos.prefLabel, (Literal(namelist[i].title())) ))
            graph.add((URIRef(uri), jl.hasAbstract, (Literal(stonetextlist[i].title())) ))
            graph.add((URIRef(uri), dc.subject, (URIRef(picurllist[j])) ))
            graph.add((URIRef(uri), foaf.primaryTopic , (URIRef('https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz')) ))

            for y in range (0,len(remarktextlist)):
                    if namelistremarks[i].title() in remarktextlist[y]:
                        graph.add((URIRef(uri), skos.scopeNote, (Literal(remarktextlist[y])) ))



for i in range(0,len(namelinklist2)):
    for j in range(0,len(picurllist)):
        if namelinklist2[i].lower() in picurllist[j].lower():
            uri = 'http://data.judaicalink.org/data/stolpersteine/' + namelinklist2[i].title()
            urilist.append(uri)
            print (uri)
            print (namelist[i].title())
            graph.add((URIRef(uri), RDF.type, foaf.Person ))
            graph.add((URIRef(uri), skos.prefLabel, (Literal(namelist[i].title())) ))
            graph.add((URIRef(uri), jl.hasAbstract, (Literal(stonetextlist[i].title())) ))
            graph.add((URIRef(uri), dc.subject, (URIRef(picurllist[j])) ))
            graph.add((URIRef(uri), foaf.primaryTopic , (URIRef('https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz')) ))
            for y in range (0,len(remarktextlist)):
                    if namelistremarks[i].title() in remarktextlist[y]:
                        graph.add((URIRef(uri), skos.scopeNote, (Literal(remarktextlist[y])) ))


graph.serialize(destination='stolpersteine.ttl', format="turtle")
