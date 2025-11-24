import json
import markdown as md
import os
import requests
import shutil
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from pathlib import Path

from . import admin
from . import tasks
from .models import Generator, Dataset, ThreadTask, Datafile
from .utils import list_dataset_slugs, read_markdown_with_frontmatter

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


@cache_page(CACHE_TTL)
def commands(request):
    all_cmds = management.get_commands()
    cmds = []
    for cmd, app in all_cmds.items():
        if app == 'data':
            cmd_class = management.load_command_class("data", cmd)
            cmd_class.name = cmd
            cmds.append(cmd_class)

    return render(request, 'data/commands.html', {"cmds": cmds})


def load_status_for_slug(slug: str) -> dict:
    """
    Retrieves the last run and status flags (generated/loaded) from the generator model.
    """
    try:
        g = Generator.objects.get(slug=slug)
    except Generator.DoesNotExist:
        return {"generated": False, "loaded": False, "status": "missing"}
    r = g.runs.first()
    if not r:
        return {"generated": False, "loaded": False, "status": "never"}
    generated = (r.status == "SUCCESS")
    loaded = (r.status == "SUCCESS")
    return {
        "generated": generated,
        "loaded": loaded,
        "status": f"{r.status}",
    }


def _collect_dumps_for_dataset(dataslug: str):
    """
   Collects dumps from JUDAICALINK_DUMPS_DIR/<dataslug>/...
    - always current first
    - then other subfolders according to mtime (descending)
    Returns (online_bool, dumps_groups).
    """
    dumps_root = Path(getattr(settings, "LABS_DUMPS_LOCAL", "/data/dumps"))
    base_url = getattr(settings, "LABS_DUMPS_WEBROOT",
                       "https://data.judaicalink.org/dumps/").rstrip("/")

    ds_dir = dumps_root / dataslug
    dumps_groups = []
    if not ds_dir.exists():
        return False, []

    subdirs = [d for d in ds_dir.iterdir() if d.is_dir()]

    current_dirs = [d for d in subdirs if d.name == "current"]
    other_dirs = [d for d in subdirs if d.name != "current"]
    other_dirs_sorted = sorted(other_dirs, key=lambda d: d.stat().st_mtime, reverse=True)
    ordered = current_dirs + other_dirs_sorted

    any_files = False

    for d in ordered:
        files = []
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            rel = f.relative_to(dumps_root)
            url = base_url + "/" + "/".join(rel.parts)
            name = f.name
            is_rdf = name.endswith((".ttl", ".ttl.gz", ".nt", ".nt.gz", ".n3", ".n3.gz"))
            files.append({
                "name": name,
                "url": url,
                "is_rdf": is_rdf,
            })
        if files:
            any_files = True
        dumps_groups.append({
            "dir": d.name,
            "is_current": (d.name == "current"),
            "files": files,
        })

    # Online heuristic: if Dataset.loaded is true and there is any dump
    ds = Dataset.objects.filter(dataslug=dataslug).first()
    online = False
    if ds and ds.loaded and any_files:
        online = True
    elif any_files and not ds:
        # Fallback: old/archived dumps
        online = True

    return online, dumps_groups


class DatasetListView(TemplateView):
    template_name = "data/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slugs = list_dataset_slugs()

        rows = []
        support_rows = []
        for slug in slugs:
            meta, body_md, _ = read_markdown_with_frontmatter(slug)
            title = meta.get("title") or slug
            # Markdown → HTML (only Body!)
            body_html = md.markdown(
                body_md,
                extensions=["extra", "toc", "sane_lists", "smarty"]
            )
            summary = body_html.split("<!--more-->")[0]

            if meta.get('category') == "support":
                support_rows.append({
                    "slug": slug,
                    "title": title,
                    "summary": mark_safe(summary),
                    "date": str(meta.get("date")),
                })
            else:
                rows.append({
                    "slug": slug,
                    "title": title,
                    "summary": mark_safe(summary),
                    "date": str(meta.get("date")),
                })

        rows = sorted(rows, key=lambda r: r["date"], reverse=True)
        support_rows = sorted(support_rows, key=lambda r: r["date"], reverse=True)

        ctx["datasets"] = rows
        ctx['support'] = support_rows
        return ctx


