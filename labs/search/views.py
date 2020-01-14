from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

from backend.models import Dataset

def index(request):
    return HttpResponse(Dataset.objects.all())