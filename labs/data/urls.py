from django.urls import path

from .views import commands, DatasetListView, DatasetDetailView

app_name = 'data'

urlpatterns = [
    path('commands', commands, name='commands'),
    path("datasets/", DatasetListView.as_view(), name="list"),
    path("datasets/<slug:slug>/", DatasetDetailView.as_view(), name="detail"),
]
