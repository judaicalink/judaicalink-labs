from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('load', views.load, name='load'),
    path('search/<str:query>', views.search, name='search')
]
