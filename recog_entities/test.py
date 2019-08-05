#from rdflib.graph import ConjunctiveGraph as Graph
from rdflib.store import Store
from rdflib.plugin import get as plugin
from sqlalchemy.orm import sessionmaker
import spacy
from models import *
import sqlalchemy as db
import rdflib
from rdflib.graph import ConjunctiveGraph as Graph
from rdflib import URIRef, RDFS, Literal, RDF
Virtuoso = plugin("Virtuoso", Store)
store=Virtuoso('DRIVER=/usr/local/virtuoso-opensource/lib/virtodbcu_r.so;Address=localhost:1111;Locale=en.UTF-8;UID=dba;PWD=dba')
#store = Virtuoso("DSN=VOS;UID=dba;PWD=dba;WideAsUTF16=Y")
default_graph_uri = "http://www.sbc.org/project/"
graph = Graph(store, identifier = URIRef(default_graph_uri))
engine = db.create_engine('sqlite:///corruption.sqlite')
context_id = 1
Base.metadata.create_all(engine)
# DB connection
Session = sessionmaker(bind=engine)
session = Session()

def clean_uri(uri):
    if uri.find('#') != -1:
        special_char = '#'
    else:
        special_char = '/'
    index = uri.rfind(special_char)
    return uri[index + 1:len(uri)]


keywords = []
links = []
cont_key = {}
resources = session.query(Resource).filter(
    Resource.context_id == context_id, Resource.potential == False)
for res in resources:
    #print(res.name)
#print ("Triples in graph before add: ", len(graph))
    for s, p, o in graph.triples((None, None, Literal(res.name))):
        #print(s, p , o)
        keywords.append(res.name)
        links.append(s)
        for s2, p2, o2 in graph.triples((s, RDF.type, None)):
            # print(s2, p2, o2)
            cont_key.update({res.name: clean_uri(o2)})

list_sentences = []


print(keywords)
print(links)



