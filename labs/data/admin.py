from django.contrib import admin
from django.contrib.admin import AdminSite
import django.db.models as django_models
from backend.admin import admin_site

from . import models

# Register your models here.

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
    list_display = ['name', 'title', 'category', 'loaded', num_loaded, 'indexed', num_indexed]
    list_editable = ['indexed', 'loaded']
    list_display_links = ['name']

    formfield_overrides = formfield_overrides     
    inlines = [ DatafileAdmin, ]
    actions = [ set_indexed, unset_indexed, 'load_fuseki', 'unload_fuseki', 'delete_fuseki' ]

    def load_fuseki(self, request, queryset):
        from backend import tasks
        for ds in queryset:
            slug = ds.dataslug or ds.name
            tasks.call_command_as_task('fuseki_loader', 'load', slug)
        self.message_user(request, 'Load started for selected datasets.')

    load_fuseki.short_description = 'Load in Fuseki'

    def unload_fuseki(self, request, queryset):
        from backend import tasks
        for ds in queryset:
            slug = ds.dataslug or ds.name
            tasks.call_command_as_task('fuseki_loader', 'unload', slug)
        self.message_user(request, 'Unload started for selected datasets.')

    unload_fuseki.short_description = 'Unload from Fuseki'

    def delete_fuseki(self, request, queryset):
        from backend import tasks
        for ds in queryset:
            slug = ds.dataslug or ds.name
            tasks.call_command_as_task('fuseki_loader', 'delete', slug)
        self.message_user(request, 'Delete started for selected datasets.')

    delete_fuseki.short_description = 'Delete from Fuseki'



admin_site.register(models.Dataset, DatasetAdmin)
