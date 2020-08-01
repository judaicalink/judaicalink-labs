import requests
import json
import re
import elasticsearch
import rdflib
import time
import gzip
import os
from . import models
from . import sparqltools
from pathlib import Path
from datetime import datetime
from django.utils.http import http_date
from django.conf import settings

def url_2_filename(url):
    url = url.replace(':', '_').replace('/', '_').replace('__', '_').replace('__', '_')
    return url
    

def get_filename(url):
    return 'backend/rdf_files/' + url_2_filename(url)


def load_rdf_file(url):
    headers = {}
    filename = get_filename(url)
    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        headers['If-Modified-Since'] = http_date(int(mtime)) 
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            Path("backend/rdf_files").mkdir(parents=True, exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(res.content)
    except:
        print("Connection error: " + url)
    return filename



property2field = {
        'http://www.w3.org/2004/02/skos/core#prefLabel': 'name',
        'http://www.w3.org/2004/02/skos/core#altLabel': 'Alternatives',
        'http://data.judaicalink.org/ontology/birthDate': 'birthDate',
        'http://data.judaicalink.org/ontology/birthYear': 'birthYear',
        'http://data.judaicalink.org/ontology/birthLocation': 'birthLocation',
        'http://data.judaicalink.org/ontology/deathDate': 'deathDate',
        'http://data.judaicalink.org/ontology/deathYear': 'deathYear',
        'http://data.judaicalink.org/ontology/deathLocation': 'deathLocation',
        'http://data.judaicalink.org/ontology/hasAbstract': 'Abstract',
        }

def cleanstring(value, chars):
    for c in chars:
        value = value.replace(c, '')
    value = re.sub( '\s+', ' ', value).strip()
    return value

def index_file(filename, task):
    openfunc = open
    if filename.endswith(".gz"):
        openfunc = gzip.open
    with openfunc(filename, "rt", encoding="utf8") as f:
        g = rdflib.Graph()
        g.parse(f, format='n3')
        es = elasticsearch.Elasticsearch()
        data = {}
        triples = g.triples((None, None, None))
        for row in triples:
            s = str(row[0])
            p = str(row[1]) 
            o = (row[2])
            if p in property2field:
                f = property2field[p]
                if s in data:
                    doc = data[s]
                    if f in doc:
                        doc[f].append(o)
                    else:
                        doc[f] = [ o ]
                else:
                    data[s] = {
                            f: [ o ]
                            }
        bulk_body = []
        for s in data:
            doc = {}
            for f in data[s]:
                values = data[s][f]
                if len(values)==0:
                    continue
                values = ' - '.join(values)
                if f == 'Abstract':
                    values = cleanstring(values, ['"', '{', '}'])
                if f == 'Alternatives':
                    values = cleanstring(values, ['"', '{', '}', '.'])
                doc[f] = values
            #indexing slug
            dataslug = s
            dataslug = dataslug.replace ("http://data.judaicalink.org/data/", "").split ("/")[0]
            doc ["dataslug"] = dataslug
            index = {
                    "update": { "_index": "judaicalink", "_id": s }
                    }
            bulk_body.append(json.dumps(index))
            bulk_body.append(json.dumps({"doc": doc, "doc_as_upsert": True}))
        if len(bulk_body)>0:
            task.log(filename + " indexing")
            es.bulk('\n'.join(bulk_body))

            



mappings = {
    "properties": {
      "Name":   { "type": "text"  },     
      "birthDate":   { "type": "text"  },     
      "birthYear":   { "type": "integer"  },     
      "deathDate":   { "type": "text"  },    
      "deathYear":   { "type": "integer"  },     
      "birthLocation":   { "type": "text"  },     
      "deathLocation":   { "type": "text"  },    
      "Abstract":   { "type": "text"  },
      "Alternatives":   { "type": "text"  },     
    }
  }

    
mappings_simpletext = {
    "properties": {
      "text":   { "type": "text"  },     
    }
  }

    
def load_in_elasticsearch(task):
    es = elasticsearch.Elasticsearch()
    ic = elasticsearch.client.IndicesClient(es)
    if ic.exists(settings.JUDAICALINK_INDEX):
        ic.delete(settings.JUDAICALINK_INDEX)
    ic.create(index=settings.JUDAICALINK_INDEX, body={'mappings': mappings})
    for df in models.Datafile.objects.filter(indexed=True, dataset__indexed=True):
        if df.dataset.is_rdf():
            task.log(df.url + " parsing")
            filename = load_rdf_file(df.url)
            index_file(filename, task)
    for df in models.Datafile.objects.filter(indexed=True, dataset__indexed=True):
        if df.dataset.category == 'support':
            openfunc = open
            filename = load_rdf_file(df.url)
            if filename.endswith(".gz"):
                openfunc = gzip.open
            with openfunc(filename, "rt", encoding="utf8") as f:
                print ("indexing: " + filename)
                es.bulk(f.read())
            
    


def create_dataset(name, db_type='mem'):
    res = requests.get(settings.FUSEKI_SERVER + '$/datasets/' + name)
    if res.status_code==404:
        res = requests.post(settings.FUSEKI_SERVER + '$/datasets', {'dbType': db_type, 'dbName':name})

def load_in_fuseki(task):
    create_dataset('judaicalink')
    for ds in models.Dataset.objects.all():
        if not ds.is_rdf():
            continue
        task.log(ds.name + " dropping")
        sparqltools.unload(settings.FUSEKI_SERVER + 'judaicalink/update', ds.graph)
        if not ds.loaded:
            continue
        for df in ds.datafile_set.all():
            if df.loaded:
                filename = load_rdf_file(df.url)
                task.log(filename + " loading")
                sparqltools.load(filename, settings.FUSEKI_SERVER + 'judaicalink/update', ds.graph, log=task.log)
