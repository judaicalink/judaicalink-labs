from django.contrib import sitemaps
from django.urls import reverse
from .views import index

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['index']

    def location(self, item):
        return reverse(item)