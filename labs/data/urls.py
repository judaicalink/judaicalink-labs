from django.contrib import admin
from django.urls import path, include
# for the sitemap
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

from . import views

app_name = 'data'
sitemaps = {'static': StaticViewSitemap}

urlpatterns = [
    path('', views.index, name='index'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
