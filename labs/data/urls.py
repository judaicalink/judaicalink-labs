from django.contrib import admin
from django.urls import path, include
# for the sitemap
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap

from .views import commands, DatasetListView, DatasetDetailView

app_name = 'data'

urlpatterns = [
    path('commands', commands, name='commands'),
    path("datasets/", DatasetListView.as_view(), name="list"),
    path("datasets/<slug:slug>/", DatasetDetailView.as_view(), name="detail"),
]