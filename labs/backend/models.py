from django.db import models
from datetime import datetime
from django.utils import timezone
# Create your models here.
from . import consumers
from . import hugotools

class Dataset(models.Model):
    name = models.TextField()
    title = models.TextField()
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
    data = hugotools.get_data('backend/gh_datasets/{}'.format(filename))
    try:
        ds = Dataset.objects.get(name=filename[:-3])
    except Dataset.DoesNotExist:
        ds = Dataset()
        ds.name = filename[:-3]
        ds.save()
        ds.refresh_from_db()
    ds.title = data['title']
    ds.loaded = data['loaded']
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




class ThreadTask(models.Model):
    name = models.TextField()
    is_done = models.BooleanField(blank=False, default=False)
    status_ok = models.BooleanField(blank=False, default=True)
    started = models.DateTimeField(default = timezone.now)
    ended = models.DateTimeField(null=True)
    log_text = models.TextField()


    def done(self):
        self.is_done = True
        self.ended = datetime.now()
        self.save()


    def log(self, message):
        self.refresh_from_db()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.log_text += '\n' + timestamp + ": " + message
        self.log_text = self.log_text.strip()
        self.save() 
        consumers.send_sub_message('task{}'.format(self.id), submessage=message)
        print('Logged: {}'.format(message))



    def last_log(self):
        msgs = self.log_text.split('\n')
        for i in range(len(msgs) - 1, 0, -1):
            if msgs[i].strip():
                return msgs[i]
        return ""

    def __str__(self):
        return "{}".format(self.name)
