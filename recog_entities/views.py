# Create your views here
from django.shortcuts import render, render_to_response, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from collections import OrderedDict
import rdflib
import os
from rdflib.graph import ConjunctiveGraph as Graph
from rdflib.store import Store
from rdflib.plugin import get as plugin
from rdflib import URIRef, RDFS, Literal, RDF
import spacy # spacy
import es_core_news_sm # importación del componente de spacy en español


# Se especifica a rdflib que se va a trabajar con virtuoso
Virtuoso = plugin("Virtuoso", Store)
# Se establece el conector de virtuoso DRIVER, ADDRESS, LOCALE, UID, PWD
store = Virtuoso('DRIVER=/usr/local/virtuoso-opensource/lib/virtodbcu_r.so;Address=localhost:1111;Locale=en.UTF-8;UID=dba;PWD=dba')
# Se especifica el grafo por defecto a realizar la consulta
default_graph_uri = "http://www.sbc.org/projectsbc"
# Se realiza la conexi&oacute;n con rdflib a virutoso
graph = Graph(store, identifier = URIRef(default_graph_uri))

# Asignación de spacy en idioma español
nlp = es_core_news_sm.load()

def index(request):
    title = "Arroz Verde"
    return render(request, "index.html",{'title': title})


# Metodo ajax para el procesamiento de los datos
@csrf_exempt
def process(request):
    # validacion si la petición es ajax
    if request.is_ajax() == True:
        req = {}
        # se guarda en text el texto que se envia desde la vista
        text = request.POST['data']
        # Array que guarda los recursos 
        keywords = []
        # Array que guarda las URIs
        links = []
        # EL recurso y su contador
        cont_key = {}
        #Variable que almacena las tripletas
        data = []
        text = nlp(text)
        # For que recorre cada sentencia del texto ingresado
        for sentence in text.sents:
            # searchResource permite hacer la busqueda de recurso en nuestro grafo de cada sentencia
            searchResource(keywords, sentence.text, links, data, cont_key)

        # Elimina tripletas duplicadas
        data = OrderedDict((tuple(x), x) for x in data).values()

        dictTags = {}
        # Etiquetar a cada recurso con su URI
        for i, j in zip(keywords, cleanLink(links)):
            dictTags[i] = j
        #print(dictTags)
        # Asigna el texto a otra variable para procesarla     
        textComplete = str(text)
        nroEntities = {}
        entities = {}
        # Limpia los datos 
        for i, j in dictTags.items():
            # Cuenta cada recurso que se repite 
            countEntities = textComplete.count(i)
            # Si countEntities es mayor a 0 y si I se encuentra en cont_key
            # quiere decir que si el recurso se encuentra en contkey entra al IF
            if countEntities > 0 and i in cont_key:
                # Se agrega en un diccionario cada valor encontrado
                if cont_key[i] in nroEntities:
                    aux = nroEntities[cont_key[i]]
                    nroEntities.update({cont_key[i]: countEntities + aux})
                    auxList = entities[cont_key[i]]
                    auxList.append(clean_uri(j).replace("_", " "))
                    entities.update({cont_key[i]: auxList})
                else:
                    nroEntities.update({cont_key[i]: countEntities})
                    entities.update({cont_key[i]: [clean_uri(j).replace("_", " ")]})

        # Enlazado de entidades, a cada recurso se le asigna una URI
        for i, j in dictTags.items():
            textComplete = textComplete.replace(i, "<a class='buttonHref' href=\"" + j.replace("page", "resource") + "\" target='_blank' >" + i + "</a>")

    req["textComplete"] = textComplete
    req["nroEntities"] = nroEntities
    req["entities"] = entities
    req["triplet"] = list(data)
    return JsonResponse(req, safe=False)

# Metodo para obtener el tipo de cada entidad de acuerdo al grafo
def clean_uri(uri):
    if uri.find('#') != -1:
        special_char = '#'
    else:
        special_char = '/'
    index = uri.rfind(special_char)
    return uri[index + 1:len(uri)]

# transforma los link de tipo grafo a cadenas
def cleanLink(links):
    clearLink = []
    for i in links:
        x = str(i)
        clearLink.append(x)
    return clearLink

def searchResource(keywords, sentences, links, data, cont_key):
    # transforma la sentencia a spacy para ser tratada
    sentences = nlp(sentences)
    # for que recorre cada sentencia en busca de recursos
    for ent in sentences.ents:
        # for que realiza la busqueda en cada tripleta en busca de ese recurso encontrado en la sentencia
        for s, p, o in graph.triples((None, None, Literal(ent.text))):
            # Si cada recurso se encuentra se lo asigna a keywords para luego se usado más adelante
            keywords.append(ent.text)
            # Todos los sujetos encontrado se los guarda en un array links para luego ser usados
            links.append(s)
            # for que busca el tipo que tiene cada recurso ejp: Persona, PartidoPolitico, Caso
            for s2, p2, o2 in graph.triples((s, RDF.type, None)):
                # Si esto se cumple, se agrega a cont_key el recurso con su tipo {Arroz Verde: Caso}
                cont_key.update({ent.text: clean_uri(o2)})
                #print({ent.text: clean_uri(o2)})
            # for que busca todas las URIs asociadas a ese recurso
            for s3, p3, o3 in graph.triples((s, None, None)):
                resultList = []
                resultList.append(s3.replace("page","resource"))
                resultList.append(p3)
                resultList.append(o3.replace("page","resource"))
                # Se guarda cada tripleta
                data.append(resultList)