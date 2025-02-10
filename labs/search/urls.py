from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .sitemaps import StaticViewSitemap

# for the sitemap
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap

from . import views


sitemaps = {'static': StaticViewSitemap}

app_name = 'search'

urlpatterns = [
    path('judaicalink_search_index', views.search_index, name='judaicalink_search_index'),
    path('all_search_nav', views.all_search_nav, name='all_search_nav'),
    path('search', views.search, name='search'),
    path('advanced', views.advanced, name='advanced'),
    # the sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
