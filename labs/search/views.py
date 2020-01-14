from django.shortcuts import render
from django.http import HttpResponse
import requests

# Create your views here.

from backend.models import Dataset

def index(request):
    return HttpResponse(Dataset.objects.all())


def load(request):
    with open('../data/textfile-djh.json', 'rb') as f:
        data = f.read()
        print(data)
        headers = {'content-type': 'application/json'}
        response = requests.post('http://localhost:9200/judaicalink/doc/_bulk?pretty', data=data, headers=headers)
        return HttpResponse(response)