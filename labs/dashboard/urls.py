from django.contrib import admin
from django.urls import path, include

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.test, name='test'),
]
