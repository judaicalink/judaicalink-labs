import django.db.models as django_models
from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import escape
from django.utils.safestring import mark_safe
from pathlib import Path

from . import models, views
from .models import ThreadTask
from .tasks import run_management_command

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
    can_delete = False  # löscht die Delete-Checkbox-Spalte
    show_change_link = False  # kein „Stift“-Icon
    readonly_fields = ("url", "description", "indexed", "loaded")
    max_num = 0  # keine neuen Datafiles per Admin anlegen

    # Reihenfolge und sichtbare Felder im Inline
    fields = ("url", "description", "indexed", "loaded")

    # Diese Felder nur anzeigen, nicht bearbeitbar:
    readonly_fields = ("indexed", "loaded",)

    # Checkbox-Spalte zum Löschen ausblenden, aber Bearbeiten erlauben
    can_delete = False


class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'category', 'graph', 'loaded', 'indexed', 'generation_status_short']
    list_display_links = ['name']

    formfield_overrides = formfield_overrides
    inlines = [DatafileAdmin, ]
    actions = ['regenerate_and_load_async', 'load_fuseki_and_solr_async', 'load_fuseki', 'unload_fuseki', 'load_into_solr',
               'unload_from_solr',  'unload_fuseki_and_solr_async', 'delete_ds']
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "title",
                "dataslug",
                "category",
            )
        }),
        ("Status", {
            "fields": (
                "loaded",
                "indexed",
                "generation_status_short",
            )
        }),
        ("Logs", {
            "fields": (
                "generator_log",
                "task_log",
            )
        }),
    )
    readonly_fields = (
        "loaded",
        "indexed",
        "generation_status_short",
        "generator_log",
        "task_log",
    )

    # -------- Kurzstatus für die Liste --------
    @admin.display(description="Gen.-Status")
    def generation_status_short(self, obj):
        status, _ = self._get_status_and_error(obj)
        # nur ein Wort + Symbol
        if status.startswith("OK"):
            return "✅"
        if status.startswith("läuft"):
            return "⏳"
        if status.startswith("Fehlgeschlagen"):
            return "❌"
        return status

    # -------- Detaillierter Status für Detailansicht --------
    @admin.display(description="Generierungsstatus")
    def generation_status(self, obj):
        status, error = self._get_status_and_error(obj)

        if status.startswith("OK"):
            # grüner Haken + Zeitstempel
            return mark_safe(f"<span style='color:green;'>✅ {status}</span>")

        if status.startswith("Fehlgeschlagen"):
            # rotes Kreuz + letzte Fehlerzeile
            short_err = error or "(siehe Log unten)"
            return mark_safe(
                f"<span style='color:red;'>❌ {status}<br><small>{short_err}</small></span>"
            )

        # laufend oder kein Task
        return status

    def _get_status_and_error(self, obj):
        task = obj.thread_tasks.order_by("-started").first()
        slug = obj.dataslug or obj.name

        # kein Task → nur Generator-Log auswerten
        if not task:
            gen_status, gen_line = self._detect_generator_result(slug)
            if gen_status == "SUCCESS":
                return "OK (Generator erfolgreich, kein Task)", None
            if gen_status == "ERROR":
                return "Fehlgeschlagen (Generator)", gen_line
            return "kein Task/kein Log", None

        # Task läuft noch
        if not task.is_done:
            return f"läuft seit {task.started}", None

        # Task fertig → mit Generator-Ergebnis kombinieren
        gen_status, gen_line = self._detect_generator_result(slug)

        if task.status_ok and gen_status == "SUCCESS":
            return f"OK (fertig {task.ended})", None

        if gen_status == "ERROR":
            return f"Fehlgeschlagen (fertig {task.ended})", gen_line

        if not task.status_ok:
            # Fallback: nutze Task-Log als Fehler
            return f"Fehlgeschlagen (fertig {task.ended})", task.last_log()

        # ansonsten weiß man es nicht genau, aber Task war OK
        return f"OK (fertig {task.ended})", None

    def _detect_generator_result(self, slug: str):
        """Liest logs/<slug>.log und gibt ('SUCCESS'|'ERROR'|'UNKNOWN', letzte_relevante_Zeile) zurück."""
        log_dir = getattr(settings, "GENERATOR_LOG_DIR", None)
        if not log_dir:
            return "UNKNOWN", None

        path = Path(log_dir) / f"{slug}.log"
        if not path.exists():
            return "UNKNOWN", None

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return "UNKNOWN", None

        lines = [l for l in text.splitlines() if l.strip()]
        lines_rev = list(reversed(lines))

        last_error = None
        last_success = None

        for line in lines_rev:
            lower = line.lower()
            # typische Fehler-Marker
            if "failed" in lower or "error" in lower:
                last_error = line
                break
            # typische Erfolgs-Marker
            if "generation finished" in lower or "generation finished" in lower or "copied →" in line:
                last_success = line
                break

        if last_error:
            return "ERROR", last_error
        if last_success:
            return "SUCCESS", last_success
        return "UNKNOWN", None

    # -------- Log aus logs/<slug>.log (nur Tail) --------
    @admin.display(description="Generator-Log")
    def generator_log(self, obj):
        slug = obj.dataslug or obj.name
        log_dir = getattr(settings, "GENERATOR_LOG_DIR", None)
        if not log_dir:
            return "GENERATOR_LOG_DIR ist nicht konfiguriert."

        path = Path(log_dir) / f"{slug}.log"
        if not path.exists():
            return f"Kein Log gefunden ({path})"

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Fehler beim Lesen von {path}: {e}"

        lines = text.splitlines()
        tail_lines = 100  # Anzahl der Zeilen, die du sehen willst
        tail = "\n".join(lines[-tail_lines:])

        html = (
            "<details>"
            "<summary>Log anzeigen (letzte "
            f"{min(tail_lines, len(lines))} Zeilen)</summary>"
            "<pre style='max-height:400px; overflow:auto;'>"
            f"{tail}"
            "</pre></details>"
        )
        return mark_safe(html)

    @admin.display(description="Letzter Task-Log")
    def task_log(self, obj):
        """
        Zeigt den Log des letzten ThreadTask an, der mit dem Dataset verknüpft ist.
        Nur die letzten 200 Zeilen, in einem <details>-Block.
        """
        task = obj.thread_tasks.order_by("-started").first()
        if not task:
            return "Kein Task-Log vorhanden."

        text = task.log_text or ""
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            return "Log ist leer."

        tail_lines = 200
        tail = "\n".join(lines[-tail_lines:])

        html = (
            "<details>"
            "<summary>Task-Log anzeigen (letzte "
            f"{min(tail_lines, len(lines))} Zeilen)</summary>"
            "<pre style='max-height:400px; overflow:auto;'>"
            f"{escape(tail)}"
            "</pre></details>"
        )
        return mark_safe(html)

    # -------- Async-Action: neu generieren & laden --------
    def regenerate_and_load_async(self, request, queryset):
        started, skipped = 0, 0

        for obj in queryset:
            slug = obj.dataslug or obj.name

            # Läuft schon ein Task für dieses Dataset?
            running = obj.thread_tasks.filter(is_done=False).exists()
            if running:
                skipped += 1
                self.message_user(
                    request,
                    f"Dataset '{slug}' wird bereits generiert – neuer Start wird übersprungen.",
                    level=messages.WARNING,
                )
                continue

            # Neuen Task starten
            task_id = run_management_command(
                task_name=f"generate_dataset:{slug}",
                command="generate_and_load_dataset",
                args=[slug],
            )

            # Task mit Dataset verknüpfen
            task = ThreadTask.objects.get(pk=task_id)
            task.dataset = obj
            task.save()

            started += 1

        if started:
            self.message_user(
                request,
                f"{started} Dataset(s) zur Generierung/Ladung gestartet.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} Dataset(s) wurden übersprungen (läuft bereits).",
                level=messages.INFO,
            )

    regenerate_and_load_async.short_description = (
        "Dataset neu generieren (inkl. Metadaten) und in Fuseki laden (asynchron)"
    )

    def get_dataset_log(slug: str):
        path = Path(getattr(settings, 'JUDAICALINK_GENERATORS_PATH', None), f"/logs/{slug}.log")
        if not path.exists():
            return "No log available."
        with path.open(encoding="utf-8") as f:
            return f.read().splitlines()[-500:]  # letzte 500 Zeilen

    def load_fuseki(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            # wie bisher: Fuseki arbeitet mit dem Dataset-Namen
            slug = ds.name

            try:
                task_id = run_management_command(
                    task_name=f"fuseki_load:{slug}",
                    command="fuseki_loader",
                    args=["load", slug],
                )

                # Task mit Dataset verknüpfen, damit task_log/generation_status funktionieren
                task = ThreadTask.objects.get(pk=task_id)
                task.dataset = ds
                task.save()

                started += 1
                messages.success(
                    request,
                    f"Fuseki-Load-Task für Dataset '{slug}' gestartet."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des Fuseki-Load-Tasks für {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} Fuseki-Load-Task(s) gestartet; {fail} fehlgeschlagen.",
        )

    load_fuseki.short_description = 'Load in Fuseki'

    def unload_fuseki(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            try:
                task_id = run_management_command(
                    task_name=f"fuseki_unload:{slug}",
                    command="fuseki_loader",
                    args=["unload", slug],
                )

                task = ThreadTask.objects.get(pk=task_id)
                task.dataset = ds
                task.save()

                started += 1
                messages.success(
                    request,
                    f"Fuseki-Unload-Task für Dataset '{slug}' gestartet."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des Fuseki-Unload-Tasks für {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} Fuseki-Unload-Task(s) gestartet; {fail} fehlgeschlagen.",
        )

    unload_fuseki.short_description = 'Unload from Fuseki'

    @admin.action(description="Load selected datasets into SOLR")
    def load_into_solr(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            try:
                # Neuen ThreadTask starten
                task_id = run_management_command(
                    task_name=f"solr_load_dataset:{slug}",
                    command="solr_load_dataset",
                    args=[slug],
                )

                task = ThreadTask.objects.get(pk=task_id)
                task.dataset = ds
                task.save()

                started += 1
                messages.success(
                    request,
                    f"SOLR-Load-Task für Dataset '{slug}' gestartet."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des SOLR-Load-Tasks für {slug}: {e}"
                )
                ds.indexed = False
                ds.save()

        self.message_user(
            request,
            f"{started} SOLR-Load-Task(s) gestartet; {fail} fehlgeschlagen.",
        )

    load_into_solr.short_description = "Load selected datasets into SOLR"

    @admin.action(description="Unload selected datasets from SOLR")
    def unload_from_solr(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            # Wir nutzen hier ebenfalls den Dataset-Namen; der Command
            # übersetzt ihn intern in das echte dataslug (siehe oben).
            slug = ds.dataslug or ds.name

            try:
                task_id = run_management_command(
                    task_name=f"solr_delete_dataset:{slug}",
                    command="solr_delete_dataset",
                    args=[slug],
                )

                task = ThreadTask.objects.get(pk=task_id)
                task.dataset = ds
                task.save()

                started += 1
                messages.success(
                    request,
                    f"SOLR-Unload-Task für Dataset '{slug}' gestartet."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des SOLR-Unload-Tasks für {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} SOLR-Unload-Task(s) gestartet; {fail} fehlgeschlagen.",
        )

    unload_from_solr.short_description = "Unload selected datasets from SOLR"

    @admin.action(description="Load selected datasets into Fuseki & SOLR (async)")
    def load_fuseki_and_solr_async(self, request, queryset):
        started_fuseki = 0
        started_solr = 0
        failed = 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            # 1. Fuseki-Load starten
            try:
                fuseki_task_id = run_management_command(
                    task_name=f"fuseki_load:{slug}",
                    command="fuseki_loader",
                    args=["load", slug],
                )
                fuseki_task = ThreadTask.objects.get(pk=fuseki_task_id)
                fuseki_task.dataset = ds
                fuseki_task.save()
                started_fuseki += 1
            except Exception as e:
                failed += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des Fuseki-Load-Tasks für '{slug}': {e}"
                )
                # Wenn Fuseki schon scheitert, SOLR lieber überspringen:
                continue

            # 2. SOLR-Load starten
            try:
                solr_task_id = run_management_command(
                    task_name=f"solr_load_dataset:{slug}",
                    command="solr_load_dataset",
                    args=[slug],
                )
                solr_task = ThreadTask.objects.get(pk=solr_task_id)
                solr_task.dataset = ds
                solr_task.save()
                started_solr += 1
            except Exception as e:
                failed += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des SOLR-Load-Tasks für '{slug}': {e}"
                )
                # ggf. Flag zurücksetzen, wenn du magst
                ds.indexed = False
                ds.save()

        self.message_user(
            request,
            f"{started_fuseki} Fuseki- und {started_solr} SOLR-Task(s) gestartet; "
            f"{failed} Fehlversuch(e).",
            level=messages.INFO,
        )
    load_fuseki_and_solr_async.short_description = ("Load into Fuseki & SOLR")

    @admin.action(description="Unload selected datasets from Fuseki & SOLR (async)")
    def unload_fuseki_and_solr_async(self, request, queryset):
        started_fuseki = 0
        started_solr = 0
        failed = 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            # 1. Fuseki-Unload starten
            try:
                fuseki_task_id = run_management_command(
                    task_name=f"fuseki_unload:{slug}",
                    command="fuseki_loader",
                    args=["unload", slug],
                )
                fuseki_task = ThreadTask.objects.get(pk=fuseki_task_id)
                fuseki_task.dataset = ds
                fuseki_task.save()
                started_fuseki += 1
            except Exception as e:
                failed += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des Fuseki-Unload-Tasks für '{slug}': {e}"
                )
                # Wenn Fuseki schon scheitert, SOLR lieber überspringen
                continue

            # 2. SOLR-Unload starten (solr_delete_dataset)
            try:
                solr_task_id = run_management_command(
                    task_name=f"solr_delete_dataset:{slug}",
                    command="solr_delete_dataset",
                    args=[slug],
                )
                solr_task = ThreadTask.objects.get(pk=solr_task_id)
                solr_task.dataset = ds
                solr_task.save()
                started_solr += 1
            except Exception as e:
                failed += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des SOLR-Unload-Tasks für '{slug}': {e}"
                )

        self.message_user(
            request,
            f"{started_fuseki} Fuseki- und {started_solr} SOLR-Unload-Task(s) gestartet; "
            f"{failed} Fehlversuch(e).",
            level=messages.INFO,
        )

    unload_fuseki_and_solr_async.short_description = ("Unload from Fuseki & SOLR")

    @admin.action(description="Delete the dataset completely (Fuseki, Solr, Django)")
    def delete_ds(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            slug = ds.name

            try:
                task_id = run_management_command(
                    task_name=f"delete_dataset:{slug}",
                    command="delete_dataset",
                    args=[slug],
                )

                task = ThreadTask.objects.get(pk=task_id)
                task.dataset = ds
                task.save()

                started += 1
                messages.success(
                    request,
                    f"Lösch-Task für Dataset '{slug}' gestartet."
                )

            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Fehler beim Starten des Delete-Tasks für {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} Lösch-Task(s) gestartet; {fail} fehlgeschlagen."
        )

    delete_ds.short_description = 'Delete the dataset'

    def _single_queryset(self, obj):
        # Hilfsfunktion, damit wir deine bestehenden Actions wiederverwenden können
        return models.Dataset.objects.filter(pk=obj.pk)

    def response_change(self, request, obj):
        """
        Reagiere auf Extra-Buttons im Change-Form (Detailansicht) und
        führe die bestehenden Actions nur für dieses eine Objekt aus.
        """
        # Name der Buttons muss zu den "name"-Attributen im Template passen
        if "_regenerate_and_load" in request.POST:
            self.regenerate_and_load_async(request, self._single_queryset(obj))
            return HttpResponseRedirect(".")  # auf der Detailseite bleiben

        if "_load_fuseki" in request.POST:
            self.load_fuseki(request, self._single_queryset(obj))
            return HttpResponseRedirect(".")

        if "_unload_fuseki" in request.POST:
            self.unload_fuseki(request, self._single_queryset(obj))
            return HttpResponseRedirect(".")

        if "_load_solr" in request.POST:
            self.load_into_solr(request, self._single_queryset(obj))
            return HttpResponseRedirect(".")

        if "_unload_solr" in request.POST:
            self.unload_from_solr(request, self._single_queryset(obj))
            return HttpResponseRedirect(".")

        if "_delete_ds" in request.POST:
            self.delete_ds(request, self._single_queryset(obj))
            # Nach Delete lieber zurück zur Liste:
            return HttpResponseRedirect("../")

        # Standardverhalten für alle anderen Buttons (Speichern usw.)
        return super().response_change(request, obj)

    change_list_template = 'admin/data/dataset/change_list.html'
    change_form_template = 'admin/data/dataset/change_form.html'


