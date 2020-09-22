from django.core.management.base import BaseCommand
from django.utils import timezone
import gzip
import rdflib
from bs4 import BeautifulSoup
from pathlib import Path
import scrapy
import scrapy.crawler
import re
import gzip as gziplib
import shutil
import os



class ScraperCommand(BaseCommand):
    help = 'Base Command for a scraper'

    def add_arguments(self, parser):
        parser.add_argument("--clear-cache", action="store_true", help="Clear cache before scraping.")
        parser.add_argument("--skip-scraping", action="store_true", help="Create RDF from JSON.")
        parser.add_argument("--no-rdf", action="store_true", help="Create only json")
        parser.add_argument("--gzip", action="store_true", help="Zip output files.")

    def start_scraper(self, scraper_class, gzip=False, settings={}, args_list=[], kwargs_dict={}):
        default_settings = {
                'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
                'FEED_FORMAT': 'jsonlines',
                'FEED_URI': f'{scraper_class.name}.json',
                'HTTPCACHE_ENABLED': True,
                'HTTPCACHE_DIR': f'{scraper_class.name}-cache',
        }
        default_settings.update(settings)
        process = scrapy.crawler.CrawlerProcess(default_settings)
        process.crawl(scraper_class, *args_list, **kwargs_dict)
        process.start()

        if gzip:
            with open(f'{scraper_class.name}.json', 'rb') as f_in:
                with gziplib.open(f'{scraper_class.name}.json.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(f'{scraper_class.name}.json')
    
        # out = rdflib.Graph()
        # records = []

        # jl = rdflib.Namespace("http://data.judaicalink.org/ontology/")


        # # write out new datafile
        # with open("yivo_webscraping.ttl", "wb") as f:
        #     f.write(out.serialize(format="turtle"))




    def handle(self, *args, **kwargs):
        print("This command is not meant to be executed directly, use a subclass.")



