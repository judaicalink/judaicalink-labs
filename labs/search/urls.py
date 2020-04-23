from django.contrib import admin
from django.urls import path, include

from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_index, name='search_index'),
    path('load', views.load, name='load'),
    path('search', views.search, name='search'),
]
