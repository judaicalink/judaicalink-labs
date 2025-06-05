from django.urls import path
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import SimpleSearchAPIView, AdvancedSearchAPIView
from .solrapi import JudaicalinkProxy, CMProxy, CMEntitiesProxy, CMEntityNamesProxy, CMMetaProxy


urlpatterns = [
    path('judaicalink/', JudaicalinkProxy.as_view(), name='judaicalink_search'),
    path('cm/', CMProxy.as_view(), name='cm_search'),
    path('cm/entities/', CMEntitiesProxy.as_view(), name='cm_entities_search'),
    path('cm/meta/', CMMetaProxy.as_view(), name='cm_meta_search'),
    path('cm/names/', CMEntityNamesProxy.as_view(), name='cm_entity_names_search'),
]

# For Swagger
schema_view = get_schema_view(
    openapi.Info(
      title="Judaicalink Search API",
      default_version='v1',
      description="API for Judaicalink",
      contact=openapi.Contact(email="info@judaicalink.org"),
      license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
