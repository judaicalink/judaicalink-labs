from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import gzip
import rdflib
from backend import models, dataset_loader
import requests, os
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF, SKOS, OWL, FOAF

# custom function for cleaning query string from the dataset
def clean_query(s):
    query = s.strip(" [?]").lstrip(" in").lstrip(" bei").lstrip("(?)").strip("'").strip(";")
    query = query.replace("?", "").replace("/", " ").replace(".", "").replace(",", "").replace("- ", " ").replace("°u", "ů")
    query = query.replace("   ", " ").replace("  ", " ")
    query = query.strip()
    return query



class Command(BaseCommand):
    help = 'Create parsed geoinformation'

    def handle(self, *args, **kwargs):
        # we will collect all strings we are not (yet) able to parse.
        # goal: empty this set ;-)
        jl = rdflib.Namespace("http://data.judaicalink.org/ontology/")
        
        # First, we iterate over all data files in our django database
        for df in models.Datafile.objects.all():
            # we use the backend functions to download and access the actual files 
            filename = dataset_loader.load_rdf_file(df.url)
            # we check, if the file is supposed to be RDF
            if df.dataset.is_rdf():
                self.stdout.write(f"Processing: {filename}")
                # we open the file, eiter directly or via gzip.open
                openfunc = open
                if filename.endswith(".gz"):
                    openfunc = gzip.open
                with openfunc(filename, "rt", encoding="utf8") as f:
                    geonames_user = settings.GEONAMES_API_USER # here your geonames username

                    # declare namespaces and URIRefs to be used in the script
                    jl = Namespace("http://data.judaicalink.org/ontology/")
                    wgs84 = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
                    gn = Namespace("http://www.geonames.org/ontology#")

                    jl_data = URIRef("http://data.judaicalink.org/data/")
                    jl_birth_uri = URIRef("http://data.judaicalink.org/ontology/birthLocationURI")
                    jl_death_uri = URIRef("http://data.judaicalink.org/ontology/deathLocationURI")
                    gn_root = URIRef("http://sws.geonames.org/")

                    # parse input data
                    dataset = Graph()
                    dataset.parse(f, format='ttl')

                    print("Dataset graph contains %s statements." % len(dataset))

                    geo_data = Graph() # container graph for extracted geographic information and mappings geonames - jl
                    geo_data.bind("skos", SKOS)
                    geo_data.bind("owl", OWL)
                    geo_data.bind("geo", wgs84)

                    dataset_geo_enriched = Graph() # container for birth/death location URIs 
                    dataset_geo_enriched.bind("skos", SKOS)
                    dataset_geo_enriched.bind("geo", wgs84)
                    dataset_geo_enriched.bind("jl", jl)

                    topo = set()
                    request_count = 0
                    for s,p,o in dataset.triples((None, jl.birthLocation, None)):
                        
                        query = clean_query(o) # clean the string for search
                        
                        if query not in ("", "NN"): # avoid empty queries
                            
                            topo.add(query)
                            
                            # make request to Geonames
                            url = "http://api.geonames.org/search?"
                            params = {'q': query, 'maxRows': '1', 'type': 'rdf', 'username': geonames_user}
                            response = requests.get(url, params=params)
                            request_count += 1
                            
                            # parse response
                            res = Graph() 
                            data = res.parse(data=response.text, format='xml')
                            
                            
                            if response.status_code == 200:
                                
                                gn_entity_id = ""
                                for sub, pred, obj in data.triples((None, wgs84.lat, None)):
                                    gn_entity_id = sub.split(gn_root)[1].rstrip('/')
                                    dataset_geo_enriched.add((s, jl_birth_uri, jl_data+"geonames/"+gn_entity_id))
                                    
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, OWL.sameAs, sub))
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, pred, obj))
                                    
                                for sub, pred, obj in data.triples((None, wgs84.long, None)):
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, pred, obj))
                                    
                                for sub, pred, obj in data.triples((None, gn.name, None)):
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, SKOS.prefLabel, obj))
                                for sub, pred, obj in data.triples((None, gn.alternateName, None)):
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, SKOS.altLabel, obj))
                            else:
                                print("Something went wrong with the query" + query)
                                print("Response status:", str(response.status_code))
                                print()   

                    print("Birth Locations:")
                    print("Found %s different toponyms"%len(topo))
                    print("Made %s requests to Geonames"%request_count)
                    print()


                    topo = set()
                    request_count = 0
                    for s,p,o in dataset.triples((None, (jl.deathLocation), None)):
                        
                        query = clean_query(o) # clean the string for search
                        
                        if o not in ("", "NN"): # avoid empty queries
                            
                            topo.add(query)
                            
                            # make request to Geonames
                            url = "http://api.geonames.org/search?"
                            params = {'q': query, 'maxRows': '1', 'type': 'rdf', 'username': geonames_user}
                            response = requests.get(url, params=params)
                            request_count += 1
                            
                            # parse response
                            res = Graph() 
                            data = res.parse(data=response.text, format='xml')
                            
                            if response.status_code == 200:
                                
                                gn_entity_id = ""
                                for sub, pred, obj in data.triples((None, wgs84.lat, None)):
                                    gn_entity_id = sub.split(gn_root)[1].rstrip('/')
                                    dataset_geo_enriched.add((s, jl_death_uri, jl_data+"geonames/"+gn_entity_id))
                                    
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, OWL.sameAs, sub))
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, pred, obj))
                                
                                for sub, pred, obj in data.triples((None, wgs84.long, None)):
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, pred, obj))
                                    
                                for sub, pred, obj in data.triples((None, gn.name, None)):
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, SKOS.prefLabel, obj))
                                    
                                for sub, pred, obj in data.triples((None, gn.alternateName, None)):
                                    geo_data.add((jl_data+"geonames/"+gn_entity_id, SKOS.altLabel, obj))
                            else:
                                print("Something went wrong with the query" + query)
                                print("Response status:", str(response.status_code))
                                print()
                                

                    print("Death Locations:")
                    print("Found %s different toponyms in the dataset"%len(topo))
                    print("Made %s requests to Geonames"%request_count)
                    print()


                    print("Collected %s geo interlink statements." % len(geo_data))
                    print("New dataset has been enriched with %s statements." % len(dataset_geo_enriched))

                    # save the updated dataset
                    dataset_geo_enriched.serialize(destination=f"{filename[20:]}_geo_enriched.ttl", format="ttl")

                    # save the geographic information
                    geo_size = 0
                    print()
                    if 'geo_interlinks.ttl' in os.listdir("."):
                        print("The geographic interlink dataset already exists and will be updated...")
                        existing_geo = Graph()
                        existing_geo.parse("geo_interlinks.ttl", format="ttl")
                        geo_size = len(existing_geo)
                        for s,p,o in geo_data:
                            existing_geo.add((s,p,o))
                        print("Added " + str(len(existing_geo)-geo_size) + " triples to geographic dataset.")
                        existing_geo.serialize(destination="geo_interlinks.ttl", format="ttl")
                    else:
                        print("The geographic interlink dataset is being created.")
                        geo_data.serialize(destination="geo_interlinks.ttl", format="ttl")
                        print("Added " + str(len(geo_data)) + " triples to geographic dataset (geo_interlinks.ttl).")




                