class DatasetDetailView(TemplateView):
    template_name = "data/detail.html"

    def get_context_data(self, slug: str, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            meta, body_md, md_path = read_markdown_with_frontmatter(slug)

            def _is_rdf_url(url: str) -> bool:
                url_l = url.lower()
                return any(
                    url_l.endswith(ext)
                    for ext in [".ttl", ".ttl.gz", ".nt", ".nt.gz", ".n3", ".n3.gz"]
                )

            # Bring files from Frontmatter into a simple structure
            raw_files = meta.get("files", [])
            files = []
            for f in raw_files:
                # f is a TOML-dict with "url" and "description"
                url = f.get("url") if isinstance(f, dict) else f
                if not url:
                    continue
                desc = f.get("description", "") if isinstance(f, dict) else ""
                filename = url.rstrip("/").split("/")[-1]
                files.append(
                    {
                        "url": url,
                        "description": desc,
                        "filename": filename,
                        "is_rdf": _is_rdf_url(url),
                    }
                )

        except FileNotFoundError:
            raise Http404("Dataset not found")

        # Markdown → HTML (only body!)
        body_html = md.markdown(
            body_md,
            extensions=["extra", "toc", "sane_lists", "smarty"]
        )

        # Slug for URIs: dataslug from frontmatter or fallback slug
        dataslug = meta.get("dataslug") or slug

        # Status from Generator/Run
        status = load_status_for_slug(slug)

        # Determine Dumps & „online“
        online, dumps_groups = _collect_dumps_for_dataset(dataslug)
        status["loaded"] = online  # overrides loaded status

        ctx.update({
            "slug": slug,
            "dataslug": dataslug,
            "meta": meta,
            "body_html": mark_safe(body_html),
            "md_path": md_path,
            "status": status,
            "content_dir": settings.JUDAICALINK_DATASETS_CATALOG_DIR,
            "online": online,
            "dumps_groups": dumps_groups,
            "files": files,
        })

        return ctx


def load_from_github(request):
    """
    Loads all Markdown files from the JudaicaLink-site Github repository.
    Saves files in data/gh_datasets.
    """
    tasks.call_command_as_task("sync_datasets")
    return redirect(reverse("admin:data_dataset_changelist"))


def load_solr(request):
    """
    Fetches all data files and indexes them in Solr.
    """
    tasks.call_command_as_task("index_all_datasets")
    return redirect(reverse("admin:data_dataset_changelist"))


def load_fuseki(request):
    """
    Load all datasets in Fuseki using the loader script.
    """
    tasks.call_command_as_task("fuseki_loader", "load")
    return redirect(reverse("admin:data_dataset_changelist"))


def loader_manage_all(request, action):
    """
    Run the loader script with the given action for all datasets.
    """
    tasks.call_command_as_task("fuseki_loader", action)
    return redirect(reverse("admin:data_dataset_changelist"))


def dirsize(directory):
    root_directory = Path(directory)
    return sum(f.stat().st_size for f in root_directory.glob("**/*") if f.is_file())


def serverstatus(request):
    context = {
        "site_header": admin.admin_site.site_header,
        "solr": [("Status", "offline")],
        "fuseki": [("Status", "offline")],
    }
    try:
        solr_main = json.loads(requests.get(settings.SOLR_SERVER).content.decode("utf-8"))
        solr_stats = json.loads(requests.get(settings.SOLR_SERVER).content.decode("utf-8"))
        context["solr"] = [
            ("Version", solr_main["lucene"]["solr-spec-version"]),
            ("Name", solr_main["solr_home"]),
            ("Uptime", solr_stats["uptime"]),
            ("Cores", "\n".join(solr_stats["status"].keys())),
        ]

        for core in solr_stats["status"]:
            context["solr"].append(
                (core + " Docs", "{:,}".format(solr_stats["status"][core]["index"]["numDocs"]))
            )
            context["solr"].append(
                (
                    core + " Size",
                    "{:.2f} M".format(
                        solr_stats["status"][core]["index"]["sizeInBytes"] / 1024 / 1024
                    ),
                )
            )
        if hasattr(settings, "SOLR_STORAGE"):
            df = shutil.disk_usage(settings.SOLR_STORAGE)
            context["solr"].append(
                (
                    "Disk space (" + settings.SOLR_STORAGE + ")",
                    "{:.2f} / {:.2f} G".format(df.free / 2 ** 30, df.total / 2 ** 30),
                )
            )
            context["solr"].append(
                (
                    "Disk used (" + settings.SOLR_STORAGE + ")",
                    "{:.2f} M".format(dirsize(settings.SOLR_STORAGE) / 2 ** 20),
                )
            )
    except Exception as e:
        print(str(e))

    try:
        f_main = json.loads(
            requests.get(settings.FUSEKI_SERVER + "$/server").content.decode("utf-8")
        )

        context["fuseki"] = [
            ("Version", f_main["version"]),
            (
                "Started",
                datetime.fromisoformat(f_main["startDateTime"]).strftime("%Y-%m-%d %H:%M"),
            ),
            ("Datasets", "\n".join([ds["ds.name"] for ds in f_main["datasets"]])),
        ]
        if hasattr(settings, "FUSEKI_STORAGE"):
            df = shutil.disk_usage(settings.FUSEKI_STORAGE)
            context["fuseki"].append(
                (
                    "Disk space (" + settings.FUSEKI_STORAGE + ")",
                    "{:.2f} / {:.2f} G".format(df.free / 2 ** 30, df.total / 2 ** 30),
                )
            )
            context["fuseki"].append(
                (
                    "Disk used (" + settings.FUSEKI_STORAGE + ")",
                    "{:.2f} M".format(dirsize(settings.FUSEKI_STORAGE) / 2 ** 20),
                )
            )
    except Exception as e:
        print(str(e))
    return render(request, "admin/serverstatus.html", context)


def django_commands(request):
    """
    Render a list of available dataset commands on an admin page.
    """
    from django.core import management

    all_cmds = management.get_commands()
    cmds = []
    for cmd, app in all_cmds.items():
        if app == "data":
            cmd_class = management.load_command_class("data", cmd)
            cmds.append({"name": cmd, "help": getattr(cmd_class, "help", "")})

    tasks = ThreadTask.objects.all().order_by("-started")[:20]

    context = {
        "site_header": admin.admin_site.site_header,
        "cmds": cmds,
        "tasks": tasks,
    }
    return render(request, "admin/commands.html", context)


def run_django_command(request, command):
    """
    Run a management command asynchronously and redirect back.
    """
    tasks.call_command_as_task(command)
    return redirect(reverse("admin:commands"))


def dashboard(request):
    """
    Render statistics, metrics and logs on an admin dashboard page.
    """
    stats = {
        "datasets": Dataset.objects.count(),
        "files": Datafile.objects.count(),
        "users": get_user_model().objects.count(),
    }
    metrics = {}
    try:
        with open(os.path.join(settings.BASE_DIR, "statistics.json")) as f:
            metrics = json.load(f)
    except Exception as e:
        print(str(e))

    logs = ThreadTask.objects.all().order_by("-started")[:10]

    context = {
        "site_header": admin.admin_site.site_header,
        "stats": stats,
        "metrics": metrics,
        "logs": logs,
    }

    return render(request, "admin/dashboard.html", context)
