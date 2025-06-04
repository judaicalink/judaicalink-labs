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
            re_path(r"^load_fuseki/$", self.admin_view(views.load_fuseki), name="load_fuseki"),
            re_path(
                r"^backend/serverstatus/$",
                self.admin_view(views.serverstatus),
                name="serverstatus",
            ),
            re_path(
                r"^backend/commands/$", self.admin_view(views.django_commands), name="commands"
            ),
        ] + urls
        return urls


admin_site = MyAdminSite(name="admin")


class ThreadTaskAdmin(admin.ModelAdmin):
    list_display = ["name", "started", "ended", "is_done", "status_ok", "last_log"]
    list_display_links = ["name"]
    list_filter = ["is_done", "name"]


admin_site.register(models.ThreadTask, ThreadTaskAdmin)
