# labs/backend/management/commands/fuseki_loader.py
import os
import requests
import shutil
import subprocess
import sys
import gzip
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from urllib.parse import quote, urlparse
from ...models import Dataset

env = os.environ.copy()
env["HUGO_DIR"] = str(getattr(settings, "HUGO_DIR", ""))
env.setdefault("ENDPOINT", "http://localhost:3030/judaicalink")
env.setdefault("LABS_DUMPS_WEBROOT", "http://data.judaicalink.org/dumps/")
DUMPS_LOCAL_DIR = env.get("LABS_DUMPS_LOCAL", "/mnt/data/dumps")
GENERATORS_PATH = (
    getattr(settings, "JUDAICALINK_GENERATORS_PATH", None)
    or getattr(settings, "GENERATORS_BASE_DIR", None)
)


def resolve_datafile_path(df, dataslug: str, stdout=None) -> Path:
    """
    Versucht aus Datafile.url einen lokalen Pfad zu machen.

    Reihenfolge:
      1. Absoluter Pfad aus df.url
      2. Mapping von HTTP-URLs / relativen Pfaden nach DUMPS_LOCAL_DIR
      3. Fallback: GENERATORS_PATH/<slug>/output/<slug>.ttl(.gz)
      4. Fallback: roher Path(df.url)
    """
    raw = (df.url or "").strip()
    p = Path(raw)

    def log(msg: str):
        if stdout is not None:
            stdout.write(msg)

    # 1) Absoluter Pfad direkt
    if p.is_absolute():
        log(f"[PATH] Absoluter Pfad aus url: {p} (exists={p.exists()})")
        return p

    # 2) Basis-Dumps-Dir (nur wenn es existiert)
    base_dumps = None
    if DUMPS_LOCAL_DIR:
        base_path = Path(DUMPS_LOCAL_DIR)
        if base_path.exists():
            base_dumps = base_path
        else:
            log(f"[PATH] DUMPS_LOCAL_DIR existiert nicht: {base_path}")

    candidates = []

    # HTTP-URL → Pfad relativ zu /dumps/
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        rel = parsed.path.lstrip("/")
        if "dumps/" in rel:
            # z.B. "dumps/gba/current/gba-final-01.ttl.gz" → "gba/current/gba-final-01.ttl.gz"
            rel = rel.split("dumps/", 1)[1]
        if base_dumps:
            candidates.append(base_dumps / rel)
    else:
        # Nicht-HTTP → direkt unter base_dumps
        if base_dumps:
            candidates.append(base_dumps / raw)

    # 2b) Kandidaten aus Dumps prüfen
    for cand in candidates:
        log(f"[PATH] Prüfe Kandidat: {cand}")
        if cand.exists():
            log(f"[PATH] → Verwende Datei (Dumps): {cand}")
            return cand

    # 3) Fallback: Generators-Ordner /<slug>/output/<slug>.ttl(.gz)
    if GENERATORS_PATH:
        gen_base = Path(GENERATORS_PATH) / dataslug / "output"
        cand_gz = gen_base / f"{dataslug}.ttl.gz"
        cand_ttl = gen_base / f"{dataslug}.ttl"

        for cand in (cand_gz, cand_ttl):
            log(f"[PATH] Prüfe Generator-Kandidat: {cand}")
            if cand.exists():
                log(f"[PATH] → Verwende Datei (Generator): {cand}")
                return cand

    # 4) Fallback: roher Pfad (wird später noch einmal auf exists geprüft)
    log(f"[PATH] Kein Kandidat gefunden, nutze raw-Pfad: {p}")
    return p

def _iter_dataset_slugs():
    for ds in Dataset.objects.all().only('name', 'dataslug'):
        yield (ds.dataslug or ds.name)


