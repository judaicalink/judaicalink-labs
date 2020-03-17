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
            url(r'^load_elasticsearch/$', self.admin_view(views.load_elasticsearch), name='load_elasticsearch'),
            url(r'^load_fuseki/$', self.admin_view(views.load_fuseki), name='load_fuseki'),
            url(r'^test-thread/$', self.admin_view(views.test_thread), name='test_thread'),
            url(r'^backend/serverstatus/$', self.admin_view(views.serverstatus), name='serverstatus'),
        ] + urls
        return urls


admin_site = MyAdminSite(name='admin')


formfield_overrides = {
            django_models.TextField: {'widget': admin.widgets.AdminTextInputWidget}, 
        }


def num_indexed(ds):
    files = ds.datafile_set.count() 
    indexed = ds.datafile_set.filter(indexed=True).count()
    return "{}/{}".format(indexed, files) 

num_indexed.short_description = "Indexed / Files"

def num_loaded(ds):
    files = ds.datafile_set.count() 
    loaded = ds.datafile_set.filter(loaded=True).count()
    return "{}/{}".format(loaded, files) 

num_loaded.short_description = "Loaded / Files"


def set_indexed(modeladmin, request, queryset):
    for ds in queryset:
        ds.set_indexed(True)
    modeladmin.message_user(request, 'Index flags updated.')

def unset_indexed(modeladmin, request, queryset):
    for ds in queryset:
        ds.set_indexed(False)
    modeladmin.message_user(request, 'Index flags updated.')

set_indexed.short_description = "Index selected datasets and files"
unset_indexed.short_description = "Do not index selected datasets and files"

class DatafileAdmin(admin.TabularInline):
    model = models.Datafile
    formfield_overrides = formfield_overrides
    extra = 0


class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'loaded', num_loaded, 'indexed', num_indexed]
    list_editable = ['indexed', 'loaded']
    list_display_links = ['name']

    formfield_overrides = formfield_overrides     
    inlines = [ DatafileAdmin, ]
    actions = [ set_indexed, unset_indexed ]



admin_site.register(models.Dataset, DatasetAdmin)

class ThreadTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'started', 'ended', 'is_done', 'status_ok', 'last_log']
    list_display_links = ['name']
    list_filter = ['is_done', 'name']



admin_site.register(models.ThreadTask, ThreadTaskAdmin)
