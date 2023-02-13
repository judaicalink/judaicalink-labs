"""labs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin, sitemaps
from django.contrib.admin import AdminSite
from django.urls import include, path
from backend.admin import admin_site
from django.shortcuts import render
from django.conf.urls import handler404, handler500
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap

from django.urls import path
from django.contrib.sitemaps import views
from search.sitemaps import StaticViewSitemap as searchStaticViewSitemap
from cm_search.sitemaps import StaticViewSitemap as cm_searchStaticViewSitemap
from cm_e_search.sitemaps import StaticViewSitemap as cm_e_searchStaticViewSitemap
from data.sitemaps import StaticViewSitemap as dataStaticViewSitemap

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

@cache_page(CACHE_TTL)
def index(request):
    #return HttpResponse(Dataset.objects.all())
    return render(request, "search/root.html")

admin.autodiscover()

sitemaps = {
    'search': searchStaticViewSitemap,
    'cm_search': cm_searchStaticViewSitemap,
    'cm_e_search': cm_searchStaticViewSitemap,
    'data': dataStaticViewSitemap,
            }

urlpatterns = [
    path('admin/', admin_site.urls),
    path('backend/', include('backend.urls', namespace='backend')),
    path('search/', include('search.urls', namespace='search')),
    path('lod/', include('lodjango.urls')),
    path('', index, name='index'),
    path('cm_search/', include('cm_search.urls')),
    path('cm_e_search/', include('cm_e_search.urls')),
    #path('dashboard/', include('dashboard.urls')),
    path('data', include('data.urls')),
    path('contact/', include('contact.urls', namespace='contact')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('issues/', include('issuetracker.urls', namespace='issuetracker')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
       #{'sitemaps': {'blog': GenericSitemap(sitemaps, priority=0.6)}},
       #name='django.contrib.sitemaps.views.sitemap'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'search.views.custom_error_404'
handler500 = 'search.views.custom_error_500'

