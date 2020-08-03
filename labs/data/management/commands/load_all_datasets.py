import json
import re
import rdflib
import gzip
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core import management
from data import models
from data import utils, sparqltools

def create_dataset(name, db_type='mem'):
    res = requests.get(settings.FUSEKI_SERVER + '$/datasets/' + name)
    if res.status_code==404:
        res = requests.post(settings.FUSEKI_SERVER + '$/datasets', {'dbType': db_type, 'dbName':name})

class Command(BaseCommand):
    help = 'load all datasets marked as loaded in Fuseki'

    def handle(self, *args, **kwargs):
        create_dataset('judaicalink')
        for ds in models.Dataset.objects.all():
            if not ds.is_rdf():
                continue
            self.stdout.write(ds.name + " dropping")
            sparqltools.unload(settings.FUSEKI_SERVER + 'judaicalink/update', ds.graph)
            if not ds.loaded:
                continue
            for df in ds.datafile_set.all():
                if df.loaded:
                    filename = utils.load_rdf_file(df.url)
                    self.stdout.write(filename + " loading")
                    sparqltools.load(filename, settings.FUSEKI_SERVER + 'judaicalink/update', ds.graph, log=self.stdout.write)
