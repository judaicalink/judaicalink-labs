# labs/data/management/commands/solr_load_dataset.py
import os

import gzip
from pathlib import Path
from urllib.parse import urlparse

import pysolr
import re
import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data.models import Dataset


DUMPS_LOCAL_DIR = os.environ.get(
    "DUMPS_LOCAL_DIR",
    getattr(settings, "LABS_DUMPS_LOCAL", "/mnt/data/dumps")
)

GENERATORS_PATH = getattr(settings, "GENERATORS_BASE_DIR", None)

# --- Mapping wie in sync_fuseki_solr ---------------------------------------

property2field = {
    'http://www.w3.org/2004/02/skos/core#prefLabel': 'name',
    'http://www.w3.org/2004/02/skos/core#altLabel': 'Alternatives',
    'http://data.judaicalink.org/ontology/birthDate': 'birthDate',
    'http://data.judaicalink.org/ontology/birthYear': 'birthYear',
    'http://data.judaicalink.org/ontology/birthLocation': 'birthLocation',
    'http://data.judaicalink.org/ontology/deathDate': 'deathDate',
    'http://data.judaicalink.org/ontology/deathYear': 'deathYear',
    'http://data.judaicalink.org/ontology/deathLocation': 'deathLocation',
    'http://data.judaicalink.org/ontology/hasAbstract': 'Abstract',
    'http://data.judaicalink.org/ontology/hasPublication': 'Publication',
    'http://d-nb.info/standards/elementset/gnd#gndIdentifier': 'gndIdentifier',
    'http://data.judaicalink.org/ontology/occupation': 'Occupation',
}

all_fields = set(property2field.values()) | {'link', 'dataslug'}
schema_fields = {}
for field in all_fields:
    if field in ('birthYear', 'deathYear'):
        ftype, mv = 'pint', False
    elif field in ('link', 'dataslug'):
        ftype, mv = 'string', False
    elif field in ('birthDate', 'deathDate'):
        ftype, mv = 'string', True
    else:
        ftype, mv = 'text_general', True

    schema_fields[field] = {
        'name': field,
        'type': ftype,
        'stored': True,
        'indexed': True,
        'multiValued': mv,
    }


def cleanstring(value: str) -> str:
    v = re.sub(r'\s+', ' ', value).strip()
    return v.rstrip(',')


