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
        "title": "Yivo Encyclopedia",
        "example": "http://data.judaicalink.org/data/yivo/Moscow",
        "slug": "yivo", # Used as graph name and for file names, identifies this dataset.
        "namespace_slugs": [
            "yivo"
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
class YivoSpider(DatasetSpider):
    name = metadata['slug'] # Used for the file name: {name}.jsonl
    start_urls = ['https://yivoencyclopedia.org/article.aspx/Abeles_Shimon']

    def check_queue(self, url):
        url = url[url.find("article.aspx"):]
        return super().check_queue(url)

    # Cheatsheet
    # soup = BeautifulSoup(HTMLSTRING, 'html.parser')
    # soup.h2.string # First H2
    # table = soup.select_one('table.myclass') # first by CSS Selector
    # tds = table.select('td.datacell') # all by CSS Selector
    # table.find_all("tr") # select all tr tags
    # tr.find("th").text.strip() # Find first Tag
    def parse(self, response: scrapy.http.Response):
        # We get our soup.
        soup = BeautifulSoup(response.text, 'html.parser')
        # We create an empty dictionary to store all data about this page.
        data = {}
        data['title'] = soup.h1.string
        data['uri'] = response.url.replace(":443", "")
        log.info(f"Processing {data['uri']}")
        try:
            href = soup.select_one("#ctl00_placeHolderMain_linkEmailArticle")["href"]
            data['id'] = re.search(r"id=([0-9]+)", href).group(1)
        except Exception as e:
            log.info(f"Error ({data['uri']}): {e}")
            error.info("Error ({data['uri']}): {e}")
            return None
       
        url_path = data['uri'][data['uri'].find("article.aspx"):]
        if url_path in self.visited:
            return None
        # Mark as visited
        self.visited.add(url_path)
        self.visited.add(f"article.aspx?id={data['id']}")

        # Basic stuff
        data['abstract'] = soup.select_one(".articleblockconteiner p").text

        # Images
        data['images'] = []
        for img in soup.select("img.mbimg"): 
            image = {}
            image["thumbUrl"] = f"http://www.yivoencyclopedia.org{img['src']}"
            href = img.parent["href"]
            image["viewerUrl"] = re.search(r"(http.*)&article", href).group(0)
            caption = img.parent.find_next_sibling("div")
            if caption:
                image["imgDesc"] = caption.text.replace("SEE MEDIA RELATED TO THIS ARTICLE","").strip()
            data['images'].append(image)

        # Links
        data['links'] = []
        for a in soup.select(f"#ctl00_placeHolderMain_panelArticleText a[href^='article.aspx/']"): 
            link = {}
            link["href"] = f"http://www.yivoencyclopedia.org/{a['href']}"
            link["text"] = a.text.strip()
            if len(link["text"]) > 0: # Strangely, there are sometimes empty links
                data['links'].append(link) 
                # With yield, we can either return a new URL to be crawled
                # or the final data.
                if self.check_queue(link['href']):
                    yield response.follow(link["href"])

        # Glossary terms
        data['glossary'] = []
        for span in soup.select(".term"):
            term = span.text.strip()
            if len(term)>0: # Strangely, there are sometimes empty spans
                data['glossary'].append(term)

        # Subrecords, i.e., multi-page articles (like Poland)
        data['subrecords'] = []
        isMain = True
        for index, a in enumerate(soup.select("#ctl00_placeHolderMain_panelPager a")):
            sr = {}
            sr["href"] = f"http://www.yivoencyclopedia.org" + a["href"]
            sr["page"] = a.text.strip()
            if index==0 and sr["href"]!=data['uri']:
                isMain = False
            if not isMain and index==0:
                data['parent'] = sr["href"]
                if self.check_queue(sr['href']):
                    yield response.follow(sr["href"])
            if isMain and index != 0:
                data['subrecords'].append(sr)
                if self.check_queue(sr['href']):
                    yield response.follow(sr["href"])

        # Subconcepts, i.e., H2 headings on the same page (not really a concept, but maybe useful)
        data['subconcepts'] = []
        for index, h2 in enumerate(soup.select("h2.entry")):
            sc = h2.text.strip()
            if index==0 and not isMain:
                data['title'] = f"{sc} ({data['title']})"
                break
            # The following H2 headings are NOT stored as concepts:
            stops = ["About this Article", "Suggested Reading", "YIVO Archival Resources", "Author", "Translation"]
            if sc in stops:
                break
            data['subconcepts'].append(sc)

        # Next record in alphabet
        next_article = soup.select_one('#ctl00_placeHolderMain_linkNextArticle')
        if next_article:
            data['next_article'] = next_article['href']

        # Here we yield the data of this page.
        yield data
        if next_article and self.check_queue(data['next_article']):
            yield response.follow(data['next_article'])


replacements = {
        "ł": "l",
        }

disallowed_chars = re.compile(r"[^a-z0-9:/.-_]")
multiple_underscores = re.compile(r"_{2,}")

def enforce_valid_characters(uri):
    # Unquote until no further unquoting is possible
    last = uri
    unquoted = unquote(last)
    while last != unquoted:
        last = unquoted
        unquoted = unquote(last)
    # Make sure we only use lower case
    lowered = unquoted.lower()
    # replace characters with readable latin characters, if desired.
    for char in replacements:
        lowered = lowered.replace(char, replacements[char])
    # Final replacements, disallowed chars are replaces by a single underscore 
    final = disallowed_chars.sub("_", lowered)
    # Multiple underscores are reduced to one
    final = multiple_underscores.sub("_", final)
    # And no underscore at the end.
    final = final.strip("_")
    if final != uri:
        # Make sure to check the log to see if these rules are ok
        log.info(f"Enforced URI: {uri} -> {final}")
    return final




# Helper function to convert Yivo URLs to our data URIs.
# In this case, it uses the jld namespace and add yivo and
# then the remainder of the URL after aspx/
def local(uri):
    if "article.aspx" in uri:
        uri = f"http://data.judaicalink.org/data/yivo/{uri[uri.find('aspx/') + 5:]}".lower()
    return rdflib.URIRef(enforce_valid_characters(uri))


# This is a function that is called for each dictionary that 
# we created with the crawler. All triples are collected in the
# graph that is provided.
# So no worries here about filenames, file formats and so on...
def yivo_rdf(graph: rdflib.Graph, resource_dict: dict):
    subject = local(resource_dict["uri"])
    graph.add((subject, jlo.title, rdflib.Literal(resource_dict['title'])))
    graph.add((subject, jlo.describedAt, rdflib.URIRef(resource_dict["uri"])))
    graph.add((subject, skos.prefLabel, rdflib.Literal(resource_dict["title"])))
    for l in resource_dict["links"]:	
            graph.add((subject, skos.related, local(l["href"])))
            if len(l["text"])>0:
                graph.add((local(l["href"]), skos.altLabel, rdflib.Literal(l["text"])))
    graph.add((subject, jlo.hasAbstract, rdflib.Literal(resource_dict["abstract"], "en")))
    for sc in resource_dict["subconcepts"]:
            scu = local(str(subject) + "/" + sc)
            graph.add((scu, rdf.type, skos.Concept))
            graph.add((scu, skos.broader, subject))
            graph.add((scu, skos.prefLabel, rdflib.Literal(sc)))
            graph.add((subject, skos.narrower, scu))
    for sr in resource_dict["subrecords"]:
            graph.add((subject, skos.narrower, local(sr.href)))
    if "broader" in resource_dict:
            graph.add((subject, skos.broader, rdflib.URIRef(resource_dict["broader"])))
    return graph

# The actual command. It inherits from DatasetCommand, where
# all the magic happens. Here, we can therefore keep it simple.
class Command(DatasetCommand):
    help = 'Generate the Yivo dataset from the online encyclopedia'

    def handle(self, *args, **options):
        # First, check if --gzip was given as parameter and set the 
        # gzip variable accordingly. This affects a lot, especially the
        # filenames that are produced.
        self.gzip = options['gzip']
        # Next, set your metadata. This is absolutely required, without this,
        # your command will not work, as it needs the information, e.g. to 
        # determine from the slug where the files have to be stored.
        self.set_metadata(metadata)

        # These are various test cases in yivo to quickly check if a certain
        # URL is correctly extracted. Usually you start with first, of course.
        # They are lists, because Scrapy expects a list of start_urls.
        first = ['https://yivoencyclopedia.org/article.aspx/Abeles_Shimon']
        last = ['https://yivoencyclopedia.org/article.aspx/Zylbercweig_Zalmen']
        multi = ['https://yivoencyclopedia.org/article.aspx/Poland']
        error = ['https://yivoencyclopedia.org/article.aspx?id=497']
        sub = ['https://yivoencyclopedia.org/article.aspx/Poland/Poland_before_1795']

        # Check the parameters to skip parts if desired by the user.
        if not options["skip_scraping"]:
            # This is a wrapper around Scrapy, you can actually just
            # call start_scraper just with your class, but as you can see,
            # it is possible to set various Scrapy configurations as 
            # well, if desired.
            self.start_scraper(YivoSpider, settings={"LOG_LEVEL": "INFO"}, kwargs_dict={"start_urls": first})
        if not options["no_rdf"]:
            # This is a helper function that calls the function you provide for each line in a jsonl file.
            # If you do not have jsonl as original format, it probably makes sense to create additional
            # helpers, e.g. to walk through an RDF file or a common JSON file. Discuss with the team if this is
            # needed, so that we get a common infrastructure.
            self.jsonlines_to_rdf(yivo_rdf) 

            # This adds a file to the metadata. Note that you only give the filename here, without .gz. Everyting
            # else, like a directory path and gzipping is taken care of by DatasetCommand.
            # All files not in the metadata are considered temporal files. Feed free to also add jsonl-Files or any
            # other files here, if you want to make them part of the dataset.
            self.add_file("yivo.ttl")
        # This finally writes the metadata of the new dataset and takes care of versioning.
        # Check yivo.toml to see metadata in our Hugo format, ready to be copied into the Hugo description.
        self.write_metadata()



