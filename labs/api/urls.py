from django.urls import path
from .solrapi import (
    JudaicalinkProxy, CMProxy,
    CMEntitiesProxy, CMEntityNamesProxy, CMMetaProxy
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# API endpoints
urlpatterns = [
    path('judaicalink/',        JudaicalinkProxy.as_view(),    name='api-jl'),
    path('cm/',                 CMProxy.as_view(),             name='api-cm'),
    path('cm/entities/',        CMEntitiesProxy.as_view(),      name='api-cm-entities'),
    path('cm/names/',           CMEntityNamesProxy.as_view(),   name='api-cm-entity-names'),
    path('cm/meta/',            CMMetaProxy.as_view(),          name='api-cm-meta'),
]

# Swagger / ReDoc
schema_view = get_schema_view(
    openapi.Info(
        title="Judaicalink Search API",
        default_version='v1',
        description="Solr‐backed search endpoints",
        contact=openapi.Contact(email="info@judaicalink.org"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='api-swagger'),
    path('redoc/',   schema_view.with_ui('redoc',   cache_timeout=0), name='api-redoc'),
]