def _set_loaded_flag(dataset_slug: str, value: bool):
    qs = Dataset.objects.filter(dataslug=dataset_slug)
    if not qs.exists():
        qs = Dataset.objects.filter(name=dataset_slug)
    for ds in qs:
        ds.set_loaded(value)

    # --- Metadaten-Handling -----------------------------------------------

    def _metadata_graph_uri(self, slug: str) -> str:
        """
        Liefert den Named-Graph für Metadaten dieses Datasets.
        Basis-URI kann über settings.JL_METADATA_GRAPH_BASE überschrieben werden.
        """
        base = getattr(settings, "JL_METADATA_GRAPH_BASE", "http://data.judaicalink.org/datasets")
        return f"{base.rstrip('/')}/{slug}.meta"

    def _find_meta_file(self, slug: str) -> Path | None:
        """
        Sucht nach <slug>.meta.ttl(.gz) im Generator-Output-Verzeichnis:

            GENERATORS_BASE_DIR/<slug>/output/<slug>.meta.ttl(.gz)
        """
        gen_base = getattr(settings, "GENERATORS_BASE_DIR", None)
        if not gen_base:
            return None

        base = Path(gen_base) / slug / "output"
        candidates = [
            base / f"{slug}.meta.ttl",
            base / f"{slug}.meta.ttl.gz",
        ]
        for cand in candidates:
            if cand.exists():
                self.stdout.write(f"[META] Metadaten-Datei gefunden: {cand}")
                return cand

        self.stdout.write(f"[META] Keine Metadaten-Datei für {slug} gefunden.")
        return None


