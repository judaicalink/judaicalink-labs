from django.contrib import sitemaps
from django.urls import reverse

from .views import index, search, all_search_nav, search_index

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['index', 'search:search', 'search:all_search_nav', 'search:judaicalink_search_index']

    def location(self, item):
        return reverse(item)