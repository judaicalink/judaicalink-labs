from django.conf import settings
from django.db import models
from pathlib import Path
from django.utils import timezone
from datetime import datetime
from . import hugotools
from . import consumers

class ThreadTask(models.Model):
    name = models.TextField()
    is_done = models.BooleanField(blank=False, default=False)
    status_ok = models.BooleanField(blank=False, default=True)
    started = models.DateTimeField(default=timezone.now)
    ended = models.DateTimeField(null=True)
    log_text = models.TextField()

    dataset = models.ForeignKey(
        'data.Dataset',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='thread_tasks',
    )

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


def _as_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def update_from_markdown(filename):
    path = Path(settings.HUGO_DIR) / filename
    data = hugotools.get_data(str(path))

    try:
        ds = Dataset.objects.get(name=filename[:-3])
    except Dataset.DoesNotExist:
        ds = Dataset()
        ds.name = filename[:-3]
        ds.save()
        ds.refresh_from_db()
    ds.title = data['title']
    ds.loaded = "false" # hardcoded to force reload

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


class Generator(models.Model):
    slug = models.SlugField(primary_key=True)
    title = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)
    schedule_cron = models.CharField(max_length=100, blank=True)  # optional (Doku, nicht ausführen)
    output_dir = models.CharField(max_length=500, blank=True)
    symbol_image = models.ImageField(upload_to="generator_icons/", blank=True, null=True)

    def __str__(self): return self.slug


class Run(models.Model):
    generator = models.ForeignKey(Generator, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("success", "success"), ("error", "error")])
    triples = models.IntegerField(default=0)
    artifact_ttl = models.URLField(blank=True)
    log = models.TextField(blank=True)  # traceback / messages


class Artifact(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="artifacts")
    path = models.CharField(max_length=500)
    url = models.URLField(blank=True)


class Config(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
