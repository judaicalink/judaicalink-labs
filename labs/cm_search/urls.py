from django.urls import path
# for the sitemap
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

from . import views

sitemaps = {'static': StaticViewSitemap}

urlpatterns = [
    path('', views.index, name='cm_search_index'),
    path('search_result/', views.result, name='search_result'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]