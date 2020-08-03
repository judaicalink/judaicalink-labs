from django.db import models
from datetime import datetime
from django.utils import timezone
# Create your models here.
from . import hugotools

class Dataset(models.Model):
    name = models.TextField()
    title = models.TextField()
    dataslug = models.TextField(null=True)
    indexed = models.BooleanField(default=False)
    loaded = models.BooleanField(default=False)
    graph = models.TextField(null=True)
    category = models.TextField(null=True)

    
    def set_indexed(self, value):
        self.indexed = value
        for file in self.datafile_set.all():
            file.indexed = value
            file.save()
        self.save()

    
    def set_loaded(self, value):
        self.loaded = value
        for file in self.datafile_set.all():
            file.loaded = value
            file.save()
        self.save()

    def is_rdf(self):
        return self.graph is not None and self.graph.strip() != ''

    def __str__(self):
        return "Dataset: " + self.name


class Datafile(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    url = models.TextField()
    description = models.TextField()
    indexed = models.BooleanField(default=False)
    loaded = models.BooleanField(default=False)


def update_from_markdown(filename):
    data = hugotools.get_data('data/gh_datasets/{}'.format(filename))
    try:
        ds = Dataset.objects.get(name=filename[:-3])
    except Dataset.DoesNotExist:
        ds = Dataset()
        ds.name = filename[:-3]
        ds.save()
        ds.refresh_from_db()
    ds.title = data['title']
    ds.loaded = data['loaded']
    if 'dataslug' in data:
        ds.dataslug = data['dataslug']
    if 'category' in data:
        ds.category = data['category']
    if 'graph' in data:
        ds.graph = data['graph']
    ds.datafile_set.all().delete()
    for file in data['files']:
        datafile = Datafile()
        datafile.dataset = ds
        datafile.loaded = ds.loaded
        datafile.url = file['url']
        if 'description' in file:
            datafile.description = file['description']
        datafile.save()
    ds.save()




