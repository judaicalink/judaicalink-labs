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
from urllib.parse import quote, unquote
from ._dataset_command import DatasetCommand, DatasetSpider, log, error
from ._dataset_command import jlo, jld, skos, dcterms, void, foaf, rdf

## Step by step instructions

# First: create the necessary metadata for the new dataset.
# Most importantly define the "slug", as this is used to determine
# the folder for the files and the default filenames.
metadata = {
        "title": "Encyclopedia of Russian Jewry",
        "example": "http://data.judaicalink.org/data/rujen/ben-gurion",
        "slug": "rujen", # Used as graph name and for file names, identifies this dataset.
        "namespace_slugs": [
            "rujen"
            ],
        "creators": [
            {"name": "Kai Eckert", "url": "http://wiss.iuk.hdm-stuttgart.de/people/kai-eckert"}
            ],
        "license": {
            "name": "CC0",
            "image": "https://mirrors.creativecommons.org/presskit/buttons/88x31/png/cc-zero.png",
            "uri": "https://creativecommons.org/publicdomain/zero/1.0/",
            }
        }


# In case you want to scrape data, you have to implement a scraper class.
# Check Scrapy docs for details.
# Note: As demonstrated, you can use BeautifulSoup for the actual extractio.
# Scrapy has its own extraction tools, of course you can use them, too.
class Spider(DatasetSpider):
    name = metadata['slug'] # Used for the file name: {name}.jsonl
    start_urls = [
            # All pages
            'http://rujen.ru/index.php/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:AllPages/%D0%90%D0%91%D0%90%D0%97%D0%9E%D0%92%D0%9A%D0%90',
            # Locations
            # 'http://rujen.ru/index.php/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%93%D0%B5%D0%BE%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D1%8F',
            # Persons
            # 'http://rujen.ru/index.php/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%9F%D0%B5%D1%80%D1%81%D0%BE%D0%BD%D0%B0%D0%BB%D0%B8%D0%B8',
            ]

    def lower_case(self, url):
        return quote(unquote(url.replace("http://rujen.ru", "")).lower())

    # Cheatsheet
    # soup = BeautifulSoup(HTMLSTRING, 'html.parser')
    # soup.h2.string # First H2
    # table = soup.select_one('table.myclass') # first by CSS Selector
    # tds = table.select('td.datacell') # all by CSS Selector
    # table.find_all("tr") # select all tr tags
    # tr.find("th").text.strip() # Find first Tag
    def parse(self, response: scrapy.http.Response):
        if "Служебная:Вход" in unquote(response.url):
            log.info("Login page, skipping")
            return None
        log.info(f"Processing {response.url}")
        # We get our soup.
        soup = BeautifulSoup(response.text, 'html.parser')
        # We create an empty dictionary to store all data about this page.
        data = {}

        if "AllPages" in response.url or "Все_страницы" in unquote(response.url):
            log.info("Processing index page")
            for a in soup.select("div.mw-allpages-nav a"):
                h = a["href"]
                if self.check_queue(h):
                    log.info(f"New index page: {a['href']}")
                    yield response.follow(h)
            for a in soup.select(".mw-allpages-chunk li a"):
                h = self.lower_case(a["href"])
                if self.check_queue(h):
                    log.info(f"New page: {a['href']}")
                    yield response.follow(h)
            return None

        data['uri'] = self.lower_case(response.url)
        log.info(f"Processing {data['uri']}")
        if response.status == 404:
            log.info(f"Page not found: {response.url}")
            return data
        try: # "wgArticleId":9907
            data['id'] = re.search(r'"wgArticleId":([0-9]+),', soup.head.get_text()).group(1)
        except Exception as e:
            log.info(f"Error getting ID ({data['uri']}): {e}")
            error.info(f"Error getting ID ({data['uri']}): {e}")
            # return {}

        # Basic stuff
        data['title'] = soup.select_one("h1.firstHeading").text.strip()
        abstract = soup.select_one("#mw-content-text p")
        if abstract:
            data['abstract'] = abstract.get_text().replace("\n", "").strip()
        else:
            error.info(f"No abstract: {response.url}")
	# Links
        data["links"] = []
        for a in soup.select("#mw-content-text p a"):
            link = {}
            h = self.lower_case(a['href'].replace('&action=edit&redlink=1','').replace('?title=','/'))
            link["href"] = h
            link["text"] = a.text.strip()
            if len(link["text"])>0: # Strangely, there are sometimes empty links
                data["links"].append(link)
                if self.check_queue(h):
                    yield response.follow(h)

        #Category
        data["categories"] = []
        for a in soup.select("#mw-normal-catlinks ul li a"):
            data["categories"].append(a.text.strip())


        # Here we yield the data of this page.
        yield data



latinUTF8Substitution = ["a", "b", "v", "g", "d", "e", "zh", "z", "i",
"y", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "kh", "ts",
"ch", "sh", "shch", "j", "y", "j", "e", "yu", "ya", "e", "e"]
UTF8TableBeginning = 1072;

