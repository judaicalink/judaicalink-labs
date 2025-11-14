import django.db.models as django_models
from backend import tasks
from django.contrib import admin

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
    inlines = [DatafileAdmin, ]
    actions = [set_indexed, unset_indexed, 'load_fuseki', 'unload_fuseki', 'delete_fuseki']

    def get_dataset_log(slug: str):
        path = Path(f"/path/to/logs/{slug}.log")
        if not path.exists():
            return "No log available."
        with path.open(encoding="utf-8") as f:
            return f.read().splitlines()[-500:]  # letzte 500 Zeilen

    def load_fuseki(self, request, queryset):
        for ds in queryset:
            slug = ds.dataslug or ds.name
            tasks.call_command_as_task('fuseki_loader', 'load', slug)
        self.message_user(request, 'Load started for selected datasets.')

    load_fuseki.short_description = 'Load in Fuseki'

    def unload_fuseki(self, request, queryset):
        for ds in queryset:
            slug = ds.dataslug or ds.name
            tasks.call_command_as_task('fuseki_loader', 'unload', slug)
        self.message_user(request, 'Unload started for selected datasets.')

    unload_fuseki.short_description = 'Unload from Fuseki'

    # inside DatasetAdmin
    def delete_fuseki(self, request, queryset):
        from django.core.management import call_command
        from django.core.management.base import CommandError

        ok, fail = 0, 0
        for obj in queryset:
            slug = obj.dataslug or obj.name
            try:
                call_command("fuseki_loader", "delete", slug)
                obj.delete()  # <-- also delete the Django record
                ok += 1
            except CommandError as e:
                fail += 1
        self.message_user(request, f"Deleted {ok} dataset(s); {fail} failed.")

    delete_fuseki.short_description = 'Delete from Fuseki'

    change_list_template = 'admin/data/dataset/change_list.html'


admin.site.register(models.Dataset, DatasetAdmin)
