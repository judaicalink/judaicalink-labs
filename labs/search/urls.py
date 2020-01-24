from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.search_index, name='search_index'),
    path('load', views.load, name='load'),
    path('search/<str:query>', views.search, {"page" : 1}, name='search'),
        #sets default for pagenumber to 1
    path('search/<str:query>/<int:page>', views.search, name='search'),
        #used if pagenumber is given
]
