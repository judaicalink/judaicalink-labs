from django.contrib import admin
from django.contrib.admin import AdminSite

from . import views
from . import models

# Register your models here.
class MyAdminSite(AdminSite):
    site_header = 'JudaicaLink Labs Backend'

    def get_urls(self):
        from django.conf.urls import url
        urls = super(MyAdminSite, self).get_urls()
        # Note that custom urls get pushed to the list (not appended)
        # This doesn't work with urls += ...
        urls = [
            url(r'^test/$', self.admin_view(views.admintest))
        ] + urls
        return urls

admin_site = MyAdminSite()

admin_site.register(models.Dataset)
