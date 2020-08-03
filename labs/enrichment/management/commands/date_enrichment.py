from django.core.management.base import BaseCommand
from django.utils import timezone
import gzip
import rdflib
from backend import models, dataset_loader

class Command(BaseCommand):
    help = 'Create parsed dates from birthDate and deathDate'

    def handle(self, *args, **kwargs):
        # we will collect all strings we are not (yet) able to parse.
        # goal: empty this set ;-)
        unparsed = set() 
        out = rdflib.Graph()
        jl = rdflib.Namespace("http://data.judaicalink.org/ontology/")
        
        # First, we iterate over all data files in our django database
        for df in models.Datafile.objects.all():
            # we use the backend functions to download and access the actual files 
            filename = dataset_loader.load_rdf_file(df.url)
            # we check, if the file is supposed to be RDF
            if df.dataset.is_rdf():
                self.stdout.write(f"Processing: {filename}")
                # we open the file, eiter directly or via gzip.open
                openfunc = open
                if filename.endswith(".gz"):
                    openfunc = gzip.open
                with openfunc(filename, "rt", encoding="utf8") as f:
                    # we load the contents into a graph via rdflib
                    g = rdflib.Graph()
                    g.parse(f, format='n3')
                    # And we are ready to actually do something with the data.
                    # We iterate over all triples (data statements)
                    triples = g.triples((None, None, None))
                    for row in triples:
                        if row[1] == jl.birthDate:
                            date_string = str(row[2])
                            # do your parsing magic...
                            if len(date_string) == 4 and date_string.isnumeric():
                                year = int(date_string)
                                print(year)
                                # create new triple.
                                # Check this: https://rdflib.readthedocs.io/en/stable/rdf_terms.html
                                out.add((row[0], jl.birthYear, rdflib.Literal(year, datatype=rdflib.XSD.integer)))
                            # no magic available? then it is unparsed
                            else:
                                unparsed.add(date_string)

        # write out new datafile
        with open("date_enriched.ttl", "wb") as f:
            f.write(out.serialize(format="turtle"))

        # write out unparsed so that we can have a look
        with open("unparsed_dates.txt", "w") as f:
            for d in unparsed:
                f.write(f"{d}\n")

                
