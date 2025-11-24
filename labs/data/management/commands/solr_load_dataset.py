# labs/data/management/commands/solr_load_dataset.py
import gzip
import os
import pysolr
import re
import requests
import rdflib
from data.models import Dataset
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from urllib.parse import urlparse

DUMPS_LOCAL_DIR = os.environ.get(
    "DUMPS_LOCAL_DIR",
    getattr(settings, "LABS_DUMPS_LOCAL", "/mnt/data/dumps")
)

GENERATORS_PATH = getattr(settings, "GENERATORS_BASE_DIR", None)

# Mapping

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
    Attempts to create a local path from Datafile.url.

    Order:
    1. Absolute path from df.url
    2. Mapping of HTTP URLs / relative paths to DUMPS_LOCAL_DIR
    3. Fallback: JUDAICALINK_GENERATORS_PATH/<slug>/output/<slug>.ttl(.gz)
    4. Fallback: raw path(df.url)
    """
    raw = (df.url or "").strip()
    p = Path(raw)

    def log(msg: str):
        if stdout is not None:
            stdout.write(msg)

    # 1) Absolute path direct
    if p.is_absolute():
        log(f"[PATH] Absoulte path from url: {p} (exists={p.exists()})")
        return p

    # 2) Base dumps directory (only if it exists)
    base_dumps = None
    if DUMPS_LOCAL_DIR:
        base_path = Path(DUMPS_LOCAL_DIR)
        if base_path.exists():
            base_dumps = base_path
        else:
            log(f"[PATH] DUMPS_LOCAL_DIR does not exist: {base_path}")

    candidates = []

    # HTTP-URL → Path relative to /dumps/
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        rel = parsed.path.lstrip("/")
        if "dumps/" in rel:
            rel = rel.split("dumps/", 1)[1]  # e.g. "gba/current/gba-final-01.ttl.gz"
        if base_dumps:
            candidates.append(base_dumps / rel)
    else:
        # Not HTTP → direct under unter base_dumps
        if base_dumps:
            candidates.append(base_dumps / raw)

    # 2b) Validate candidates from dumps
    for cand in candidates:
        log(f"[PATH] Check candidate: {cand}")
        if cand.exists():
            log(f"[PATH] → Use file (dumps): {cand}")
            return cand

    # 3) Fallback: Generators Folder /<slug>/output/<slug>.ttl(.gz)
    if GENERATORS_PATH:
        gen_base = Path(GENERATORS_PATH) / dataslug / "output"
        cand_gz = gen_base / f"{dataslug}.ttl.gz"
        cand_ttl = gen_base / f"{dataslug}.ttl"

        for cand in (cand_gz, cand_ttl):
            log(f"[PATH] Checking Generator candidate: {cand}")
            if cand.exists():
                log(f"[PATH] → Use file  (Generator): {cand}")
                return cand

    # 4) Fallback: raw path (is checked later)
    log(f"[PATH] No candidate found, use raw path: {p}")
    return p


class Command(BaseCommand):
    help = "Loads a single dataset (name/slug) into the SOLR-Index."

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
    # Main-Handler
    # ---------------------------------------------------------
    def handle(self, *args, **options):
        slug = options["slug"]
        self.stdout.write(self.style.NOTICE(f"Indexing dataset: {slug}"))

        # Find Dataset by name or dataslug
        try:
            ds = Dataset.objects.get(name=slug)
        except Dataset.DoesNotExist:
            try:
                ds = Dataset.objects.get(dataslug=slug)
            except Dataset.DoesNotExist:
                raise CommandError(
                    f"Dataset '{slug}' does not exist."
                )

        dataslug = ds.dataslug or ds.name

        # SOLR-Endpoint
        solr_base = f"{settings.SOLR_SERVER.rstrip('/')}/{settings.JUDAICALINK_INDEX.lstrip('/')}"
        solr = pysolr.Solr(solr_base, timeout=60)

        # Check the schema
        self.ensure_schema(solr_base)

        # Delete old documents for this dataset
        self.stdout.write(f"Deleting old documents in SOLR for slug=\"{dataslug}\" …")
        solr.delete(q=f'dataslug:"{dataslug}"')
        solr.commit()

        # Load Datafiles
        datafiles = ds.datafile_set.all()
        if not datafiles:
            raise CommandError(f"Dataset '{slug}' has no datafiles for indexing.")

        indexed = 0
        files_with_docs = 0
        resolved_any = 0
        missing_files = 0

        for df in datafiles:
            path = resolve_datafile_path(df, dataslug, stdout=self.stdout)

            if not path.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"[SOLR] File is missing: {path} (from url={df.url})"
                    )
                )
                missing_files += 1
                continue

            resolved_any += 1
            self.stdout.write(f"→ Loading file: {path}")

            path_str = str(path)

            # 1) Turtle / Turtle.gz with rdflib
            if path_str.endswith(".ttl") or path_str.endswith(".ttl.gz"):
                docs = self._parse_rdf_with_rdflib(path, dataslug)
            # 2) Everything else as N-Triples
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
                try:
                    solr.add(docs)
                except pysolr.SolrError as e:
                    self.stdout.write(self.style.ERROR(f"[SOLR] Error in Add: {e}"))
                    # Fallback: remove problematic fields and retry
                    for doc in docs:
                        doc.pop("birthDate", None)
                        doc.pop("deathDate", None)
                    self.stdout.write("[SOLR] birthDate/deathDate removed from all docs, retry …")
                    solr.add(docs)

                indexed += len(docs)
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ 0 Solr documents were generated from file {path}."
                    )
                )

        solr.commit()

        self.stdout.write(
            f"[SOLR] Files with valid path: {resolved_any}, missing files: {missing_files}"
        )

        if indexed == 0:
            ds.indexed = False
            ds.save()
            raise CommandError(
                f"Dataset '{slug}' generated a total of 0 Solr documents. "
                f"Please check the dump files and property2field mapping."
            )

        ds.indexed = True
        ds.save()
        self.stdout.write(self.style.SUCCESS(
            f"[SOLR] Dataset '{slug}' successfully indexed ({indexed} documents)."
        ))

    def _parse_rdf_with_rdflib(self, path: Path, dataslug: str):
        """
        Parses an RDF file (e.g., Turtle) using rdflib and builds Solr documents
        based on property2field.
        Also supports .ttl.gz (gzip-compressed).
        """

        g = rdflib.Graph()
        fmt = "turtle"

        path_str = str(path)

        # Import: unpack gzipped Turtle files first
        if path_str.endswith(".ttl.gz"):
            import gzip

            self.stdout.write(
                f"[RDF] Parse gzipped Turtle {path}  in format '{fmt}' …"
            )
            # gzip.open already delivers the decompressed bytes.
            with gzip.open(path, "rb") as f:
                # rdflib can directly manipulate a File object.
                g.parse(file=f, format=fmt)
        else:
            self.stdout.write(
                f"[RDF] Parse {path} with rdflib in format '{fmt}' …"
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
            f"[RDF] Total triples: {total_triples}, "
            f"of which with known prefix (property2field): {mapped_triples}"
        )

        docs = []
        for doc in updates.values():
            for key, val in list(doc.items()):
                if isinstance(val, dict) and "add" in val:
                    cleaned = [cleanstring(x) for x in val["add"]]

                    # Only allow numeric years for birthYear/deathYear
                    if key in ("birthYear", "deathYear"):
                        cleaned = [x for x in cleaned if re.fullmatch(r"\d{1,4}", x)]

                    # For birthDate/deathDate: only allow very conservative formats.
                    # e.g. YYYY or YYYY-MM or YYYY-MM-DD
                    if key in ("birthDate", "deathDate"):
                        cleaned = [
                            x
                            for x in cleaned
                            if re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?$", x)
                        ]

                    # If there are no valid values, remove the field
                    if not cleaned:
                        del doc[key]
                        continue

                    doc[key]["add"] = cleaned

            docs.append(doc)

        return docs

    # ---------------------------------------------------------
    # NT → Solr-Documents
    # ---------------------------------------------------------
    def _parse_ntriples_to_solr_docs(self, fh, dataslug: str):
        """
        Reads an N-triples/TTL-like dump file and builds
        Solr documents aggregated by subject.
        Only predicates mapped to property2field are indexed.
        """

        updates = {}

        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Simple Parser for N-Triples rows: <s> <p> <o> .
            if line.endswith("."):
                line = line[:-1].strip()

            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue

            s_raw, p_raw, o_raw = parts

            # URIs without <>
            s = s_raw.strip("<>")
            p = p_raw.strip("<>")

            field = property2field.get(p)
            if not field:
                # Predicate not relevant for Solr-Core
                continue

            # Parse Object (Literal or URI)
            o_raw = o_raw.strip()
            if o_raw.startswith("<") and o_raw.endswith(">"):
                val = o_raw.strip("<>")
            elif o_raw.startswith('"'):
                # Literal: "value"@de or "value"^^<datatype>
                try:
                    # First or last quote
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

        # Clean + convert dates
        docs = []
        for doc in updates.values():
            for key, val in list(doc.items()):
                if isinstance(val, dict) and "add" in val:
                    cleaned = [cleanstring(x) for x in val["add"]]
                    # if key in ("birthDate", "deathDate"):
                    #    cleaned = [convert_date(x) for x in cleaned]
                    doc[key]["add"] = cleaned
            docs.append(doc)

        return docs
