from django.contrib import admin
from django.urls import path, include, re_path

from . import views

urlpatterns = [
    re_path(r'^grid/(?P<path>.+)$', views.get_grid, name='get-grid'),
    re_path(r'^(?P<path>.+)$', views.get, name='get'),
]
