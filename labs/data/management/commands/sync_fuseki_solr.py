import re
import requests
import pysolr
import logging
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand

# Mapping RDF predicates to Solr fields
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

# Schema fields beyond property fields
all_fields = set(property2field.values()) | {'link', 'dataslug'}
schema_fields = {}
for field in all_fields:
    if field in ('birthYear', 'deathYear'):
        ftype, mv = 'pint', False
    elif field in ('link', 'dataslug'):
        ftype, mv = 'string', False
    else:
        ftype, mv = 'text_general', True
    schema_fields[field] = {
        'name': field,
        'type': ftype,
        'stored': True,
        'indexed': True,
        'multiValued': mv
    }

# Initialize module logger
logger = logging.getLogger('sync_fuseki_solr')
logger.setLevel(logging.DEBUG)

# Clean string function

def cleanstring(value):
    """Trim whitespace, collapse spaces, strip commas."""
    v = re.sub(r'\s+', ' ', value).strip()
    return v.rstrip(',')

# Date conversion for ISO Solr format

def convert_date(val):
    """
    Try parsing common date formats, fallback to raw string.
    """
    formats = ['%Y-%m-%d', '%Y-%m', '%d.%m.%Y', '%Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            continue
    return val

class Command(BaseCommand):
    help = 'Sync Fuseki RDF triples to Solr with incremental clears, cleaning, logging, and console output'

    def ensure_schema(self, solr_base):
        url = f"{solr_base}/schema/fields"
        try:
            print("[SCHEMA] Fetching existing schema fields...")
            resp = requests.get(url)
            resp.raise_for_status()
            existing = {f['name'] for f in resp.json().get('fields', [])}
            print(f"[SCHEMA] Found {len(existing)} fields")
            for name, spec in schema_fields.items():
                if name not in existing:
                    print(f"[SCHEMA] Adding field {name}")
                    logger.info(f"Adding schema field {name}")
                    r = requests.post(url, json={'add-field': spec})
                    r.raise_for_status()
            print("[SCHEMA] Schema verification complete")
        except Exception as e:
            print(f"[SCHEMA][ERROR] {e}")
            logger.error(f"Schema sync error: {e}")

    def handle(self, *args, **opts):
        # Set up file logging
        fh_all = logging.FileHandler('sync_fuseki_solr.log')
        fh_all.setLevel(logging.INFO)
        fh_err = logging.FileHandler('sync_fuseki_solr_errors.log')
        fh_err.setLevel(logging.ERROR)
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh_all.setFormatter(fmt)
        fh_err.setFormatter(fmt)
        logger.addHandler(fh_all)
        logger.addHandler(fh_err)

        solr_base = f"{settings.SOLR_SERVER.rstrip('/')}/{settings.JUDAICALINK_INDEX.lstrip('/')}"
        solr = pysolr.Solr(solr_base, timeout=10)

        print("[INFO] Starting schema check...")
        logger.info("Starting schema sync")
        self.ensure_schema(solr_base)

        sparql_url = 'http://localhost:3030/judaicalink/query'
        graphs_q = "SELECT DISTINCT ?graph WHERE { GRAPH ?graph {} }"
        try:
            print("[INFO] Fetching graph list...")
            r = requests.post(sparql_url, data={'query': graphs_q}, headers={'Accept': 'application/sparql-results+json'})
            r.raise_for_status()
            graphs = [b['graph']['value'] for b in r.json()['results']['bindings']]
            print(f"[INFO] Found {len(graphs)} graphs")
            logger.info(f"Found {len(graphs)} graphs")
        except Exception as e:
            print(f"[ERROR] Graph fetch failed: {e}")
            logger.error(f"Graph fetch failed: {e}")
            return

        cnt_q = lambda g: f"SELECT (COUNT(*) as ?count) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }}"
        data_q = lambda g, o, l: f"SELECT ?s ?p ?o WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }} OFFSET {o} LIMIT {l}"

        for graph in graphs:
            slug = graph.rstrip('/').split('/')[-1]
            # clear only this dataslug
            try:
                print(f"[INFO] Clearing docs for dataslug={slug}")
                solr.delete(q=f"dataslug:{slug}")
                solr.commit()
                print(f"[INFO] Cleared Solr docs for dataslug={slug}")
                logger.info(f"Cleared Solr docs for dataslug={slug}")
            except Exception as e:
                print(f"[ERROR] Clear dataslug {slug} failed: {e}")
                logger.error(f"Clear dataslug {slug} failed: {e}")

            # count triples
            try:
                cr = requests.post(sparql_url, data={'query': cnt_q(graph)}, headers={'Accept': 'application/sparql-results+json'})
                cr.raise_for_status()
                total = int(cr.json()['results']['bindings'][0]['count']['value'])
                print(f"[INFO] Graph {slug} has {total} triples")
                logger.info(f"Graph {slug} has {total} triples")
            except Exception as e:
                print(f"[ERROR] Count failed for {slug}: {e}")
                logger.error(f"Count failed for {slug}: {e}")
                continue

            offset = 0
            while offset < total:
                try:
                    print(f"[INFO] Fetching triples from {slug} offset={offset}")
                    dr = requests.post(sparql_url, data={'query': data_q(graph, offset, 1000)}, headers={'Accept': 'application/sparql-results+json'})
                    dr.raise_for_status()
                    rows = dr.json()['results']['bindings']
                    print(f"[INFO] Retrieved {len(rows)} triples")
                    logger.info(f"Fetched {len(rows)} triples from {slug} offset={offset}")
                except Exception as e:
                    print(f"[ERROR] Fetch error {slug} offset={offset}: {e}")
                    logger.error(f"Fetch error {slug} offset={offset}: {e}")
                    break

                updates = {}
                for rbind in rows:
                    s = rbind['s']['value']; p = rbind['p']['value']; o = rbind['o']
                    fld = property2field.get(p)
                    if s not in updates:
                        updates[s] = {'id': s, 'link': {'set': s}, 'dataslug': {'set': slug}}
                    if not fld:
                        continue
                    v = o['value'] if o['type']=='uri' else cleanstring(o['value'])
                    if fld in updates[s]:
                        updates[s][fld]['add'].append(v)
                    else:
                        updates[s][fld] = {'add': [v]}

                # clean and convert dates
                docs = []
                for doc in updates.values():
                    for key, val in list(doc.items()):
                        if isinstance(val, dict) and 'add' in val:
                            cleaned = [cleanstring(x) for x in val['add']]
                            if key in ('birthDate','deathDate'):
                                cleaned = [convert_date(x) for x in cleaned]
                            doc[key]['add'] = cleaned
                    docs.append(doc)

                try:
                    print(f"[INFO] Indexing {len(docs)} docs for {slug} offset={offset}")
                    solr.add(docs)
                    solr.commit()
                    print(f"[INFO] Indexed batch successfully")
                    logger.info(f"Indexed {len(docs)} docs for {slug} offset={offset}")
                except Exception as e:
                    print(f"[ERROR] Indexing error {slug} offset={offset}: {e}")
                    logger.error(f"Indexing error {slug} offset={offset}: {e}")
                    for d in docs:
                        print(f"[ERROR] Failed doc: {d}")
                        logger.error(f"Failed doc: {d}")

                offset += len(rows)
        print("[INFO] Sync complete.")
        logger.info("Sync complete.")
