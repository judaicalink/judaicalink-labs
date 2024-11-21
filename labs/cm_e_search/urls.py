from django.urls import path
# for the sitemap
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

from . import views

sitemaps = {'static': StaticViewSitemap}

app_name = 'cm_e_search'

urlpatterns = [
    path('', views.index, name='entity_search_index'),
    path('search_result/', views.result, name='search_result'),
    path('/api/get_names/', views.get_names, name='get_names'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
