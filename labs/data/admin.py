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
    can_delete = False
    show_change_link = False
    readonly_fields = ("url", "description", "indexed", "loaded")
    max_num = 0

    fields = ("url", "description", "indexed", "loaded")
    readonly_fields = ("indexed", "loaded",)
    can_delete = False


class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'category', 'graph', 'loaded', 'indexed', 'generation_status_short']
    list_display_links = ['name']

    formfield_overrides = formfield_overrides
    inlines = [DatafileAdmin, ]
    actions = ['regenerate_and_load_async', 'load_fuseki_and_solr_async', 'load_fuseki', 'unload_fuseki',
               'load_into_solr',
               'unload_from_solr', 'unload_fuseki_and_solr_async', 'delete_ds']
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

    # Short status for the list view
    @admin.display(description="Status")
    def generation_status_short(self, obj):
        status, _ = self._get_status_and_error(obj)
        # nur ein Wort + Symbol
        if status.startswith("OK"):
            return "✅"
        if status.startswith("running"):
            return "⏳"
        if status.startswith("Failed"):
            return "❌"
        return status

    # Detailed status for the detail view
    @admin.display(description="Status of generation")
    def generation_status(self, obj):
        status, error = self._get_status_and_error(obj)

        if status.startswith("OK"):
            # green checkmark and timestamp
            return mark_safe(f"<span style='color:green;'>✅ {status}</span>")

        if status.startswith("Failed"):
            # red cross and error message (shortened)
            short_err = error or "(siehe Log unten)"
            return mark_safe(
                f"<span style='color:red;'>❌ {status}<br><small>{short_err}</small></span>"
            )

        # running or unknown
        return status

    def _get_status_and_error(self, obj):
        task = obj.thread_tasks.order_by("-started").first()
        slug = obj.dataslug or obj.name

        # no task → only evaluate Generator Log
        if not task:
            gen_status, gen_line = self._detect_generator_result(slug)
            if gen_status == "SUCCESS":
                return "OK (Generator successful, no task)", None
            if gen_status == "ERROR":
                return "Failed (Generator)", gen_line
            return "no task/no log", None

        # Task still running
        if not task.is_done:
            return f"running since {task.started}", None

        # Task done → combine with Generator-Result
        gen_status, gen_line = self._detect_generator_result(slug)

        if task.status_ok and gen_status == "SUCCESS":
            return f"OK (done {task.ended})", None

        if gen_status == "ERROR":
            return f"Failed (done {task.ended})", gen_line

        if not task.status_ok:
            # Fallback: use Task Log as error message
            return f"Failed (done {task.ended})", task.last_log()

        # otherwise, all OK
        return f"OK (done {task.ended})", None

    def _detect_generator_result(self, slug: str):
        """
        Reads logs/<slug>.log and returns ('SUCCESS'|'ERROR'|'UNKNOWN', last relevant line) back.
        """
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
            # typical error markers
            if "failed" in lower or "error" in lower:
                last_error = line
                break
            # typical success markers
            if "generation finished" in lower or "generation finished" in lower or "copied →" in line:
                last_success = line
                break

        if last_error:
            return "ERROR", last_error
        if last_success:
            return "SUCCESS", last_success
        return "UNKNOWN", None

    # -------- Log from logs/<slug>.log (only tail) --------
    @admin.display(description="Generator Log")
    def generator_log(self, obj):
        slug = obj.dataslug or obj.name
        log_dir = getattr(settings, "GENERATOR_LOG_DIR", None)
        if not log_dir:
            return "GENERATOR_LOG_DIR is not configured."

        path = Path(log_dir) / f"{slug}.log"
        if not path.exists():
            return f"No log found ({path})"

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Error reading from {path}: {e}"

        lines = text.splitlines()
        tail_lines = 100  # Number of lines to show
        tail = "\n".join(lines[-tail_lines:])

        html = (
            "<details>"
            "<summary>Show Log (last "
            f"{min(tail_lines, len(lines))} lines)</summary>"
            "<pre style='max-height:400px; overflow:auto;'>"
            f"{tail}"
            "</pre></details>"
        )
        return mark_safe(html)

    @admin.display(description="Last Task Log")
    def task_log(self, obj):
        """
        Displays the log of the last ThreadTask associated with the dataset.
        Only the last 200 lines, in a <details> block.
        """
        task = obj.thread_tasks.order_by("-started").first()
        if not task:
            return "No Task Log available."

        text = task.log_text or ""
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            return "Log is empty."

        tail_lines = 200
        tail = "\n".join(lines[-tail_lines:])

        html = (
            "<details>"
            "<summary>Show Task Log (last "
            f"{min(tail_lines, len(lines))} lines)</summary>"
            "<pre style='max-height:400px; overflow:auto;'>"
            f"{escape(tail)}"
            "</pre></details>"
        )
        return mark_safe(html)

    # -------- Async-Action: regenerate & load --------
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
                    f"Dataset '{slug}' is already being generated – skipping new start.",
                    level=messages.WARNING,
                )
                continue

            # Start new task
            task_id = run_management_command(
                task_name=f"generate_dataset:{slug}",
                command="generate_and_load_dataset",
                args=[slug],
            )

            # Combine Task with Dataset for logging/status
            task = ThreadTask.objects.get(pk=task_id)
            task.dataset = obj
            task.save()

            started += 1

        if started:
            self.message_user(
                request,
                f"{started} Dataset(s) generation/loading started.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} Dataset(s) skipped (already running).",
                level=messages.INFO,
            )

    regenerate_and_load_async.short_description = (
        "Generate dataset (incl. metadata) and load in Fuseki (asynchron)"
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
            # Fuseki uses the Dataset-Name
            slug = ds.name

            try:
                task_id = run_management_command(
                    task_name=f"fuseki_load:{slug}",
                    command="fuseki_loader",
                    args=["load", slug],
                )

                # Link the task to the dataset so that task_log/generation_status work.
                task = ThreadTask.objects.get(pk=task_id)
                task.dataset = ds
                task.save()

                started += 1
                messages.success(
                    request,
                    f"Fuseki load task started for dataset '{slug}'."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Error starting Fuseki load task for {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} Fuseki load task started; {fail} failed.",
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
                    f"Fuseki unload task started for dataset '{slug}'."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Error starting the Fuseki unload task for {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} Fuseki unload task(s) started; {fail} failed.",
        )

    unload_fuseki.short_description = 'Unload from Fuseki'

    @admin.action(description="Load datasets into SOLR")
    def load_into_solr(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            try:
                # Start new ThreadTask
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
                    f"SOLR load task started for dataset '{slug}'."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Error starting the SOLR load tasks for {slug}: {e}"
                )
                ds.indexed = False
                ds.save()

        self.message_user(
            request,
            f"{started} SOLR load task(s) started; {fail} failed.",
        )

    load_into_solr.short_description = "Load selected datasets into SOLR"

    @admin.action(description="Unload selected datasets from SOLR")
    def unload_from_solr(self, request, queryset):
        started, fail = 0, 0

        for ds in queryset:
            # We also use the dataset name here; the command
            # translates it internally into the actual dataslug (see above).
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
                    f"SOLR unload task for dataset '{slug}' started."
                )
            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Error starting the SOLR unload tasks for {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} SOLR unload task(s) started; {fail} failed.",
        )

    unload_from_solr.short_description = "Unload selected datasets from SOLR"

    @admin.action(description="Load selected datasets into Fuseki & SOLR (async)")
    def load_fuseki_and_solr_async(self, request, queryset):
        started_fuseki = 0
        started_solr = 0
        failed = 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            # 1. Start Fuseki load
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
                    f"Error starting Fuseki load task for '{slug}': {e}"
                )
                # If Fuseki fails, better skip SOLR
                continue

            # 2. Start SOLR load
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
                    f"FError starting SOLR load task for '{slug}': {e}"
                )
                # reset indexed flag
                ds.indexed = False
                ds.save()

        self.message_user(
            request,
            f"{started_fuseki} Fuseki and {started_solr} SOLR task(s) started; "
            f"{failed} fail(s).",
            level=messages.INFO,
        )

    load_fuseki_and_solr_async.short_description = "Load into Fuseki & SOLR"

    @admin.action(description="Unload selected datasets from Fuseki & SOLR (async)")
    def unload_fuseki_and_solr_async(self, request, queryset):
        started_fuseki = 0
        started_solr = 0
        failed = 0

        for ds in queryset:
            slug = ds.dataslug or ds.name

            # 1. Start Fuseki unload
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
                    f"Error starting the Fuseki unload tasks for '{slug}': {e}"
                )
                # If Fuseki fails, better skip SOLR
                continue

            # 2. Start SOLR-Unload
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
                    f"Error staring ther SOLR unload tasks for '{slug}': {e}"
                )

        self.message_user(
            request,
            f"{started_fuseki} Fuseki and {started_solr} SOLR unload task(s) started; "
            f"{failed} fail(s).",
            level=messages.INFO,
        )

    unload_fuseki_and_solr_async.short_description = ("Unload from Fuseki & SOLR")

    @admin.action(description="Delete the dataset completely (Fuseki, SOLR, Database)")
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
                    f"Delete task started for dataset '{slug}'."
                )

            except Exception as e:
                fail += 1
                messages.error(
                    request,
                    f"Error starting delete tasks for {slug}: {e}"
                )

        self.message_user(
            request,
            f"{started} Delete task(s) started; {fail} failed."
        )

    delete_ds.short_description = 'Delete the dataset'

    def _single_queryset(self, obj):
        # Helper functions to reuse existing action methods for a single object
        return models.Dataset.objects.filter(pk=obj.pk)

    def response_change(self, request, obj):
        """
        Respond to extra buttons in the Change form (detail view) and
        execute the existing actions only for this one object.
        """
        # Name der Buttons muss zu den "name"-Attributen im Template passen
        if "_regenerate_and_load" in request.POST:
            self.regenerate_and_load_async(request, self._single_queryset(obj))
            return HttpResponseRedirect(".")  # stay on detail page

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
            # Redirect to the dataset list after deletion
            return HttpResponseRedirect("../")

        # Standard response for other cases
        return super().response_change(request, obj)

    change_list_template = 'admin/data/dataset/change_list.html'
    change_form_template = 'admin/data/dataset/change_form.html'


