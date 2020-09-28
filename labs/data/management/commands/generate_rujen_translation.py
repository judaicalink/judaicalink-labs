import requests
from urllib.parse import quote, unquote
from ._dataset_command import DatasetCommand, jlo, log, error
import json
import rdflib
from googletrans import Translator
import os
import csv

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
    '''
    This quickly gets banned by Google and is just for demonstration.
    Use googletrans for better results.
    '''
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={quote(text)}"
    res = requests.get(url)
    data = json.loads(res.text)
    sentences = []
    for sentence in data[0]:
        if sentence and len(sentence)>0:
            sentences.append(sentence[0])
    return "".join(sentences)

translator = Translator()
engl_cachefile = None
engl_cached = {}

def transform_rdf(graph, ingraph):
    query = f"""
    SELECT ?s ?o WHERE {{?s <{jlo.hasAbstract}> ?o .}} 
            """
    res = ingraph.query(query)
    for triple in res:
        # engl = translate(triple["o"], "ru", "en")
        s = str(triple["s"])
        if s in engl_cached:
            engl = engl_cached[s].strip()
            log.info(f"Added translation (cached): {s}: {engl[:20]}")
        else:
            engl = translator.translate(triple["o"], src="ru", dest="en").text.strip()
            engl_cached[s] = engl
            log.info(f"Added translation: {s}: {engl[:20]}")
        graph.add((triple["s"], jlo.hasAbstract, rdflib.Literal(engl, "en")))

class Command(DatasetCommand):
    help = 'Translate the Rujen encyclopedia'

    def handle(self, *args, **options):
        self.set_metadata(metadata)
        engl_cachefile = os.path.join(self.directory, "engl_cache.csv")
        if os.path.exists(engl_cachefile):
            with open(engl_cachefile, "r", encoding="utf-8") as f:
                for row in csv.reader(f):
                    engl_cached[row[0]] = row[1]
        log.info(f"Cache populated with {len(engl_cached)} entries.")
        try:
            self.turtle_to_rdf(transform_rdf, turtle_filename="rujen.ttl", source_dataset_slug="rujen")
        except KeyboardInterrupt:
            log.info("User interrupt, finishing...")
        with open(engl_cachefile, "w", encoding="utf-8") as f:
            writer = csv.writer(f)
            for s in engl_cached:
                writer.writerow((s, engl_cached[s]))
        self.add_file("engl_cache.csv")
        self.write_metadata()


