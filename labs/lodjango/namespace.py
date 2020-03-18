namespaces = {
    'skos': 'http://www.w3.org/2004/02/skos/core#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dcterms': 'http://purl.org/dc/terms/',
    'jld': 'http://data.judaicalink.org/data/',
    'jlo': 'http://data.judaicalink.org/ontology/',
    'owl': 'http://www.w3.org/2002/07/owl#',
        }

def uri(ns, name):
    return "{}{}".format(namespaces[ns],name)
