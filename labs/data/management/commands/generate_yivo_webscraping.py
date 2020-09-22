from django.core.management.base import BaseCommand
from django.utils import timezone
import gzip
import rdflib
from bs4 import BeautifulSoup
from pathlib import Path
import scrapy
import scrapy.crawler
# soup = BeautifulSoup(HTMLSTRING, 'html.parser')
# soup.h2.string # First H2
# table = soup.select_one('table.myclass') # first by CSS Selector
# table.find_all("tr") # select all tr tags
# tr.find("th").text.strip() # Find first Tag
import re
from ._scraper_command import ScraperCommand


class YivoSpider(scrapy.Spider):
    name = 'yivo'
    start_urls = ["https://yivoencyclopedia.org/article.aspx/Abeles_Shimon"]

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}
        data["title"] = soup.h1.string
        data["next_article"] = soup.select_one('#ctl00_placeHolderMain_linkNextArticle')['href']
        yield data
        yield response.follow(data["next_article"])

class Command(ScraperCommand):
    help = 'Generate the Yivo dataset from the online encyclopedia'

    def handle(self, *args, **options):
        first = ["https://yivoencyclopedia.org/article.aspx/Abeles_Shimon"]
        last = ["http://www.yivoencyclopedia.org/article.aspx/Zylbercweig_Zalmen"]
        multi = ["http://www.yivoencyclopedia.org/article.aspx/Poland"]
        error = ["http://www.yivoencyclopedia.org/article.aspx?id=497"]
        sub = ["http://www.yivoencyclopedia.org/article.aspx/Poland/Poland_before_1795"]
        self.start_scraper(YivoSpider, gzip=options['gzip'], kwargs_dict={"start_urls": first})



        out = rdflib.Graph()
        records = []

        jl = rdflib.Namespace("http://data.judaicalink.org/ontology/")
        

        # write out new datafile
        with open("yivo_webscraping.ttl", "wb") as f:
            f.write(out.serialize(format="turtle"))


                