def convert_date(val: str) -> str:
    from datetime import datetime
    formats = ['%Y-%m-%d', '%Y-%m', '%d.%m.%Y', '%Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            continue
    return val


def resolve_datafile_path(df, dataslug, stdout=None) -> Path:
    """
    Versucht aus Datafile.url einen lokalen Pfad zu machen.

    Reihenfolge:
    1. Absoluter Pfad aus df.url
    2. Mapping von HTTP-URLs / relativen Pfaden nach DUMPS_LOCAL_DIR
    3. Fallback: JUDAICALINK_GENERATORS_PATH/<slug>/output/<slug>.ttl(.gz)
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
            rel = rel.split("dumps/", 1)[1]  # z.B. "gba/current/gba-final-01.ttl.gz"
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




class Command(BaseCommand):
    help = "Lädt ein einzelnes Dataset (nach name/dataslug) in den SOLR-Index."

    def add_arguments(self, parser):
        parser.add_argument("slug", type=str)

    def ensure_schema(self, solr_base: str):
        url = f"{solr_base}/schema/fields"
        self.stdout.write("[SCHEMA] Fetching existing schema fields…")
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            existing = {f["name"] for f in resp.json().get("fields", [])}
            self.stdout.write(f"[SCHEMA] Found {len(existing)} fields")
            for name, spec in schema_fields.items():
                if name not in existing:
                    self.stdout.write(f"[SCHEMA] Adding field {name}")
                    r = requests.post(url, json={"add-field": spec})
                    r.raise_for_status()
            self.stdout.write("[SCHEMA] Schema verification complete")
        except Exception as e:
            self.stderr.write(f"[SCHEMA][ERROR] {e}")

    # ---------------------------------------------------------
    # Haupt-Handler
    # ---------------------------------------------------------
    def handle(self, *args, **options):
        slug = options["slug"]
        self.stdout.write(self.style.NOTICE(f"Indexiere Dataset: {slug}"))

        # Dataset finden
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

        # SOLR-Endpunkt wie in sync_fuseki_solr
        solr_base = f"{settings.SOLR_SERVER.rstrip('/')}/{settings.JUDAICALINK_INDEX.lstrip('/')}"
        solr = pysolr.Solr(solr_base, timeout=60)

        # Schema prüfen
        self.ensure_schema(solr_base)

        # Alte Dokumente für dieses Dataset löschen
        self.stdout.write(f"Lösche alte Dokumente in SOLR für dataslug=\"{dataslug}\" …")
        solr.delete(q=f'dataslug:"{dataslug}"')
        solr.commit()

        # --- AB HIER KEINE METADATEN MEHR LADEN! ---

        # Datafiles laden
        datafiles = ds.datafile_set.all()
        if not datafiles:
            raise CommandError(f"Dataset '{slug}' hat keine Datafiles zum Indexen.")

        indexed = 0
        files_with_docs = 0
        resolved_any = 0
        missing_files = 0

        for df in datafiles:
            path = resolve_datafile_path(df, dataslug, stdout=self.stdout)

            if not path.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"[SOLR] Datei fehlt: {path} (aus url={df.url})"
                    )
                )
                missing_files += 1
                continue

            resolved_any += 1
            self.stdout.write(f"→ Lade Datei: {path}")

            path_str = str(path)

            # 1) Turtle / Turtle.gz mit rdflib
            if path_str.endswith(".ttl") or path_str.endswith(".ttl.gz"):
                docs = self._parse_rdf_with_rdflib(path, dataslug)
            # 2) Alles andere als N-Triples über Zeilenparser
            else:
                if path_str.endswith(".gz"):
                    open_func = gzip.open
                    open_kwargs = {
                        "mode": "rt",
                        "encoding": "utf-8",
                        "errors": "replace",
                    }
                else:
                    open_func = open
                    open_kwargs = {
                        "mode": "r",
                        "encoding": "utf-8",
                        "errors": "replace",
                    }

                with open_func(path, **open_kwargs) as fh:
                    docs = self._parse_ntriples_to_solr_docs(fh, dataslug)

            if docs:
                files_with_docs += 1
                solr.add(docs)
                indexed += len(docs)
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Aus Datei {path} wurden 0 Solr-Dokumente erzeugt "
                        f"(evtl. keine passenden Properties in property2field oder falsches Format)."
                    )
                )

        solr.commit()

        self.stdout.write(
            f"[SOLR] Dateien mit gültigem Pfad: {resolved_any}, fehlende Dateien: {missing_files}"
        )

        if indexed == 0:
            ds.indexed = False
            ds.save()
            raise CommandError(
                f"Dataset '{slug}' erzeugte insgesamt 0 Solr-Dokumente. "
                f"Bitte Dump-Dateien und property2field-Mapping prüfen."
            )

        ds.indexed = True
        ds.save()
        self.stdout.write(self.style.SUCCESS(
            f"[SOLR] Dataset '{slug}' erfolgreich indexiert ({indexed} Dokumente)."
        ))

    def _parse_rdf_with_rdflib(self, path: Path, dataslug: str):
        """
        Parsed eine RDF-Datei (z.B. Turtle) mit rdflib und baut Solr-Dokumente
        auf Basis von property2field wie in sync_fuseki_solr.
        Unterstützt auch .ttl.gz (gzip-komprimiert).
        """
        try:
            import rdflib
        except ImportError:
            raise CommandError(
                "rdflib ist nicht installiert. Bitte mit "
                "'pip install rdflib' nachinstallieren, "
                "um Turtle-Dateien (.ttl/.ttl.gz) zu verarbeiten."
            )

        g = rdflib.Graph()
        fmt = "turtle"

        path_str = str(path)

        # --- WICHTIG: gzipped Turtle vorher entpacken ---
        if path_str.endswith(".ttl.gz"):
            import gzip

            self.stdout.write(
                f"[RDF] Parse gzipped Turtle {path} mit rdflib im Format '{fmt}' …"
            )
            # gzip.open liefert bereits die dekomprimierten Bytes
            with gzip.open(path, "rb") as f:
                # rdflib kann direkt mit einem File-Objekt umgehen
                g.parse(file=f, format=fmt)
        else:
            self.stdout.write(
                f"[RDF] Parse {path} mit rdflib im Format '{fmt}' …"
            )
            g.parse(path.as_posix(), format=fmt)

        updates = {}
        total_triples = 0
        mapped_triples = 0

        for s, p, o in g:
            total_triples += 1
            s_str = str(s)
            p_str = str(p)

            field = property2field.get(p_str)
            if not field:
                continue

            mapped_triples += 1

            if isinstance(o, rdflib.term.Literal):
                val = str(o)
            else:
                val = str(o)

            val = cleanstring(val)

            if s_str not in updates:
                updates[s_str] = {
                    "id": s_str,
                    "link": {"set": s_str},
                    "dataslug": {"set": dataslug},
                }

            if field in updates[s_str]:
                updates[s_str][field].setdefault("add", []).append(val)
            else:
                updates[s_str][field] = {"add": [val]}

        self.stdout.write(
            f"[RDF] Gesamt-Tripel: {total_triples}, "
            f"davon mit bekanntem Prädikat (property2field): {mapped_triples}"
        )

        docs = []
        for doc in updates.values():
            for key, val in list(doc.items()):
                if isinstance(val, dict) and "add" in val:
                    cleaned = [cleanstring(x) for x in val["add"]]
                    #if key in ("birthDate", "deathDate"):
                    #    cleaned = [convert_date(x) for x in cleaned]
                    doc[key]["add"] = cleaned
            docs.append(doc)

        return docs

    # ---------------------------------------------------------
    # NT → Solr-Dokumente (analog zu sync_fuseki_solr)
    # ---------------------------------------------------------
    def _parse_ntriples_to_solr_docs(self, fh, dataslug: str):
        """
        Liest ein N-Triples/TTL-ähnliches Dumpfile und baut
        Solr-Dokumente, die nach Subject aggregiert sind.
        Nur Predicates, die in property2field gemappt sind, werden indexiert.
        """

        updates = {}

        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Einfacher Parser für N-Triples-Zeilen: <s> <p> <o> .
            if line.endswith("."):
                line = line[:-1].strip()

            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue

            s_raw, p_raw, o_raw = parts

            # URIs ohne <>
            s = s_raw.strip("<>")
            p = p_raw.strip("<>")

            field = property2field.get(p)
            if not field:
                # Predicate nicht relevant für unseren Solr-Core
                continue

            # Objekt parsen (Literal oder URI)
            o_raw = o_raw.strip()
            if o_raw.startswith("<") and o_raw.endswith(">"):
                val = o_raw.strip("<>")
            elif o_raw.startswith('"'):
                # Literal: "value"@de oder "value"^^<datatype>
                try:
                    # sehr einfacher Ansatz: erstes und letztes Anführungszeichen
                    first = o_raw.find('"')
                    last = o_raw.rfind('"')
                    if last > first:
                        val = o_raw[first + 1:last]
                    else:
                        val = o_raw.strip('"')
                except Exception:
                    val = o_raw.strip('"')
            else:
                val = o_raw

            val = cleanstring(val)

            if s not in updates:
                updates[s] = {
                    "id": s,
                    "link": {"set": s},
                    "dataslug": {"set": dataslug},
                }

            if field in updates[s]:
                updates[s][field].setdefault("add", []).append(val)
            else:
                updates[s][field] = {"add": [val]}

        # Clean + Datumskonvertierung wie in sync_fuseki_solr
        docs = []
        for doc in updates.values():
            for key, val in list(doc.items()):
                if isinstance(val, dict) and "add" in val:
                    cleaned = [cleanstring(x) for x in val["add"]]
                    #if key in ("birthDate", "deathDate"):
                    #    cleaned = [convert_date(x) for x in cleaned]
                    doc[key]["add"] = cleaned
            docs.append(doc)

        return docs
