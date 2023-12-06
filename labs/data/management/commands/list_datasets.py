import json
import re
import pysolr
import rdflib
import gzip
from django.conf import settings
from django.core.management.base import BaseCommand
from data import models, utils



class Command(BaseCommand):
    help = '''
    List all datasets.
    '''

    def add_arguments(self, parser):
        parser.add_argument('--with-files', action="store_true", help="Show also data files.")
        parser.add_argument('--only-files', action="store_true", help="Show only data files.")
        parser.add_argument('slugs', nargs='*', help="List of dataset slugs")

    def handle(self, *args, **kwargs):
        datasets = []
        if len(kwargs['slugs'])==0:
            datasets = models.Dataset.objects.all()
        else:
            for slug in kwargs['slugs']:
                datasets.extend(models.Dataset.objects.filter(dataslug=slug))
        for ds in datasets:
            if not kwargs['only_files']:
                self.stdout.write(ds.name)
            if kwargs['only_files'] or kwargs['with_files']:
                for df in ds.datafile_set.all():
                    filename = utils.load_rdf_file(df.url)
                    self.stdout.write("{}{}".format("   " if kwargs['with_files'] else "", filename))