def get_latin_string(cyrillicString):
    result = "";
    input = cyrillicString.lower()
    for index, char in enumerate(input):
        charCodeDec = ord(char)-UTF8TableBeginning
        if (charCodeDec>=0 and charCodeDec<34):
            result += latinUTF8Substitution[charCodeDec]
        else:
            result += char
    return result


def local(uri):
    if "index.php" in uri:
        slug = get_latin_string(unquote(uri).replace("/index.php/", ""))
        return jld[f"rujen/{slug}"] 
    else:
        return rdflib.URIRef(uri)


# This is a function that is called for each dictionary that 
# we created with the crawler. All triples are collected in the
# graph that is provided.
# So no worries here about filenames, file formats and so on...
def create_rdf(graph: rdflib.Graph, resource_dict: dict):
    subject = local(resource_dict["uri"])
    log.info(f"Generating RDF for {subject}")
    graph.add((subject, rdf.type, skos.Concept))
    graph.add((subject, skos.prefLabel, rdflib.Literal(resource_dict["title"])))
    graph.add((subject, jlo.describedAt, rdflib.URIRef(f"http://rujen.ru/index.php/{resource_dict['uri']}")))
    identifier = unquote(resource_dict["uri"].replace("/index.php/", ""))
    graph.add((subject, dcterms.identifier, rdflib.Literal(identifier)))
    for l in resource_dict["links"]:	
            graph.add((subject, skos.related, local(l["href"])))
            if len(l["text"])>0:
                graph.add((local(l["href"]), skos.altLabel, rdflib.Literal(l["text"])))
    if "categories" in resource_dict:
        for cat in resource_dict["categories"]:
            if cat=="Персоналии":
                graph.add((subject, rdf.type, jlo.Person))
            elif cat=="География":
                graph.add((subject, rdf.type, jlo.Place))
            else:
                error.info("Unknown category: " + cat)
    if "abstract" in resource_dict:
        graph.add((subject, jlo.hasAbstract, rdflib.Literal(resource_dict["abstract"], "ru")))
        referTo = re.search(r"^(.+), см\. (\S+)\.$", resource_dict["abstract"])
        if referTo:
            source = referTo.group(1)
            target = referTo.group(2)
            log.info(f"Refer to detected {source} to {target}")
            targetCheck = False
            if "links" in resource_dict:
                for link in resource_dict["links"]:
                    if f"/{unquote(target).lower()}" in unquote(link["href"]).lower():
                        targetCheck = link["href"]
            sourceCheck = identifier==source.lower().replace(" ", "_")
            if not sourceCheck or not targetCheck:
                    error.info(f"{source} -> {target} ({identifier}<>{source.lower().replace(' ', '_')}) ({targetCheck})") 
            else:
                    graph.add((subject, jlo.referTo, local(targetCheck)))
    else:
        graph.add((subject, skos.scopeNote, rdflib.Literal("The article describing this concept does not (yet) exist in the encyclopedia.", "en")))
    return graph

# The actual command. It inherits from DatasetCommand, where
# all the magic happens. Here, we can therefore keep it simple.
class Command(DatasetCommand):
    help = 'Generate the Rujen dataset from the online encyclopedia'

    def handle(self, *args, **options):
        # First, check if --gzip was given as parameter and set the 
        # gzip variable accordingly. This affects a lot, especially the
        # filenames that are produced.
        self.gzip = options['gzip']
        # Next, set your metadata. This is absolutely required, without this,
        # your command will not work, as it needs the information, e.g. to 
        # determine from the slug where the files have to be stored.
        self.set_metadata(metadata)

        # Check the parameters to skip parts if desired by the user.
        if not options["skip_scraping"]:
            # This is a wrapper around Scrapy, you can actually just
            # call start_scraper just with your class, but as you can see,
            # it is possible to set various Scrapy configurations as 
            # well, if desired.
            self.start_scraper(Spider, settings={"LOG_LEVEL": "INFO", "HTTPERROR_ALLOWED_CODES": [404]})
        if not options["no_rdf"]:
            # This is a helper function that calls the function you provide for each line in a jsonl file.
            # If you do not have jsonl as original format, it probably makes sense to create additional
            # helpers, e.g. to walk through an RDF file or a common JSON file. Discuss with the team if this is
            # needed, so that we get a common infrastructure.
            self.jsonlines_to_rdf(create_rdf) 

            # This adds a file to the metadata. Note that you only give the filename here, without .gz. Everyting
            # else, like a directory path and gzipping is taken care of by DatasetCommand.
            # All files not in the metadata are considered temporal files. Feed free to also add jsonl-Files or any
            # other files here, if you want to make them part of the dataset.
            self.add_file("rujen.ttl")
        # This finally writes the metadata of the new dataset and takes care of versioning.
        # Check yivo.toml to see metadata in our Hugo format, ready to be copied into the Hugo description.
        self.write_metadata()



