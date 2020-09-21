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


class YivoSpider(scrapy.Spider):
    name = 'yivo Spider'
    start_urls = ["https://yivoencyclopedia.org/article.aspx/Abeles_Shimon"]

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}
        data["title"] = soup.h1.string
        data["next_article"] = soup.select_one('#ctl00_placeHolderMain_linkNextArticle')['href']
        yield data
        yield response.follow(data["next_article"])

class Command(BaseCommand):
    help = 'Generate the Yivo dataset from the online encyclopedia'

    def handle(self, *args, **kwargs):
        first = "https://yivoencyclopedia.org/article.aspx/Abeles_Shimon"
        spider = YivoSpider()
        spider.start_urls = [first]
        process = scrapy.crawler.CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'FEED_FORMAT': 'json',
            'FEED_URI': 'yivo_webscraping.json'
            #'FEED': { Path('yivo_webscraping.json'): { 'format': 'jsonlines', 'encoding': 'utf-8'} },
            # 'LOG_LEVEL': 'WARNING'
        })
        process.crawl(YivoSpider, start_urls=[first])
        process.start()



        out = rdflib.Graph()
        records = []

        jl = rdflib.Namespace("http://data.judaicalink.org/ontology/")
        

        # write out new datafile
        with open("yivo_webscraping.ttl", "wb") as f:
            f.write(out.serialize(format="turtle"))


                
