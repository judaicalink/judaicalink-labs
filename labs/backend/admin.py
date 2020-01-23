from django.contrib import admin
from django.contrib.admin import AdminSite
import django.db.models as django_models

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


formfield_overrides = {
            django_models.TextField: {'widget': admin.widgets.AdminTextInputWidget}, 
        }


def num_files(ds):
    files = ds.datafile_set.count() 
    indexed = ds.datafile_set.filter(indexed=True).count()
    return "{}/{}".format(indexed, files) 

num_files.short_description = "Indexed / Files"


def set_indexed(modeladmin, request, queryset):
    for ds in queryset:
        ds.set_indexed(True)
    modeladmin.message_user(request, 'Index flags updated.')

def unset_indexed(modeladmin, request, queryset):
    for ds in queryset:
        ds.set_indexed(False)
    modeladmin.message_user(request, 'Index flags updated.')

set_indexed.short_description = "Index selected datasets and files"
unset_indexed.short_description = "So not index selected datasets and files"

class DatafileAdmin(admin.TabularInline):
    model = models.Datafile
    formfield_overrides = formfield_overrides
    extra = 0


class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', num_files]
    list_display_links = ['name']

    formfield_overrides = formfield_overrides     
    inlines = [ DatafileAdmin, ]
    actions = [ set_indexed, unset_indexed ]



admin_site.register(models.Dataset, DatasetAdmin)

class ThreadTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'started', 'ended', 'is_done', 'last_log']
    list_display_links = ['name']
    list_filter = ['is_done', 'name']



admin_site.register(models.ThreadTask, ThreadTaskAdmin)
