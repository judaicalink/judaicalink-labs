import json
import re
import pysolr
import rdflib
import gzip
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core import management
from data import models
from data import utils

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


class Command(BaseCommand):
    help = 'index all datasets marked as indexed in solr'

    def handle(self, *args, **kwargs):
        solr = pysolr.Solr(settings.SOLR_SERVER, always_commit=True, timeout=10)
        ic = pysolr.client.IndicesClient(solr)
        if ic.exists(settings.JUDAICALINK_INDEX):
            ic.delete(settings.JUDAICALINK_INDEX)
        ic.create(index=settings.JUDAICALINK_INDEX, body={'mappings': mappings})
        for df in models.Datafile.objects.filter(indexed=True, dataset__indexed=True):
            if df.dataset.is_rdf():
                self.stdout.write(df.url + " parsing")
                filename = utils.load_rdf_file(df.url)
                management.call_command("index_file", filename, stdout=self.stdout, stderr=self.stderr)
        for df in models.Datafile.objects.filter(indexed=True, dataset__indexed=True):
            if df.dataset.category == 'support':
                openfunc = open
                filename = utils.load_rdf_file(df.url)
                if filename.endswith(".gz"):
                    openfunc = gzip.open
                with openfunc(filename, "rt", encoding="utf8") as f:
                    self.stdout.write("indexing: " + filename)
                    solr.add(json.load(f))

