from django.contrib import sitemaps
from django.urls import reverse
from .views import index, result, get_names

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['entity_search_index', 'search_result']

    def location(self, item):
        return reverse(item)