import requests
from urllib.parse import quote, unquote
from ._dataset_command import DatasetCommand, jlo
import json
import rdflib

metadata = {
        "title": "Translations for Rujen (Google)",
        "example": "http://data.judaicalink.org/data/rujen/ben-gurion",
        "slug": "rujen-translation", # Used as graph name and for file names, identifies this dataset.
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

def translate(text, source_lang, target_lang):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={quote(text)}"
    res = requests.get(url)
    data = json.loads(res.text)
    sentences = []
    for sentence in data[0]:
        if sentence and len(sentence)>0:
            sentences.append(sentence[0])
    return "".join(sentences)

def transform_rdf(graph, ingraph):
    query = f"""
    SELECT ?s ?o WHERE {{?s <{jlo.hasAbstract}> ?o .}} 
            """
    res = ingraph.query(query)
    for triple in res:
        engl = translate(triple["o"], "ru", "en")
        graph.add((triple["s"], jlo.hasAbstract, rdflib.Literal(engl, "en")))
        print(f"Added translation: {triple['s']}")

class Command(DatasetCommand):
    help = 'Translate the Rujen encyclopedia'

    def handle(self, *args, **options):
        self.set_metadata(metadata)
        self.turtle_to_rdf(transform_rdf, turtle_filename="rujen.ttl", source_dataset_slug="rujen")


