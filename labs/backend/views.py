from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
import json
import requests
from pathlib import Path
from . import tasks
from . import models
from data import utils as dataset_loader
from . import admin
import time
import shutil
from datetime import datetime


# Create your views here.


def load_from_github(request):
    '''
    Loads all Markdown files from the judaicalink-site Github repository.
    Saves files in data/gh_datasets.
    '''
    tasks.call_command_as_task('sync_datasets')
    return redirect(reverse('admin:data_dataset_changelist'))


def load_elasticsearch(request):
    '''
    Fetches all data files and indexes them in ES.
    '''
    tasks.call_command_as_task('index_all_datasets')
    return redirect(reverse('admin:data_dataset_changelist'))


def load_fuseki(request):
    '''
    Fetches all data files and loads them in Fuseki.
    '''
    tasks.call_command_as_task('load_all_datasets')
    return redirect(reverse('admin:data_dataset_changelist'))


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
        if settings.ELASTICSEARCH_SSL_ENABLED:
            es_main = json.loads(requests.get(settings.ELASTICSEARCH_SERVER, verify=True,
                                              cert=settings.ELASTICSEARCH_SERVER_CERT_PATH,
                                              auth=(settings.ELASTICSEARCH_SERVER_USER, settings.ELASTICSEARCH_SERVER_PASSWORD),
                                              ).content.decode('utf-8'))
            es_stats = json.loads(requests.get(settings.ELASTICSEARCH_SERVER + '_stats', verify=True,
                                               cert=settings.ELASTICSEARCH_SERVER_CERT_PATH,
                                               auth=(settings.ELASTICSEARCH_SERVER_USER, settings.ELASTICSEARCH_SERVER_PASSWORD),
                                               ).content.decode('utf-8'))

        else:
            es_main = json.loads(requests.get(settings.ELASTICSEARCH_SERVER).content.decode('utf-8'))
            es_stats = json.loads(requests.get(settings.ELASTICSEARCH_SERVER + '_stats').content.decode('utf-8'))

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