admin.site.register(models.Dataset, DatasetAdmin)


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


admin.register(models.ThreadTask, ThreadTaskAdmin)

# ... alles oben (DatasetAdmin, ThreadTaskAdmin etc.) bleibt wie bisher ...


# Alias, damit in data/views.py `admin.admin_site.site_header` funktioniert
admin_site = admin.site


def _extra_admin_urls():
    """
    Zusätzliche Admin-URLs aus der data-App.
    Pfade sind relativ zu /admin/.
    """
    return [
        path(
            "load_from_github/",
            admin.site.admin_view(views.load_from_github),
            name="load_from_github",
        ),
        path(
            "load_solr/",
            admin.site.admin_view(views.load_solr),
            name="load_solr",
        ),
        path(
            "load_fuseki/",
            admin.site.admin_view(views.load_fuseki),
            name="load_fuseki",
        ),
        path(
            "loader/<str:action>/",
            admin.site.admin_view(views.loader_manage_all),
            name="loader_manage_all",
        ),
        path(
            "backend/dashboard/",
            admin.site.admin_view(views.dashboard),
            name="dashboard",
        ),
        path(
            "backend/serverstatus/",
            admin.site.admin_view(views.serverstatus),
            name="serverstatus",
        ),
        path(
            "backend/commands/",
            admin.site.admin_view(views.django_commands),
            name="commands",
        ),
        path(
            "backend/run_command/<str:command>/",
            admin.site.admin_view(views.run_django_command),
            name="run_command",
        ),
    ]


def _wrap_admin_urls(original_get_urls):
    """
    Hängt unsere zusätzlichen URLs an das Standard-Admin an.
    """

    def get_urls():
        return _extra_admin_urls() + original_get_urls()

    return get_urls


# Hier wird das Django-Admin „gepatched“:
admin.site.get_urls = _wrap_admin_urls(admin.site.get_urls)
