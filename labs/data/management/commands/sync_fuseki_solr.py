import re
import requests
import pysolr
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

# Fields to ensure in Solr schema
required_fields = {
    'link': {
        'name': 'link',
        'type': 'string',
        'stored': True,
        'indexed': True,
        'multiValued': False
    },
    'dataslug': {
        'name': 'dataslug',
        'type': 'string',
        'stored': True,
        'indexed': True,
        'multiValued': False
    },
}

def cleanstring(value, chars):
    """
    Remove unwanted characters and normalize whitespace.
    """
    for c in chars:
        value = value.replace(c, '')
    return re.sub(r'\s+', ' ', value).strip()

class Command(BaseCommand):
    help = 'Sync Fuseki RDF triples (all graphs) to Solr, updating schema and indexing data'

    def ensure_schema_fields(self, solr_base):
        """
        Check and add required fields to Solr schema if missing.
        """
        schema_url = f"{solr_base}/schema/fields"
        try:
            print("[INFO] Verifying Solr schema fields...")
            resp = requests.get(schema_url)
            resp.raise_for_status()
            existing = {f['name'] for f in resp.json().get('fields', [])}

            for fname, fdef in required_fields.items():
                if fname not in existing:
                    print(f"[INFO] Adding missing field to schema: {fname}")
                    add_payload = {'add-field': fdef}
                    add_resp = requests.post(schema_url, json=add_payload)
                    add_resp.raise_for_status()
                    print(f"[INFO] Field {fname} added.")
            print("[INFO] Schema fields verified.")
        except Exception as e:
            self.stderr.write(f"[ERROR] Schema update failed: {e}")

    def handle(self, *args, **options):
        # Initialize Solr client
        solr_base = f"{settings.SOLR_SERVER.rstrip('/')}/{settings.JUDAICALINK_INDEX.lstrip('/')}"
        solr = pysolr.Solr(solr_base, timeout=10)

        # Ensure required schema fields
        self.ensure_schema_fields(solr_base)

        # Clear existing index
        try:
            print("[INFO] Clearing Solr index ...")
            solr.delete(q='*:*')
            solr.commit()
            print("[INFO] Solr index cleared.")
        except Exception as e:
            self.stderr.write(f"[ERROR] Unable to clear Solr index: {e}")
            return

        sparql_url = "http://localhost:3030/judaicalink/query"
        # Fetch all named graphs
        graph_query = """
        SELECT DISTINCT ?graph
        WHERE { GRAPH ?graph {} }
        """
        try:
            print("[INFO] Fetching list of graphs...")
            resp = requests.post(
                sparql_url,
                data={'query': graph_query},
                headers={'Accept': 'application/sparql-results+json'}
            )
            resp.raise_for_status()
            graphs = [b['graph']['value'] for b in resp.json()['results']['bindings']]
            print(f"[INFO] Found {len(graphs)} graphs.")
        except Exception as e:
            self.stderr.write(f"[ERROR] Failed to fetch graphs: {e}")
            return

        # Query templates
        count_query = lambda g: f"SELECT (COUNT(*) as ?count) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }}"
        data_query = lambda g, off, lim: f"SELECT ?s ?p ?o WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }} OFFSET {off} LIMIT {lim}"

        # Iterate each graph
        for graph in graphs:
            dataslug = graph.rstrip('/').split('/')[-1]
            try:
                cq = count_query(graph)
                cresp = requests.post(
                    sparql_url,
                    data={'query': cq},
                    headers={'Accept': 'application/sparql-results+json'}
                )
                cresp.raise_for_status()
                total = int(cresp.json()['results']['bindings'][0]['count']['value'])
                print(f"[INFO] Graph {graph} ({dataslug}) has {total} triples.")
            except Exception as e:
                self.stderr.write(f"[ERROR] Failed to count triples for {graph}: {e}")
                continue

            offset = 0
            while offset < total:
                try:
                    dq = data_query(graph, offset, 1000)
                    dresp = requests.post(
                        sparql_url,
                        data={'query': dq},
                        headers={'Accept': 'application/sparql-results+json'}
                    )
                    dresp.raise_for_status()
                    rows = dresp.json()['results']['bindings']
                    print(f"[INFO] Fetched {len(rows)} triples from {graph} (offset {offset}).")
                except Exception as e:
                    self.stderr.write(f"[ERROR] Failed fetching offset {offset} in {graph}: {e}")
                    break

                updates = {}
                for row in rows:
                    subj = row['s']['value']
                    pred = row['p']['value']
                    obj = row['o']
                    field = property2field.get(pred)

                    if subj not in updates:
                        updates[subj] = {
                            'id': subj,
                            'link': {'set': subj},
                            'dataslug': {'set': dataslug}
                        }
                    if not field:
                        continue

                    val = obj['value']
                    if obj.get('type') == 'literal':
                        val = cleanstring(val, ['\n', '\t'])

                    if field in updates[subj]:
                        existing = updates[subj][field]['add']
                        if isinstance(existing, list):
                            existing.append(val)
                        else:
                            updates[subj][field]['add'] = [existing, val]
                    else:
                        updates[subj][field] = {'add': [val]}

                docs = list(updates.values())
                try:
                    print(f"[INFO] Applying atomic updates for {len(docs)} documents...")
                    solr.add(docs)
                    solr.commit()
                    print(f"[INFO] Committed batch at offset {offset}.")
                except Exception as e:
                    self.stderr.write(f"[ERROR] Solr atomic update failed at offset {offset}: {e}")

                offset += len(rows)

        print("[INFO] Completed syncing all graphs.")
