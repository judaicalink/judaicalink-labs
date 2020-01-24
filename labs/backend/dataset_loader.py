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

def url_2_filename(url):
    url = url.replace(':', '_').replace('/', '_').replace('__', '_').replace('__', '_')
    return url
    


def load_rdf_file(url):
    headers = {}
    filename = 'backend/rdf_files/' + url_2_filename(url)
    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        headers['If-Modified-Since'] = http_date(int(mtime)) 
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        Path("backend/rdf_files").mkdir(parents=True, exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(res.content)
    return filename


sparql_query = '''
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX gndo: <http://d-nb.info/standards/elementset/gnd#>
    PREFIX pro: <http://purl.org/hpi/patchr#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX edm: <http://www.europeana.eu/schemas/edm/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX dblp: <http://dblp.org/rdf/schema-2015-01-26#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX bibtex: <http://data.bibbase.org/ontology/#>
    PREFIX jl: <http://data.judaicalink.org/ontology/>
select distinct ?o ?name ?bd ?dd ?bl ?dl ?abs (group_concat(?alt; SEPARATOR="-") as ?alt2)
 where
{
     ?o skos:prefLabel ?name.
     ?o skos:altLabel ?alt
     optional {?o jl:birthDate ?bd}
     optional {?o jl:deathDate ?dd}
     optional{ ?o jl:birthLocation ?bl }
     optional {?o jl:deathLocation ?dl}
     optional {?o jl:hasAbstract ?abs}
} group by ?o ?name ?bd ?dd ?bl ?dl ?abs
'''


def index_file(filename, task):
    openfunc = open
    if filename.endswith(".gz"):
        openfunc = gzip.open
    with openfunc(filename, "rt", encoding="utf8") as f:
        g = rdflib.Graph()
        g.parse(f, format='n3')
        res = g.query(sparql_query)
        es = elasticsearch.Elasticsearch()
        bulk_body = [] 
        for row in res:
            uri = row[0]
            name = row[1] 
            birth = row[2]
            death = row[3]
            blocation = row[4]
            dlocation = row[5]
            abstract = row[6]
            if abstract:
                abstract = abstract.replace('"','')
                abstract = abstract.replace('{','')
                abstract = abstract.replace('}','')
                abstract = re.sub( '\s+', ' ', abstract).strip()

            altname = row[7]
            if altname:
                altname = altname.replace('{','')
                altname = altname.replace('}','')
                altname = altname.replace('"','')
                altname = altname.replace('.','')

            doc = { 
                "Name": name,
                "birthDate": birth,
                "deathDate": death,
                "birthLocation": blocation,
                "deathLocation": dlocation,
                "Abstract": abstract,
                "Alternatives": altname
                }
            index = {
                    "index": { "_index": "judaicalink", "_id": uri }
                    }
            bulk_body.append(json.dumps(index))
            bulk_body.append(json.dumps(doc))
        if len(bulk_body)>0:
            task.log(filename + " indexing")
            es.bulk('\n'.join(bulk_body))

            



mappings = {
    "properties": {
      "Name":   { "type": "text"  },     
      "birthDate":   { "type": "text"  },     
      "deathDate":   { "type": "text"  },    
      "birthLocation":   { "type": "text"  },     
      "deathLocation":   { "type": "text"  },    
      "Abstract":   { "type": "text"  },
      "Alternatives":   { "type": "text"  },     
    }
  }

    
def load_in_elasticsearch(task):
    es = elasticsearch.Elasticsearch()
    ic = elasticsearch.client.IndicesClient(es)
    if ic.exists('judaicalink'):
        ic.delete('judaicalink')
    ic.create(index='judaicalink', body={'mappings': mappings})
    for df in models.Datafile.objects.filter(indexed=True, dataset__indexed=True):
        task.log(df.url + " parsing")
        filename = load_rdf_file(df.url)
        index_file(filename, task)
