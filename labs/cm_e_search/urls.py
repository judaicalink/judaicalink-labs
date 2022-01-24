from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='entity_search_index'),
    path('search_result/', views.result, name='search_result')
]