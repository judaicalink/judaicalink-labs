from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import gzip
import rdflib
from bs4 import BeautifulSoup
from pathlib import Path
import scrapy
import scrapy.crawler
import re
import gzip
import shutil
import os
import json
import toml
import subprocess
import logging
import sys
import traceback


## The base script
# Here, all the magic happens to ensure that our datasets are consistent.
# You should only change this code in close cooperation with the rest of 
# the team as any change here might break the other dataset commands.

# Good example commands to see this in action:
# - generate_yivo.py
# - ...

# The following namespaces are preconfigured and can directly be used.
# Make sure to import them in your dataset command:
# from ._dataset_command import jlo, jld, ...
namespaces = {
        "jlo": rdflib.Namespace("http://data.judaicalink.org/ontology/"),
        "jld": rdflib.Namespace("http://data.judaicalink.org/data/"),
        "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
        "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
        "rdf": rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        "rdfs": rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#"),
        "owl": rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
        "xsd": rdflib.Namespace("http://www.w3.org/2001/XMLSchema#"),
        "geo": rdflib.Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#"),
        "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
        "foaf": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
        "prov": rdflib.Namespace("http://www.w3.org/ns/prov#"),
        "cc": rdflib.Namespace("https://creativecommons.org/ns#"),
}

# Yes, this is evil. But saves a lot of writing ;-)
for ns in namespaces:
    exec(f"{ns} = namespaces['{ns}']")


# Logging for our scripts
log = logging.getLogger("log")
error = logging.getLogger("error")

