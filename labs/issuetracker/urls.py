# URL's

from django.urls import path

from . import views

app_name = 'issuetracker'

urlpatterns = [
    path('fab', views.fab, name='fab'),
    path('issue_form', views.issue_create, name='issue_create'),
    path('issue_submit', views.issue_submit, name='issue_submit'),
    path('issue_close/<str:uuid>', views.issue_close, name='issue_close'),
    path('logout', views.logout_view, name='logout'),
]