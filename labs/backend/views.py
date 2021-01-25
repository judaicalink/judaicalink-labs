from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
import requests
import json
from . import hugotools
from . import tasks
from . import models
from . import dataset_loader
from . import admin
import time
import shutil
from datetime import datetime
from pathlib import Path


# Create your views here.


def load_from_github(request):
    '''
    Loads all Markdown files from the judaicalink-site Github repository.
    Saves files in gh_datasets.
    '''
    tasks.start_task('Github Import', task_github)
    return redirect(reverse('admin:backend_dataset_changelist'))


def task_github(task):
    try:
        Path("backend/gh_datasets").mkdir(parents=True, exist_ok=True)
        gh_res = requests.get('https://api.github.com/repos/wisslab/judaicalink-site/contents/content/datasets')
        gh_datasets = json.loads(gh_res.content.decode('utf-8'))
        for gh_dataset in gh_datasets:
            task.log('Importing {}'.format(gh_dataset['name']))
            gh_ds_md = requests.get(gh_dataset['download_url'])
            with open('backend/gh_datasets/{}'.format(gh_dataset['name']), 'wb') as f:
                f.write(gh_ds_md.content)
            models.update_from_markdown(gh_dataset['name'])
        
    except Exception as e:
        raise e


def load_elasticsearch(request):
    '''
    Fetches all data files and indexes them in ES.
    '''
    tasks.start_task('Elasticsearch loader', dataset_loader.load_in_elasticsearch)
    return redirect(reverse('admin:backend_dataset_changelist'))


def load_fuseki(request):
    '''
    Fetches all data files and loads them in Fuseki.
    '''
    tasks.start_task('Fuseki loader', dataset_loader.load_in_fuseki)
    return redirect(reverse('admin:backend_dataset_changelist'))


def test_thread(request):
    tasks.start_task("Sleeper test", sleeper)
    return HttpResponse('started')

def sleeper(task):
    task.log("I'm a sleeper!")
    time.sleep(10)
    task.log('Awake')


def dirsize(directory):
    root_directory = Path(directory)
    return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file() )


def serverstatus(request):
    context = {
        'site_header': admin.admin_site.site_header,
        'elasticsearch': [('Status', 'offline')],
        'fuseki': [('Status', 'offline')],
            }
    try:
        es_main = json.loads(requests.get(settings.ELASTICSEARCH_SERVER).content.decode('utf-8'))
        es_stats = json.loads(requests.get(settings.ELASTICSEARCH_SERVER+'_stats').content.decode('utf-8'))
        context['elasticsearch'] = [
            ('Version', es_main['version']['number']),
            ('Name', es_main['name']),
            ('Cluster Name', es_main['cluster_name']),
            ('Indices', '\n'.join(es_stats['indices']))
            ]
        for index in es_stats['indices']:
            context['elasticsearch'].append((index + ' Docs', "{:,}".format(es_stats['indices'][index]['total']['docs']['count'])))
            context['elasticsearch'].append((index + ' Size', "{:.2f} M".format(es_stats['indices'][index]['total']['store']['size_in_bytes']/1024/1024)))
        if hasattr(settings, 'ELASTICSEARCH_STORAGE'):
            df = shutil.disk_usage(settings.ELASTICSEARCH_STORAGE)
            context['elasticsearch'].append(('Disk space (' + settings.ELASTICSEARCH_STORAGE + ')', "{:.2f} / {:.2f} G".format(df.free / 2**30, df.total/2**30)))
            context['elasticsearch'].append(('Disk used (' + settings.ELASTICSEARCH_STORAGE + ')', "{:.2f} M".format(dirsize(settings.ELASTICSEARCH_STORAGE)/2**20)))
    except Exception as e:
        print(str(e))
    
    try:
        f_main = json.loads(requests.get(settings.FUSEKI_SERVER+'$/server').content.decode('utf-8'))
        
        context['fuseki'] = [
            ('Version', f_main['version']),
            ('Started', datetime.fromisoformat(f_main['startDateTime']).strftime("%Y-%m-%d %H:%M")),
            ('Datasets', '\n'.join([ds['ds.name'] for ds in f_main['datasets']]))
                ]
        if hasattr(settings, 'FUSEKI_STORAGE'):
            df = shutil.disk_usage(settings.FUSEKI_STORAGE)
            context['fuseki'].append(('Disk space (' + settings.FUSEKI_STORAGE + ')', "{:.2f} / {:.2f} G".format(df.free / 2**30, df.total/2**30)))
            context['fuseki'].append(('Disk used (' + settings.FUSEKI_STORAGE  + ')', "{:.2f} M".format(dirsize(settings.FUSEKI_STORAGE)/2**20)))
    except Exception as e:
        print(str(e))
    return render(request, 'admin/serverstatus.html', context)
