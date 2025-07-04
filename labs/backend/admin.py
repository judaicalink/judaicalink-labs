from django.contrib import admin
from django.contrib.admin import AdminSite
import django.db.models as django_models
from django.urls import re_path

from . import views
from . import models


# Register your models here.
class MyAdminSite(AdminSite):
    site_header = "JudaicaLink Labs Backend"

    def get_urls(self):
        urls = super(MyAdminSite, self).get_urls()
        # Note that custom urls get pushed to the list (not appended)
        # This doesn't work with urls += ...
        urls = [
            re_path(
                r"^load_from_github/$",
                self.admin_view(views.load_from_github),
                name="load_from_github",
            ),
            re_path(
                r"^load_solr/$",
                self.admin_view(views.load_solr),
                name="load_solr",
            ),
            re_path(r"^load_fuseki/$", self.admin_view(views.load_fuseki), name="load_fuseki"),
            re_path(
                r"^loader/(?P<action>load|unload|delete)/$",
                self.admin_view(views.loader_manage_all),
                name="loader_manage_all",
            ),
            re_path(
                r"^backend/dashboard/$",
                self.admin_view(views.dashboard),
                name="dashboard",
            ),
            re_path(
                r"^backend/serverstatus/$",
                self.admin_view(views.serverstatus),
                name="serverstatus",
            ),
            re_path(
                r"^backend/commands/$", self.admin_view(views.django_commands), name="commands"
            ),
            re_path(
                r"^backend/run_command/(?P<command>[^/]+)/$",
                self.admin_view(views.run_django_command),
                name="run_command",
            ),
        ] + urls
        return urls


admin_site = MyAdminSite(name="admin")


class ThreadTaskAdmin(admin.ModelAdmin):
    list_display = ["name", "started", "ended", "is_done", "status_ok", "last_log"]
    list_display_links = ["name"]
    list_filter = ["is_done", "name"]


admin_site.register(models.ThreadTask, ThreadTaskAdmin)