class Command(BaseCommand):
    help = "Wrapper around the JudaicaLink Fuseki loader. Uses either a CLI 'judaicalink-loader' or a loader.py script."

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['load', 'unload', 'delete'])
        parser.add_argument('dataset', nargs='?', default='all',
                            help="Dataset acronym or 'all'")

    # --- resolution helpers -------------------------------------------------

    def _resolve_cli(self):
        """Return ['judaicalink-loader'] if an installed CLI exists."""
        cli = shutil.which('judaicalink-loader')
        return [cli] if cli else None

    def _resolve_loader_py(self):
        """
        Resolve a loader.py path from:
        1) Django setting JUDAICALINK_LOADER_PATH (file or directory)
        """
        # 1) Django setting
        path = getattr(settings, 'JUDAICALINK_LOADER_PATH', None)
        if path:
            p = Path(path)
            if p.is_file():
                return p
            if p.is_dir():
                cand = p / 'loader.py'
                if cand.is_file():
                    return cand
        # print("JUDAICALINK_LOADER_PATH: ", path)

        return path

    # --- Metadaten-Handling: EIN gemeinsamer Graph -------------------------

    def _metadata_graph_uri(self) -> str:
        """
        Gemeinsamer Metadaten-Graph für alle Datasets.

        Kann bei Bedarf in settings überschrieben werden:
        JL_METADATA_GRAPH_URI = "http://data.judaicalink.org/datasets"
        """
        return getattr(
            settings,
            "JL_METADATA_GRAPH_URI",
            "http://data.judaicalink.org/datasets",
        )

    def _dataset_graph_uri(self, ds, dataslug: str) -> str:
        """
        Graph-URI für das Dataset.

        Wenn im Dataset ein graph-Feld gesetzt ist, wird dieses benutzt.
        Sonst Fallback auf JL_DATA_GRAPH_BASE/dataslug.
        """
        graph = getattr(ds, "graph", None)
        if graph:
            graph = graph.strip()
        if graph:
            return graph

        base = getattr(settings, "JL_DATA_GRAPH_BASE", "http://data.judaicalink.org/data")
        return f"{base.rstrip('/')}/{dataslug}"

    def _fuseki_post_file(self, path: Path, graph_uri: str):
        """
        Schickt eine Datei (TTL/NT, optional .gz) an Fuseki in den angegebenen Graph.
        """
        endpoint = env.get("ENDPOINT", "http://localhost:3030/judaicalink").rstrip("/")
        url = f"{endpoint}/data?graph={quote(graph_uri, safe='')}"

        path_str = str(path)
        data = path.read_bytes()
        if path_str.endswith(".gz"):
            data = gzip.decompress(data)
            # Endung ohne .gz bestimmen
            inner = path_str[:-3]
        else:
            inner = path_str

        if inner.endswith(".ttl"):
            content_type = "text/turtle"
        elif inner.endswith(".nt") or inner.endswith(".ntriples"):
            content_type = "application/n-triples"
        else:
            # Fallback: versuche Turtle
            content_type = "text/turtle"

        self.stdout.write(f"[Fuseki] POST {url} ({content_type}), Datei: {path}")
        resp = requests.post(url, data=data, headers={"Content-Type": content_type})
        try:
            resp.raise_for_status()
        except Exception as e:
            raise CommandError(f"[Fuseki] Fehler beim POST von {path} in Graph <{graph_uri}>: {e}")

    def _load_dataset_from_datafiles(self, slug: str):
        """
        Lädt EIN Dataset in Fuseki, basierend auf allen zugehörigen Datafiles.
        Verwendet die gleiche Pfadlogik wie der SOLR-Loader.
        """
        self.stdout.write(self.style.NOTICE(f"[Fuseki] Lade Dataset '{slug}' über Datafiles …"))

        # Dataset finden (name oder dataslug)
        try:
            ds = Dataset.objects.get(name=slug)
        except Dataset.DoesNotExist:
            try:
                ds = Dataset.objects.get(dataslug=slug)
            except Dataset.DoesNotExist:
                raise CommandError(
                    f"Dataset '{slug}' existiert nicht (weder als name noch als dataslug)."
                )

        dataslug = ds.dataslug or ds.name
        graph_uri = self._dataset_graph_uri(ds, dataslug)

        datafiles = ds.datafile_set.all()
        if not datafiles:
            raise CommandError(f"Dataset '{slug}' hat keine Datafiles zum Laden.")

        loaded_files = 0
        missing_files = 0

        for df in datafiles:
            path = resolve_datafile_path(df, dataslug, stdout=self.stdout)

            if not path.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"[Fuseki] Datei fehlt: {path} (aus url={df.url})"
                    )
                )
                missing_files += 1
                continue

            self.stdout.write(f"[Fuseki] → Lade Datei: {path} in Graph <{graph_uri}>")
            self._fuseki_post_file(path, graph_uri)
            loaded_files += 1

        self.stdout.write(
            f"[Fuseki] Dateien mit gültigem Pfad: {loaded_files}, fehlende Dateien: {missing_files}"
        )

        if loaded_files == 0:
            ds.set_loaded(False)
            raise CommandError(
                f"Dataset '{slug}' konnte nicht geladen werden (0 Dateien erfolgreich)."
            )

        # Flag am Dataset & Datafiles setzen
        ds.set_loaded(True)
        self.stdout.write(
            self.style.SUCCESS(
                f"[Fuseki] Dataset '{slug}' erfolgreich in Graph <{graph_uri}> geladen "
                f"({loaded_files} Datei(en))."
            )
        )

        # Metadaten ebenfalls laden (ein gemeinsamer Meta-Graph, wie du ihn schon hast)
        try:
            self._load_metadata_graph(dataslug)
        except Exception as e:
            self.stderr.write(f"[META] Fehler beim Laden der Metadaten für '{dataslug}': {e}")


    def _find_meta_file(self, slug: str) -> Path | None:
        """
        Sucht nach <slug>.meta.ttl(.gz) im gleichen Verzeichnis wie die TTL-Files.

        Mögliche Orte:
        - DUMPS_LOCAL_DIR/<slug>/current/
        - JUDAICALINK_GENERATORS_PATH/<slug>/output/
        """
        candidates_dirs = []

        # 1) dumps-Verzeichnis (lokale Dumps)
        dumps_base = Path(env.get("DUMPS_LOCAL_DIR", "/mnt/data/dumps"))
        candidates_dirs.append(dumps_base / slug / "current")

        # 2) generators-Verzeichnis (neue Generatoren)
        gen_base = getattr(settings, "JUDAICALINK_GENERATORS_PATH", None) \
                   or getattr(settings, "GENERATORS_BASE_DIR", None)
        if gen_base:
            candidates_dirs.append(Path(gen_base) / slug / "output")

        # jetzt in allen Kandidaten-Verzeichnissen nach <slug>.meta.ttl(.gz) suchen
        for base_dir in candidates_dirs:
            for p in (
                    base_dir / f"{slug}.meta.ttl",
                    base_dir / f"{slug}.meta.ttl.gz",
            ):
                if p.exists():
                    self.stdout.write(f"[META] Metadaten-Datei gefunden: {p}")
                    return p

        self.stdout.write(f"[META] Keine Metadaten-Datei für {slug} gefunden.")
        return None

    def _load_metadata_graph(self, slug: str):
        """
        Lädt <slug>.meta.ttl(.gz) in den gemeinsamen Metadaten-Graphen.

        Wichtig:
        - Kein DROP des Graphen.
        - POST auf /data?graph=... -> Tripel werden ergänzt.
        - Vorher werden die alten Tripel für diesen slug anhand der Subjekte
          aus der Meta-Datei aus dem Graphen gelöscht (Update).
        """
        meta_path = self._find_meta_file(slug)
        if not meta_path:
            # keine Meta-Datei -> nichts zu tun
            return

        endpoint = env.get("ENDPOINT", "http://localhost:3030/judaicalink").rstrip("/")
        graph_uri = self._metadata_graph_uri()

        # Datei lesen (ggf. .gz dekomprimieren)
        data = meta_path.read_bytes()
        if str(meta_path).endswith(".gz"):
            data = gzip.decompress(data)

        # 1) Alte Metadaten für diesen slug anhand der Subjekte löschen
        #    (nur URI-Subjekte; Blank Nodes lassen wir in Ruhe)
        g = Graph()
        g.parse(data=data.decode("utf-8"), format="turtle")
        subjects = {s for s in g.subjects() if isinstance(s, URIRef)}

        if subjects:
            values = " ".join(f"<{str(s)}>" for s in subjects)
            sparql = f"""
DELETE {{
  GRAPH <{graph_uri}> {{
    ?s ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    VALUES ?s {{ {values} }}
    ?s ?p ?o .
  }}
}}
"""
            update_url = f"{endpoint}/update"
            self.stdout.write(f"[META] Lösche alte Metadaten für {slug} aus {graph_uri}")
            resp_del = requests.post(
                update_url,
                data={"update": sparql},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if not resp_del.ok:
                raise CommandError(
                    f"Metadaten-DELETE für {slug} fehlgeschlagen "
                    f"(Status {resp_del.status_code}): {resp_del.text[:500]}"
                )

        # 2) Neue Metadaten in den gemeinsamen Graphen POSTen (additiv)
        data_url = f"{endpoint}/data?graph={quote(graph_uri, safe='')}"
        self.stdout.write(f"[META] Lade Metadaten {meta_path} in Graph {graph_uri}")
        resp_post = requests.post(
            data_url,
            data=data,
            headers={"Content-Type": "text/turtle"},
        )
        if not resp_post.ok:
            raise CommandError(
                f"Metadaten-Upload für {slug} nach Fuseki fehlgeschlagen "
                f"(Status {resp_post.status_code}): {resp_post.text[:500]}"
            )

    def _delete_metadata_for_slug(self, slug: str):
        """
        Löscht Metadaten für einen slug aus dem gemeinsamen Metadaten-Graphen,
        ohne den Graphen selbst zu löschen.

        1. Wenn eine <slug>.meta.ttl(.gz) existiert:
           - Lösche alle Tripel mit URI-Subjekten aus dieser Datei.
           - Lösche zusätzlich die prov:used / build.py-BNode-Kette anhand
             des rdfs:label "<slug>/scripts/build.py".
        2. Wenn KEINE Meta-Datei existiert:
           - Fallback: lösche alle Tripel, deren Subjekt
             <http://data.judaicalink.org/datasets/{slug}> ist.
        """
        endpoint = env.get("ENDPOINT", "http://localhost:3030/judaicalink").rstrip("/")
        graph_uri = self._metadata_graph_uri()
        update_url = f"{endpoint}/update"

        # --- Versuch: Meta-Datei finden ------------------------------------
        meta_path = self._find_meta_file(slug)

        # --- Fallback, wenn keine Meta-Datei vorhanden ---------------------
        if not meta_path:
            subject = f"http://data.judaicalink.org/datasets/{slug}"
            sparql = f"""
DELETE {{
  GRAPH <{graph_uri}> {{
    <{subject}> ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    <{subject}> ?p ?o .
  }}
}}
"""
            self.stdout.write(
                f"[META] Keine Meta-Datei für {slug}; Fallback: "
                f"Lösche alle Tripel mit Subjekt <{subject}> aus Graph {graph_uri}"
            )
            resp = requests.post(
                update_url,
                data={"update": sparql},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if not resp.ok:
                raise CommandError(
                    f"Metadaten-Fallback-Löschung für {slug} fehlgeschlagen "
                    f"(Status {resp.status_code}): {resp.text[:500]}"
                )
            return

        # --- Normale Löschung basierend auf der Meta-Datei -----------------
        # Meta-Datei lesen (ggf. .gz dekomprimieren)
        data = meta_path.read_bytes()
        if str(meta_path).endswith(".gz"):
            data = gzip.decompress(data)

        g = Graph()
        g.parse(data=data.decode("utf-8"), format="turtle")

        # --- 1) URI-Subjekte löschen ----------------------------------------
        subjects = {s for s in g.subjects() if isinstance(s, URIRef)}

        if subjects:
            values = " ".join(f"<{str(s)}>" for s in subjects)
            sparql = f"""
DELETE {{
  GRAPH <{graph_uri}> {{
    ?s ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    VALUES ?s {{ {values} }}
    ?s ?p ?o .
  }}
}}
"""
            self.stdout.write(f"[META] Lösche URI-Subjekte für {slug} aus Graph {graph_uri}")
            resp = requests.post(
                update_url,
                data={"update": sparql},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if not resp.ok:
                raise CommandError(
                    f"Metadaten-Löschung (URI-Subjekte) für {slug} fehlgeschlagen "
                    f"(Status {resp.status_code}): {resp.text[:500]}"
                )

        # --- 2) Blank-Node-Kette für build.py löschen -----------------------
        prov_used = URIRef("http://www.w3.org/ns/prov#used")
        rdfs_label = URIRef("http://www.w3.org/2000/01/rdf-schema#label")

        build_labels: set[str] = set()
        for s, p, o in g.triples((None, rdfs_label, None)):
            if isinstance(o, Literal) and "/scripts/build.py" in str(o):
                build_labels.add(str(o))

        for label in build_labels:
            sparql_bnodes = f"""
DELETE {{
  GRAPH <{graph_uri}> {{
    ?activity ?p1 ?code .
    ?code ?p2 ?o2 .
  }}
}}
WHERE {{
  GRAPH <{graph_uri}> {{
    ?activity <{prov_used}> ?code .
    ?code <{rdfs_label}> "{label}" .
    ?activity ?p1 ?code .
    ?code ?p2 ?o2 .
  }}
}}
"""
            self.stdout.write(
                f"[META] Lösche prov:used/build.py-BNodes für {slug} "
                f"(Label '{label}') aus Graph {graph_uri}"
            )
            resp2 = requests.post(
                update_url,
                data={"update": sparql_bnodes},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if not resp2.ok:
                raise CommandError(
                    f"Metadaten-Löschung (build.py-BNodes) für {slug} fehlgeschlagen "
                    f"(Status {resp2.status_code}): {resp2.text[:500]}"
                )

    # --- command builder ----------------------------------------------------

    def _build_cmd(self, action, dataset):
        """
        Build a subprocess command that either uses:
        - the installed CLI 'judaicalink-loader' (legacy interface),
        - or the Python script loader.py with flags supported by your loader.py.
        """
        # Try the CLI first
        cli = self._resolve_cli()
        if cli:
            # This assumes the legacy CLI accepted: judaicalink-loader <load|unload|delete> [dataset]
            cmd = cli + [action]
            if dataset:
                cmd.append(dataset)
            return cmd

        # Fallback: use loader.py
        loader_py = self._resolve_loader_py()
        if not loader_py:
            raise CommandError(
                "Could not find 'judaicalink-loader' on PATH "
                "and failed to locate a loader.py. "
                "Set settings.JUDAICALINK_LOADER_PATH or env JUDAICALINK_LOADER_PATH."
            )

        # Map admin actions to loader.py flags (based on your loader.py interface)
        # - load all         -> python loader.py
        # - load one dataset -> python loader.py --dataset <ds>
        # - unload/delete    -> python loader.py --dataset <ds> --drop-only
        #   (there is no 'unload all' in loader.py; we only support per-dataset here)
        if action == 'load':
            if dataset == 'all':
                return [sys.executable, str(loader_py), '--load-all', '--force']
            else:
                return [sys.executable, str(loader_py), '--dataset', dataset]

        if action in ('unload', 'delete'):
            if dataset == 'all':
                return ['__BATCH__']
            return [sys.executable, str(loader_py), '--dataset', dataset, '--drop-only']

        # Should never reach here due to choices validation
        raise CommandError(f"Unsupported action: {action}")

    # --- main handler -------------------------------------------------------

    # --- main handler -------------------------------------------------------

    def handle(self, *args, **options):
        action = options["action"]
        dataset = options["dataset"]

        # Neuer Weg: EIN Dataset laden → direkt über Datafiles (ohne loader.py)
        if action == "load" and dataset != "all":
            # dataset ist der Name/Slug aus dem Admin (name oder dataslug)
            self._load_dataset_from_datafiles(dataset)
            return

        # Slug-Liste bestimmen
        if dataset == "all":
            # Für load/unload/delete all iterieren wir über alle bekannten Datasets
            slugs = list(_iter_dataset_slugs())
        else:
            slugs = [dataset]

        for ds_slug in slugs:
            # Vor dem eigentlichen Loader-Call ggf. loaded-Flag zurücksetzen
            if action in ("unload", "delete"):
                _set_loaded_flag(ds_slug, False)

            # Command über die zentrale Builder-Funktion zusammenbauen
            cmd = self._build_cmd(action, ds_slug)

            self.stdout.write(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, env=env)

            if result.returncode != 0:
                raise CommandError(
                    f"Loader-Fehler (exit {result.returncode}) für Dataset {ds_slug}"
                )

            # Nach erfolgreichem Lauf: Flags & Metadaten anpassen
            if action == "load":
                _set_loaded_flag(ds_slug, True)
                # Metadaten (falls vorhanden) für dieses Dataset aktualisieren
                try:
                    self._load_metadata_graph(ds_slug)
                except Exception as e:
                    self.stderr.write(f"[META][ERROR] {e}")
            elif action in ("unload", "delete"):
                # Metadaten für dieses Dataset entfernen, aber gemeinsamen Graph behalten
                try:
                    self._delete_metadata_for_slug(ds_slug)
                except Exception as e:
                    self.stderr.write(f"[META][ERROR] {e}")
