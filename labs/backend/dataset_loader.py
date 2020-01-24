import requests
import os
from . import models
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

    
def load_in_elasticsearch(task):
    for df in models.Datafile.objects.filter(indexed=True, dataset__indexed=True):
        task.log(df.url)
        load_rdf_file(df.url)

    
