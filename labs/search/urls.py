from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'search'

urlpatterns = [
    path('judaicalink_search_index', views.search_index, name='judaicalink_search_index'),
    path('all_search_nav', views.all_search_nav, name='all_search_nav'),
    path('load', views.load, name='load'),
    path('search', views.search, name='search'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
