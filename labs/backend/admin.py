from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import re_path
from django.utils.html import escape
from django.utils.safestring import mark_safe

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

@admin.register(models.ThreadTask)
class ThreadTaskAdmin(admin.ModelAdmin):
    """
    Admin-Ansicht für ALLE Tasks (ThreadTask), unabhängig vom Dataset.
    """

    list_display = (
        "id",
        "name",
        "dataset",
        "started",
        "ended",
        "is_done",
        "status_icon",
        "short_last_line",
    )

    list_filter = (
        "is_done",
        "status_ok",
        "dataset",
    )

    search_fields = (
        "name",
        "log_text",
        "dataset__name",
        "dataset__dataslug",
    )

    date_hierarchy = "started"
    ordering = ("-started",)

    readonly_fields = (
        "name",
        "dataset",
        "is_done",
        "status_ok",
        "started",
        "ended",
        "log_pretty",
    )

    fieldsets = (
        (None, {
            "fields": (
                "name",
                "dataset",
            )
        }),
        ("Status", {
            "fields": (
                "is_done",
                "status_ok",
                "started",
                "ended",
            )
        }),
        ("Log", {
            "fields": ("log_pretty",)
        }),
    )

    @admin.display(description="Status")
    def status_icon(self, obj):
        if not obj.is_done:
            return "⏳"
        return "✅" if obj.status_ok else "❌"

    @admin.display(description="Letzte Logzeile")
    def short_last_line(self, obj):
        last = obj.last_log()
        if not last:
            return "—"
        last = last.strip()
        if len(last) > 120:
            return last[:117] + "…"
        return last

    @admin.display(description="Task-Log (Tail)")
    def log_pretty(self, obj):
        text = obj.log_text or ""
        text = text.strip()
        if not text:
            return "Keine Logeinträge."

        lines = [l for l in text.splitlines() if l.strip()]
        tail_lines = 200
        tail = "\n".join(lines[-tail_lines:])

        html = (
            "<details open>"
            "<summary>Letzte "
            f"{min(tail_lines, len(lines))} Zeilen anzeigen</summary>"
            "<pre style='max-height: 500px; overflow: auto;'>"
            f"{escape(tail)}"
            "</pre></details>"
        )
        return mark_safe(html)


admin_site.register(models.ThreadTask, ThreadTaskAdmin)