# Helper to zip files, obviously...
def gzip_file(filename):
    with open(filename, 'rb') as f_in:
        with gzip.open(f'{filename}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(filename)


# Base class for the spiders.
class DatasetSpider(scrapy.Spider):
    # We provide two sets to keep track of already seen
    # pages and already queued ones. 
    # This is not always needed, Scrapy caches requests and
    # also provided means to avoid duplicates
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.visited = set()
        self.queued = set()


    # Helper to check if we already know a URL.
    def check_queue(self, url):
        if url in self.visited:
            return False
        if url in self.queued:
            return False
        self.queued.add(url)
        return True


# Base class for the command.
class DatasetCommand(BaseCommand):
    help = 'Base Command for a scraper'

    
    def __init__(self):
        super().__init__()
        self.gzip = False

    def add_arguments(self, parser):
        # This clears the Scrapy cache, otherwise all requests will be cached so that
        # you won't have to recrawl everything. Clear the cache if the original data on the Web has changed.
        # For production, we should change the caching to a full RFC 2616 Cache.
        # https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-policy-rfc2616
        parser.add_argument("--clear-cache", action="store_true", help="Clear cache before scraping.")
        parser.add_argument("--skip-scraping", action="store_true", help="Create RDF from JSON.")
        parser.add_argument("--no-rdf", action="store_true", help="Create only json")
        parser.add_argument("--gzip", action="store_true", help="Zip output files.")


    def set_metadata(self, metadata):
        '''
        This does various initialisations, it is mandatory to call this method at the beginning,
        but after setting self.gzip!
        '''
        self.metadata = metadata
        if not "files" in metadata:
            self.metadata["files"] = []
        self.directory = os.path.join(settings.LABS_DUMPS_LOCAL, metadata["slug"])
        self.add_file(f"{self.metadata['slug']}-metadata.ttl", description=f"Metadata for {self.metadata['slug']} dataset.")
        Path(self.directory).mkdir(parents=True, exist_ok=True)
        if os.path.exists(os.path.join(self.directory, "log.txt")):
            os.remove(os.path.join(self.directory, "log.txt"))
        if os.path.exists(os.path.join(self.directory, "error.txt")):
            os.remove(os.path.join(self.directory, "error.txt"))
        logFileHandler = logging.FileHandler(os.path.join(self.directory, "log.txt"), mode="w")
        errorFileHandler = logging.FileHandler(os.path.join(self.directory, "error.txt"), mode="w")
        log.addHandler(logFileHandler)
        log.addHandler(logging.StreamHandler(sys.stdout))
        error.addHandler(errorFileHandler)
        error.addHandler(logging.StreamHandler(sys.stdout))
        log.setLevel(logging.INFO)
        error.setLevel(logging.INFO)


    def add_file(self, filename, description = None):
        '''
        Adds a file officially to the dataset. Use just the filename, without .gz ending.
        Metadata includes filename, filepath (within the dumps directory), public URL, description.
        Public and local dumps location is configured in Django settings.
        '''
        if self.gzip and not filename.endswith(".gz"):
            filename += ".gz"

        if not description:
            description = f"RDF dump of the {self.metadata['slug']} dataset."

        self.metadata["files"].append({
                "filename": filename,
                "filepath": os.path.join(self.metadata['slug'], filename),
                "url": f"{settings.LABS_DUMPS_WEBROOT}{self.metadata['slug']}/{filename}",
                "description": description,
            })


    def start_scraper(self, scraper_class, filename=None, settings={}, args_list=[], kwargs_dict={}):
        if not filename:
            filename = f"{self.metadata['slug']}.jsonl"
        filepath = os.path.join(self.directory, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        default_settings = {
                'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
                'FEED_FORMAT': 'jsonlines',
                'FEED_URI': filepath,
                'HTTPCACHE_ENABLED': True,
                'HTTPCACHE_DIR': f"{self.metadata['slug']}-cache",
        }
        default_settings.update(settings)
        scraper_class.directory = self.directory
        process = scrapy.crawler.CrawlerProcess(default_settings)
        process.crawl(scraper_class, *args_list, **kwargs_dict)
        process.start()

        if self.gzip:
            gzip_file(filepath)


    def jsonlines_to_rdf(self, dict_to_graph_function, jsonl_filename=None, rdf_filename=None):
        '''
        Opens the jsonl file, either the default (slug.jsonl) or the one provided as parameter.
        Calls the provided dict_to_graph_function with a prepared graph and a dict for the
        current record.
        '''
        if not jsonl_filename:
            jsonl_filename = f"{self.metadata['slug']}.jsonl"
        if not rdf_filename:
            rdf_filename = f"{self.metadata['slug']}.ttl"
        if self.gzip and not jsonl_filename.endswith(".gz"):
            jsonl_filename += ".gz" 
        jsonl_filepath = os.path.join(self.directory, jsonl_filename)
        rdf_filepath = os.path.join(self.directory, rdf_filename)
        graph = rdflib.Graph()
        for ns in namespaces:
            graph.bind(ns, namespaces[ns])
        openfunc = open
        if jsonl_filepath.endswith(".gz"):
            openfunc = gzip.open
        with openfunc(jsonl_filepath, "rt", encoding="utf-8") as jsonlines:
            for line in jsonlines:
                line_dict = json.loads(line)
                dict_to_graph_function(graph, line_dict)
        with open(rdf_filepath, "wb") as f:
            f.write(graph.serialize(format="turtle"))
        if self.gzip:
            gzip_file(rdf_filepath)


    def turtle_to_rdf(self, graph_to_graph_function, turtle_filename=None, rdf_filename=None, source_dataset_slug=None):
        '''
        Opens the turtle file, either the default (slug.jsonl) or the one provided as parameter.
        Calls the provided graph_to_graph_function with a prepared graph and a graph for the
        current record.
        '''
        if not turtle_filename:
            turtle_filename = f"{self.metadata['slug']}.ttl"
        if not rdf_filename:
            rdf_filename = f"{self.metadata['slug']}.ttl"
        if turtle_filename==rdf_filename and not source_dataset_slug:
            print("You must explicitly give a different rdf_filename, if you read from the default filename.")
            return
        if self.gzip and not rdf_filename.endswith(".gz"):
            rdf_filename += ".gz" 
        directory = self.directory
        if source_dataset_slug:
            directory = directory.replace(self.metadata['slug'], source_dataset_slug)
        print(f"Directory: {directory}")
        print(f"Source slug: {source_dataset_slug}")
        turtle_filepath = os.path.join(directory, turtle_filename)
        if not os.path.exists(turtle_filepath) and not turtle_filepath.endswith(".gz"):
            turtle_filepath += ".gz"
        rdf_filepath = os.path.join(self.directory, rdf_filename)
        graph = rdflib.Graph()
        for ns in namespaces:
            graph.bind(ns, namespaces[ns])
        openfunc = open
        if turtle_filepath.endswith(".gz"):
            openfunc = gzip.open
        with openfunc(turtle_filepath, "rt", encoding="utf-8") as infile:
            prefixes = []
            datalines = []
            try:
                for line in infile:
                    if "@prefix" in line:
                        prefixes.append(line)
                    elif len(line.strip()) > 0:
                        datalines.append(line)
                    else:
                        if len(datalines) > 0:
                            ingraph = rdflib.Graph()
                            data = "\n".join(prefixes)
                            data += "\n\n"
                            data += "\n".join(datalines)
                            datalines.clear()
                            ingraph.parse(data = data, format="turtle")
                            try:
                                graph_to_graph_function(graph, ingraph)
                            except Exception as e:
                                error.info(f"Exception during RDF generation: {e}")
                                traceback.print_exc()
            except KeyboardInterrupt:
                log.info("User interrupt, writing partial turtle file...")
        with open(rdf_filepath, "wb") as f:
            f.write(graph.serialize(format="turtle"))
        if self.gzip:
            gzip_file(rdf_filepath)


    def create_version(self):
        date_prefix = timezone.now().strftime("%Y-%m-%d-")
        for f in self.metadata["files"]:
            source = os.path.join(self.directory, f['filename'])
            target = os.path.join(self.directory, f"{date_prefix}{f['filename']}")
            shutil.copy(source, target)


    def write_metadata(self, rdf_filename=None, toml_filename=None):
        '''
        Creates toml and ttl metadata files, containing all infos from the provided
        metadata, as well as automatically obtained data, such as git commit, current date, script name, ...
        It also creates the versioned copies of the data, although we might want to make this optional.
        '''
        if not rdf_filename:
            rdf_filename = f"{self.metadata['slug']}-metadata.ttl"
        if not toml_filename:
            toml_filename = f"{self.metadata['slug']}-metadata.toml"
        rdf_filepath = os.path.join(self.directory, rdf_filename)
        toml_filepath = os.path.join(self.directory, toml_filename)
        graph = rdflib.Graph()
        creation_date = timezone.now()
        self.metadata["date"] = creation_date
        try:
            process = subprocess.Popen(['git', 'rev-parse', 'HEAD'], shell=False, stdout=subprocess.PIPE)
            git_head_hash = process.communicate()[0].strip().decode("utf-8")
        except:
            git_head_hash = "Not available"
        scriptinfo = True
        try:
            script = self.__class__.__module__.split(".")[-1] + ".py"
            script_path = settings.LABS_GIT_WEBROOT + self.__class__.__module__.replace(".", "/") + ".py"
        except:
            script = "Not available"
            script_path = "Not available"
            scriptinfo = False

        self.metadata["generator"] = {
            "script": script,
            "gitweb": script_path,
            "commit": git_head_hash,
            }
        # The toml file contains the metadata to be copied to the Hugo page
        with open(toml_filepath, "w", encoding="utf-8") as f:
            toml.dump(self.metadata, f)
        # The ttl file contains the metadata as RDF to be shown in Pubby.
        for ns in namespaces:
            graph.bind(ns, namespaces[ns])
        subject = rdflib.URIRef(f"http://data.judaicalink.org/datasets/{self.metadata['slug']}")
        graph.add((subject, rdf.type, void.Dataset))
        graph.add((subject, dcterms.date, rdflib.Literal(creation_date)))
        graph.add((subject, dcterms.title, rdflib.Literal(self.metadata["title"])))
        if "license" in self.metadata:
            if "uri" in self.metadata["license"]:
                graph.add((subject, cc.license, rdflib.URIRef(self.metadata["license"]["uri"])))
            if "name" in self.metadata["license"]:
                graph.add((subject, dcterms.rights, rdflib.Literal(self.metadata["license"]["name"])))
        if scriptinfo:
            graph.add((subject, rdf.type, prov.Entity))
            activity = rdflib.BNode()
            script = rdflib.BNode()
            graph.add((subject, prov.wasGeneratedBy, activity))
            graph.add((activity, prov.used, script))
            graph.add((script, jlo.gitWeb, rdflib.URIRef(self.metadata["generator"]["gitweb"])))
            graph.add((script, jlo.gitCommit, rdflib.Literal(self.metadata["generator"]["commit"])))
            graph.add((script, rdfs.label, rdflib.Literal(self.metadata["generator"]["script"])))
        with open(rdf_filepath, "wb") as f:
            f.write(graph.serialize(format="turtle"))
        if self.gzip:
            gzip_file(rdf_filepath)
        self.create_version()


    def handle(self, *args, **kwargs):
        print("This command is not meant to be executed directly, use a subclass.")



