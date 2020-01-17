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
            url(r'^load_from_github/$', self.admin_view(views.load_from_github), name='load_from_github'),
            url(r'^test-thread/$', self.admin_view(views.test_thread), name='test_thread')
        ] + urls
        return urls

admin_site = MyAdminSite()

admin_site.register(models.Dataset)

class ThreadTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_done', 'last_log']
    list_display_links = ['name']



admin_site.register(models.ThreadTask, ThreadTaskAdmin)
