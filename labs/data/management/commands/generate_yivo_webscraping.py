from django.core.management.base import BaseCommand
from django.utils import timezone
import gzip
import rdflib
from bs4 import BeautifulSoup
from pathlib import Path
import scrapy
import scrapy.crawler
import scrapy.http
import re
from ._dataset_command import DatasetCommand
from ._dataset_command import jlo, jld, skos, dcterms, void, foaf

metadata = {
        "name": "yivo", # Used as graph name and for file names, identifies this dataset.
        "namespace_slugs": [
            "yivo"
            ],
        "creators": [
            {"name": "Kai Eckert", "url": "http://wiss.iuk.hdm-stuttgart.de/people/kai-eckert"}
            ]
        }


class YivoSpider(scrapy.Spider):
    name = metadata["name"] # Used for the file name: {name}.jsonl
    start_urls = ["https://yivoencyclopedia.org/article.aspx/Abeles_Shimon"]

    # Cheatsheet
    # soup = BeautifulSoup(HTMLSTRING, 'html.parser')
    # soup.h2.string # First H2
    # table = soup.select_one('table.myclass') # first by CSS Selector
    # table.find_all("tr") # select all tr tags
    # tr.find("th").text.strip() # Find first Tag
    def parse(self, response: scrapy.http.Response):
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}
        data["title"] = soup.h1.string
        data["uri"] = response.url
        data["next_article"] = soup.select_one('#ctl00_placeHolderMain_linkNextArticle')['href']
        yield data
        yield response.follow(data["next_article"])


def yivo_rdf(graph: rdflib.Graph, resource_dict: dict):
    subject = jld[f"yivo/{resource_dict['uri'][resource_dict['uri'].rfind('/') + 1:]}"] 
    graph.add((subject, jlo.title, rdflib.Literal(resource_dict['title'])))
    return graph


class Command(DatasetCommand):
    help = 'Generate the Yivo dataset from the online encyclopedia'

    def handle(self, *args, **options):
        self.set_metadata(metadata)
        first = ["http://www.yivoencyclopedia.org/article.aspx/Abeles_Shimon"]
        last = ["http://www.yivoencyclopedia.org/article.aspx/Zylbercweig_Zalmen"]
        multi = ["http://www.yivoencyclopedia.org/article.aspx/Poland"]
        error = ["http://www.yivoencyclopedia.org/article.aspx?id=497"]
        sub = ["http://www.yivoencyclopedia.org/article.aspx/Poland/Poland_before_1795"]

        self.start_scraper(YivoSpider, gzip=options['gzip'], kwargs_dict={"start_urls": first})
        self.jsonlines_to_rdf(yivo_rdf, gzip=options['gzip'])



