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
from ._dataset_command import DatasetCommand, DatasetSpider, log, error
from ._dataset_command import owl, foaf, rdf, skos, dcterms, dc, jlo

#os.chdir('C:\\Users\\Maral\\Desktop')
# Frage wer creator, hab mich mal rein
# Step 1 (finished)
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

# Step 2
class StolpersteineSpider(DatasetSpider):
    name = metadata['slug']
    start_urls = [
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Altstadt',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Neustadt',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Oberstadt',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Bretzenheim',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Ebersheim',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Finthen',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Gonsenheim',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Hechtsheim',
            'https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz-Kastel_AKK',
            ]

    def parse(self, response: scrapy.http.Response):

        soup = BeautifulSoup(response.text)

        
        stonetextlist=[]  #Mehrere Listen für die Tabelle in Wikipedia
        picurllist=[]
        remarktextlist=[]
        namelist=[]
        namelinklist1=[]
        namelinklist2=[]
        urilist=[]
        namelistremarks=[]


        body = soup.findAll('td')  # Damit findet man die Kästen auf der Homepage mit den Links zu den Stolpersteinen, oder es sind allgemein die Reihenelemente in der Stoplerstein-Tabelle

        pic = soup.findAll('a',attrs={"class" : "image"}) # Damit findet man die Bilder

        for i in range(1,len(pic),1): #extract the link to the stone pictures

            picurl = 'https://de.wikipedia.org' + str(pic[i].get('href'))
            log.info(picurl)
            picurllist.append(picurl)



        explain = soup.findAll('td',attrs={"align" : "center"})
        for j in range(0,len(explain)):
            stonetext = explain[j].getText(' ')
            #log.info(stonetext)
            stonetextlist.append(stonetext)
            namecontent = explain[j].getText(',')
            namecontent = namecontent.replace('UND ARBEITETE,','')
            log.info(namecontent)

            if 'DR.' in namecontent:
                namecontent = namecontent.replace('DR.','')

            names = namecontent.split(',',2)[1].lstrip()
           # if ' ' not in names:
            #    log.info(explain[j].getText(','), '...' ,  names)
             #   names = names + ' ' + namecontent.split(',',3)[2]
              #  log.info(names)
            if 'JG.' not in namecontent.split(',',3)[2].lstrip() and 'GEB.' not in namecontent.split(',',3)[2].lstrip() and 'VERH.' not in namecontent.split(',',3)[2].lstrip():
                names = names + ' ' + namecontent.split(',',3)[2].lstrip()
                log.info(names)

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
                log.info(names)
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

        data = {
            "stonetextlist":stonetextlist,  #Mehrere Listen für die Tabelle in Wikipedia
            "picurllist":picurllist,
            "remarktextlist":remarktextlist,
            "namelist":namelist,
            "namelinklist1":namelinklist1,
            "namelinklist2":namelinklist2,
            "urilist":urilist,
            "namelistremarks":namelistremarks,
        }
        return data



def create_rdf(graph, dictionary):

    stonetextlist=dictionary["stonetextlist"]  #Mehrere Listen für die Tabelle in Wikipedia
    picurllist=dictionary["picurllist"]
    remarktextlist=dictionary["remarktextlist"]
    namelist=dictionary["namelist"]
    namelinklist1=dictionary["namelinklist1"]
    namelinklist2=dictionary["namelinklist2"]
    urilist=dictionary["urilist"]
    namelistremarks=dictionary["namelistremarks"]
    
    for i in range(0,len(namelinklist1)):
       for j in range(0,len(picurllist)):
            if namelinklist1[i].lower() in picurllist[j].lower():
                uri = 'http://data.judaicalink.org/data/stolpersteine/' + namelinklist1[i].title()
                urilist.append(uri)
                graph.add((URIRef(uri), rdf.type, foaf.Person ))
                graph.add((URIRef(uri), skos.prefLabel, (Literal(namelist[i].title())) ))
                graph.add((URIRef(uri), jlo.hasAbstract, (Literal(stonetextlist[i].title())) ))
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
                log.info(uri)
                log.info(namelist[i].title())
                graph.add((URIRef(uri), rdf.type, foaf.Person ))
                graph.add((URIRef(uri), skos.prefLabel, (Literal(namelist[i].title())) ))
                graph.add((URIRef(uri), jlo.hasAbstract, (Literal(stonetextlist[i].title())) ))
                graph.add((URIRef(uri), dc.subject, (URIRef(picurllist[j])) ))
                graph.add((URIRef(uri), foaf.primaryTopic , (URIRef('https://de.wikipedia.org/wiki/Liste_der_Stolpersteine_in_Mainz')) ))
                for y in range (0,len(remarktextlist)):
                        if namelistremarks[i].title() in remarktextlist[y]:
                            graph.add((URIRef(uri), skos.scopeNote, (Literal(remarktextlist[y])) ))
    return graph

# Step 5
class Command(DatasetCommand):
    help = 'Generate the Stolpersteine dataset from the wikipedia articles'

    def handle(self, *args, **options):
        self.gzip = options['gzip']
        self.set_metadata(metadata)

        if not options["skip_scraping"]:
            self.start_scraper(StolpersteineSpider, settings={"LOG_LEVEL": "INFO"})

        if not options["no_rdf"]:
            # This is a helper function that calls the function you provide for each line in a jsonl file.
            # If you do not have jsonl as original format, it probably makes sense to create additional
            # helpers, e.g. to walk through an RDF file or a common JSON file. Discuss with the team if this is
            # needed, so that we get a common infrastructure.
            self.jsonlines_to_rdf(create_rdf) 

            # This adds a file to the metadata. Note that you only give the filename here, without .gz. Everyting
            # else, like a directory path and gzipping is taken care of by DatasetCommand.
            # All files not in the metadata are considered temporal files. Feed free to also add jsonl-Files or any
            # other files here, if you want to make them part of the dataset.
            self.add_file("stolpersteine.ttl")
        self.write_metadata()






