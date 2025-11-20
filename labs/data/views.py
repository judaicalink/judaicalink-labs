from pathlib import Path

from datetime import datetime

import markdown as md
from django.conf import settings
from django.core import management
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.http import Http404
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from .models import Generator, Dataset
from .utils import list_dataset_slugs, read_markdown_with_frontmatter

# Create your views here.
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
    Holt den letzten Run & Status-Fahnen (generated/loaded) aus dem Generator-Modell.
    (Kann später mit dem neuen Dataset-Management zusammengeführt werden.)
    """
    try:
        g = Generator.objects.get(slug=slug)
    except Generator.DoesNotExist:
        return {"generated": False, "loaded": False, "status": "missing"}
    r = g.runs.first()
    if not r:
        return {"generated": False, "loaded": False, "status": "never"}
    generated = (r.status == "SUCCESS")
    loaded = (r.status == "SUCCESS")  # wird gleich durch "online" überschrieben
    return {
        "generated": generated,
        "loaded": loaded,
        "status": f"{r.status}",
    }


def _collect_dumps_for_dataset(dataslug: str):
    """
    Sammelt Dumps aus JUDAICALINK_DUMPS_DIR/<dataslug>/...
    - current immer zuerst
    - danach andere Unterordner nach mtime (absteigend)
    Gibt (online_bool, dumps_groups) zurück.
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

    # Online-Heuristik: wenn Dataset.loaded True und es gibt irgendeinen Dump
    ds = Dataset.objects.filter(dataslug=dataslug).first()
    online = False
    if ds and ds.loaded and any_files:
        online = True
    elif any_files and not ds:
        # Fallback: alte/archivierte Dumps, aber noch kein neues Dataset-Objekt
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
            # Markdown → HTML (nur Body!)
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

            # Files aus Frontmatter in eine einfache Struktur bringen
            raw_files = meta.get("files", [])
            files = []
            for f in raw_files:
                # f ist in deinem TOML ein dict mit "url" und "description"
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

        # Markdown → HTML (nur Body!)
        body_html = md.markdown(
            body_md,
            extensions=["extra", "toc", "sane_lists", "smarty"]
        )

        # Slug für URIs: dataslug aus Frontmatter oder fallback slug
        dataslug = meta.get("dataslug") or slug

        # Status aus Generator/Run (wird unten bzgl. "loaded" angepasst)
        status = load_status_for_slug(slug)

        # Dumps & „online“ bestimmen
        online, dumps_groups = _collect_dumps_for_dataset(dataslug)
        status["loaded"] = online  # Überschreibt loaded: hier bedeutet „online“

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
            "files": files,  # <-- neu
        })

        return ctx