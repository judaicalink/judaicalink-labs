import requests
import json
import re
import elasticsearch
import rdflib
import time
import gzip
import os
from . import models
from . import sparqltools
from pathlib import Path
from datetime import datetime
from django.utils.http import http_date
from django.conf import settings


def url_2_filename(url):
    url = url.replace(':', '_').replace('/', '_').replace('__', '_').replace('__', '_')
    return url
    

def get_filename(url):
    return 'data/rdf_files/' + url_2_filename(url)


def load_rdf_file(url):
    headers = {}
    filename = get_filename(url)
    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        headers['If-Modified-Since'] = http_date(int(mtime)) 
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            Path("data/rdf_files").mkdir(parents=True, exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(res.content)
    except:
        print("Connection error: " + url)
    return filename


    
