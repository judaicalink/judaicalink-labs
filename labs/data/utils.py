import os
import re
import requests
from django.conf import settings
from django.utils.http import http_date
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Tuple

FRONT_TOML_RE = re.compile(r"(?s)^\s*\+\+\+\s*(.*?)\s*\+\+\+\s*(.*)$")  # TOML + Body


def url_2_filename(url):
    url = url.replace(':', '_').replace('/', '_').replace('__', '_').replace('__', '_')
    return url


def get_filename(url):
    return 'data/rdf_files/' + url_2_filename(url)


def load_rdf_file(url):
    headers = {}
    filename = get_filename(url)
    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        headers['If-Modified-Since'] = http_date(int(mtime))
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            Path("data/rdf_files").mkdir(parents=True, exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(res.content)
    except:
        print("Connection error: " + url)
    return filename


def content_root() -> Path:
    return Path(getattr(settings, "JUDAICALINK_DATASETS_CATALOG_DIR"))


@lru_cache(maxsize=1_000)
def read_markdown_with_frontmatter(slug: str) -> Tuple[Dict[str, Any], str, Path]:
    """
    Liefert (meta, body, path). meta kommt aus TOML-Frontmatter, body ist Markdown (ohne Frontmatter).
    Erlaubt slug.md oder <slug>/index.md
    """
    import toml

    # Kandidaten wie bei Hugo
    root = content_root()
    candidates = [
        root / f"{slug}.md",
        root / slug / "index.md",
        root / slug / f"{slug}.md",
    ]
    md_path = next((p for p in candidates if p.exists()), None)
    if not md_path:
        raise FileNotFoundError(f"Dataset markdown not found for slug '{slug}' in {root}")

    text = md_path.read_text(encoding="utf-8")
    m = FRONT_TOML_RE.match(text)
    if not m:
        return {}, text, md_path

    toml_block, body = m.group(1), m.group(2)
    try:
        meta = toml.loads(toml_block) or {}
    except Exception:
        meta = {}
    # slug aus Dateiname ableiten, wenn nicht gesetzt
    meta.setdefault("slug", slug)
    return meta, body, md_path


def list_dataset_slugs() -> list[str]:
    """
    Sucht alle .md Dateien im content_dir (Hugo-Struktur).
    """
    root = content_root()
    slugs = set()

    for p in root.glob("*.md"):
        slugs.add(p.stem)

    for d in root.iterdir():
        if d.is_dir():
            if (d / "index.md").exists():
                slugs.add(d.name)
            elif (d / f"{d.name}.md").exists():
                slugs.add(d.name)

    return sorted(slugs)


def clear_cache():
    read_markdown_with_frontmatter.cache_clear()
