import gzip
import json
import pysolr
import rdflib
import re
from django.conf import settings
from django.core.management.base import BaseCommand

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
    value = re.sub('\s+', ' ', value).strip()
    return value


class Command(BaseCommand):
    help = 'Index data from a file in solr'

    def add_arguments(self, filepath):
        filepath.add_argument('filepath', type=str, help='Filepath to file that needs to be indexed')

    def handle(self, *args, **kwargs):
        filepath = kwargs['filepath']
        openfunc = open
        if filepath.endswith(".gz"):
            openfunc = gzip.open
        with openfunc(filepath, "rt", encoding="utf8") as f:
            g = rdflib.Graph()
            g.parse(f, format='n3')
            solr = pysolr.Solr(settings.SOLR_SERVER, always_commit=True, timeout=10)
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
                            doc[f] = [o]
                    else:
                        data[s] = {
                            f: [o]
                        }
            bulk_body = []
            for s in data:
                doc = {}
                for f in data[s]:
                    values = data[s][f]
                    if len(values) == 0:
                        continue
                    values = ' - '.join(values)
                    if f == 'Abstract':
                        values = cleanstring(values, ['"', '{', '}'])
                    if f == 'Alternatives':
                        values = cleanstring(values, ['"', '{', '}', '.'])
                    doc[f] = values
                # indexing slug
                dataslug = s
                dataslug = dataslug.replace("http://data.judaicalink.org/data/", "").split("/")[0]
                doc["dataslug"] = dataslug
                index = {
                    "update": {"_index": settings.JUDAICALINK_INDEX, "_id": s}
                }
                bulk_body.append(json.dumps(index))
                bulk_body.append(json.dumps({"doc": doc, "doc_as_upsert": True}))
            if len(bulk_body) > 0:
                self.stdout.write('indexing successful!')
                solr.add(bulk_body, commit=True)
