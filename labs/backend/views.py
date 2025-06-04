import json
import shutil
from datetime import datetime
from pathlib import Path

import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse

from . import admin
from . import tasks


# Create your views here.


def load_from_github(request):
    """
    Loads all Markdown files from the judaicalink-site Github repository.
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
    Fetches all data files and loads them in Fuseki.
    """
    tasks.call_command_as_task("load_all_datasets")
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
                    "{:.2f} / {:.2f} G".format(df.free / 2**30, df.total / 2**30),
                )
            )
            context["solr"].append(
                (
                    "Disk used (" + settings.SOLR_STORAGE + ")",
                    "{:.2f} M".format(dirsize(settings.SOLR_STORAGE) / 2**20),
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
                    "{:.2f} / {:.2f} G".format(df.free / 2**30, df.total / 2**30),
                )
            )
            context["fuseki"].append(
                (
                    "Disk used (" + settings.FUSEKI_STORAGE + ")",
                    "{:.2f} M".format(dirsize(settings.FUSEKI_STORAGE) / 2**20),
                )
            )
    except Exception as e:
        print(str(e))
    return render(request, "admin/serverstatus.html", context)


def django_commands(request):
    """Render a list of available dataset commands on an admin page."""
    from django.core import management

    all_cmds = management.get_commands()
    cmds = []
    for cmd, app in all_cmds.items():
        if app == "data":
            cmd_class = management.load_command_class("data", cmd)
            cmds.append({"name": cmd, "help": getattr(cmd_class, "help", "")})

    context = {
        "site_header": admin.admin_site.site_header,
        "cmds": cmds,
    }
    return render(request, "admin/commands.html", context)
