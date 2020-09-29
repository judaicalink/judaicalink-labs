import requests
from urllib.parse import quote, unquote
from ._dataset_command import DatasetCommand, jlo, skos, log, error
import json
import rdflib
from googletrans import Translator
import os
import csv
import re

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
trans_cached = {}
src_lang = "ru"

def configure_task(task):
    global cachefile, outfile, dest_lang, prop
    if task=="en-label":
        cachefile = "en_label_cache.csv"
        outfile = "rujen-en-label-translations.ttl"
        dest_lang = "en"
        prop = skos.prefLabel
    elif task=="en-abstract":
        cachefile = "en_abstract_cache.csv"
        outfile = "rujen-en-abstract-translations.ttl"
        dest_lang = "en"
        prop = jlo.hasAbstract
    elif task=="de-label":
        cachefile = "de_label_cache.csv"
        outfile = "rujen-de-label-translations.ttl"
        dest_lang = "de"
        prop = skos.prefLabel
    elif task=="de-abstract":
        cachefile = "de_abstract_cache.csv"
        outfile = "rujen-de-abstract-translations.ttl"
        dest_lang = "de"
        prop = jlo.hasAbstract


def transform_rdf(graph, ingraph):
    global translator
    query = "SELECT ?s ?o WHERE {?s <" + str(prop) + "> ?o .}"
    res = ingraph.query(query)
    for triple in res:
        s = str(triple["s"])
        if s in trans_cached:
            trans = trans_cached[s].strip()
            log.info(f"Added translation (cached): {s}: {trans[:20]}")
        else:
            trans = translator.translate(triple["o"], src=src_lang, dest=dest_lang)
            log.info(f"Added translation: {s}: {trans.text.strip()[:20]} {trans.src} - {trans.dest}")
            if trans.src=="ru" and re.search('[а-яА-Я]', trans.text.strip()):
                error.info(f"Cyrillic in translation: {s}")
            if trans.src=="ru":
                trans_cached[s] = trans.text.strip()
                trans = trans.text.strip()
            else:
                log.info("Translation does not work anymore, getting no translation. I use a new instance.")
                translator = Translator()
        graph.add((triple["s"], prop, rdflib.Literal(trans, dest_lang)))

class Command(DatasetCommand):
    help = 'Translate the Rujen encyclopedia'

    def handle(self, *args, **options):
        self.set_metadata(metadata)

        for task in ["en-abstract", "en-label", "de-abstract", "de-label"]:
            log.info(f"Starting task {task}")
            configure_task(task)
            trans_cached.clear()
            cachefile_path = os.path.join(self.directory, cachefile)
            if os.path.exists(cachefile_path):
                with open(cachefile_path, "r", encoding="utf-8") as f:
                    for row in csv.reader(f):
                        trans_cached[row[0]] = row[1]
            log.info(f"Cache populated with {len(trans_cached)} entries.")
            try:
                self.turtle_to_rdf(transform_rdf, turtle_filename="rujen.ttl", source_dataset_slug="rujen", rdf_filename=outfile)
            except KeyboardInterrupt:
                log.info("User interrupt, finishing...")
            with open(cachefile_path, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                for s in trans_cached:
                    writer.writerow((s, trans_cached[s]))
            self.add_file(cachefile)
            self.add_file(outfile)
        
        self.write_metadata()


