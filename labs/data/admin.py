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
    actions = [ set_indexed, unset_indexed ]



admin_site.register(models.Dataset, DatasetAdmin)
