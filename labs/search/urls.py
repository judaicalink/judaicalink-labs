from django.contrib import admin
from django.urls import path, include

from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_index, name='search_index'),
    path('all_search_nav', views.all_search_nav, name='all_search_nav'),
    path('load', views.load, name='load'),
    path('search', views.search, name='search'),
]
