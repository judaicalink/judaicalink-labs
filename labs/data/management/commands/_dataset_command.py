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

for ns in namespaces:
    exec(f"{ns} = namespaces['{ns}']")


def gzip_file(filename):
    with open(filename, 'rb') as f_in:
        with gzip.open(f'{filename}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(filename)


class DatasetSpider(scrapy.Spider):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)


    def log(self, message):
        print(f"Log: {message}")
        logfile = os.path.join(self.__class__.directory, "log.txt")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")


    def error(self, message):
        print(f"Error: {message}")
        logfile = os.path.join(self.__class__.directory, "error.txt")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")


class DatasetCommand(BaseCommand):
    help = 'Base Command for a scraper'

    
    def __init__(self):
        super().__init__()
        self.gzip = False


    def log(self, message):
        print(f"Log: {message}")
        logfile = os.path.join(self.directory, "log.txt")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")


    def error(self, message):
        print(f"Error: {message}")
        logfile = os.path.join(self.directory, "error.txt")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")


    def add_arguments(self, parser):
        parser.add_argument("--clear-cache", action="store_true", help="Clear cache before scraping.")
        parser.add_argument("--skip-scraping", action="store_true", help="Create RDF from JSON.")
        parser.add_argument("--no-rdf", action="store_true", help="Create only json")
        parser.add_argument("--gzip", action="store_true", help="Zip output files.")


    def set_metadata(self, metadata):
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


    def add_file(self, filename, description = None):
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


    def create_version(self):
        date_prefix = timezone.now().strftime("%Y-%m-%d-")
        for f in self.metadata["files"]:
            source = os.path.join(self.directory, f['filename'])
            target = os.path.join(self.directory, f"{date_prefix}{f['filename']}")
            shutil.copy(source, target)


    def write_metadata(self, rdf_filename=None, toml_filename=None):
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