admin.site.register(models.Dataset, DatasetAdmin)


@admin.register(models.ThreadTask)
class ThreadTaskAdmin(admin.ModelAdmin):
    """
    Admin View for all tasks (ThreadTask), unrelated to the dataset.
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

    @admin.display(description="Last log line")
    def short_last_line(self, obj):
        last = obj.last_log()
        if not last:
            return "—"
        last = last.strip()
        if len(last) > 120:
            return last[:117] + "…"
        return last

    @admin.display(description="Task Log (tail)")
    def log_pretty(self, obj):
        text = obj.log_text or ""
        text = text.strip()
        if not text:
            return "No log entries."

        lines = [l for l in text.splitlines() if l.strip()]
        tail_lines = 200
        tail = "\n".join(lines[-tail_lines:])

        html = (
            "<details open>"
            "<summary>Show last "
            f"{min(tail_lines, len(lines))} lines</summary>"
            "<pre style='max-height: 500px; overflow: auto;'>"
            f"{escape(tail)}"
            "</pre></details>"
        )
        return mark_safe(html)


admin.register(models.ThreadTask, ThreadTaskAdmin)

# Alias so that `admin.admin_site.site_header` works in data/views.py
admin_site = admin.site


def _extra_admin_urls():
    """
    Additional admin URLs from the data app.
    Paths are relative to /admin/.
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
    Append additional URLs to the default admin.
    """

    def get_urls():
        return _extra_admin_urls() + original_get_urls()

    return get_urls


# Patch the Django admin:
admin.site.get_urls = _wrap_admin_urls(admin.site.get_urls)
