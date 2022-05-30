# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1I0GBjW5UgWos-j7f-avVLXXsx66hO8vi
"""

#!pip install beautifulsoup4
#!pip install lxml
#!pip install spacy-dbpedia-spotlight
#!pip install textacy
#!pip install rdflib

#!python -m spacy download en_core_web_lg

"""Se importan las librerías que se van a utilizar. 
Se realiza la request a la página que muestras los tornados entre unas fechas para un condado de USA. En ese listado se buscarán los tornados.
"""

#!gdown 17sFuZxT25UIFle1WPrPe7HIwlFUVW6hI
#!unzip StormEventsDatabase-Dayton-tornado.zip

from bs4 import BeautifulSoup
from collections import OrderedDict
from rdflib import Graph, BNode, Literal
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore, Store, _node_to_sparql
from rdflib.namespace import RDF, XSD, Namespace
import requests

import os
import requests
import spacy_dbpedia_spotlight
import spacy
import itertools
import json
import textacy

nlp = spacy.load('en_core_web_lg')

ruta = "./StormEventsDatabase-Dayton-tornado/"

# Cargamos en un diccionario de listas los nombres de los archivos separados
# en base al tipo de evento.

informes = []

for fichero in os.listdir(ruta):
  #Sacamos solo tornados según el convenio de nombre de archivos
  contenido = open(ruta + fichero, "r").read()
  informes.append(contenido)

"""Ahora que tenemos el HTML de cada informe cargado necesitamos acceder al texto libre del mismo (_narrative_)."""
from bs4 import BeautifulSoup

def extraer_narrativa(contenido):
  soup = BeautifulSoup(contenido, 'html.parser')
  todos_tds = soup.find_all("td")

  narrative = ""

  for i in range(len(todos_tds)):
    contenidos_td = todos_tds[i].contents
    if 'Event Narrative' in contenidos_td:
      narrative = todos_tds[i+1].get_text()
      break

  return narrative

#Diccionario construido segun el estudio de uds según spacy
infoInteres = {
    "velocidad": {
        "mph": ["QUANTITY", "CARDINAL"]
    },
    "ubicaciones": {
        "street": ["FAC"],
        "road": ["FAC", "LOC", "ORG", "GPE"],
        "school": ["FAC"],
        "drive": ["FAC", "LOC"],
        "lane": ["FAC"],
        "crossing": ["FAC"],
        "avenue": ["FAC"],
        "pike": ["FAC", "LOC"],
        "highway": ["FAC"],
        "hall": ["FAC"],
        "route": ["FAC", "ORG"]
    }
}

tornado_idx = 1000

#ahora a añadir los tornados
tornados = {}


# Connect to fuseki triplestore
# Función para convertir blank nodes. Si no existe peta porque no sabe procesar la clase BNode
def my_bnode_ext(node):
    if isinstance(node, BNode):
        return '<bnode:b%s>' % node
    return _node_to_sparql(node)


# Creo la store con los endpoitns
store = SPARQLUpdateStore('http://156.35.98.103:3030/tornados/update', node_to_sparql=my_bnode_ext)
query_endpoint = "http://156.35.98.103:3030/tornados/query"
update_endpoint = "http://156.35.98.103:3030/tornados/update"
store.open((query_endpoint, update_endpoint))

graph = Graph(store)


# define example namespace
prefix_ex = Namespace("http://example.org/")
prefix_om = Namespace("http://opendata.caceres.es/def/ontomunicipio#")
prefix_out = Namespace("http://ontologies.hypios.com/out#")
prefix_ou = Namespace("http://opendata.unex.es/def/ontouniversidad#")
prefix_sx = Namespace("http://shex.io/ns/shex#")
prefix_sd = Namespace("http://www.w3.org/ns/sparql-service-description#")
prefix_st = Namespace("http://sweetontology.net/phenAtmoPrecipitation/")
prefix_stf = Namespace("http://sweetontology.net/stateStorm/")
prefix_location = Namespace("http://sw.deri.org/2006/07/location/loc#")
prefix_loc = Namespace("http://www.w3.org/2007/uwa/context/location.owl#")
prefix_schema = Namespace("http://schema.org/")
prefix_sc = Namespace("http://purl.org/science/owl/sciencecommons/")
prefix_fo = Namespace("http://purl.org/ontology/fo/")
prefix_db = Namespace("http://dbpedia.org/resource/classes#")
prefix_oum = Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")

# Añadimos la primera parte de la lista de tornados
graph.add((prefix_ex.tornadosEj3, RDF.first, prefix_ex.tornado + str(tornado_idx)))
graph.add((prefix_ex.tornadosEj3, RDF.rest, prefix_ex.listItem + str(tornado_idx)))

for informe in range(len(informes)):
  contenido = informes[informe]
  
  #sacamos la info por defecto
  tornado_soup = BeautifulSoup(contenido, 'html.parser')
  tables = tornado_soup.find_all("table")
  tds = tables[0].find_all("td")
  
  for i in range(len(tds)):
    text = tds[i].get_text()
    if text == "State":
      state_value = tds[i+1].get_text()
    elif text == "County/Area":
      county = tds[i+1].get_text()
    elif text == "Report Source":
      report_source_value = tds[i+1].get_text()
    elif text == "Begin Date":
      begin_date = tds[i+1].get_text()
    elif text == "End Date":
      end_date = tds[i+1].get_text()
    elif text == "Begin Lat/Lon":
      info = tds[i+1].get_text().split("/")
      begin_lat = info[0]
      begin_lon = info[1]
    elif text == "End Lat/Lon":
      info == tds[i+1].get_text().split("/")
      end_lat = info[0]
      end_lon = info[1]
    elif text == "Deaths Direct/Indirect":
      info = tds[i+1].get_text().split(" ")[0].split("/")
      deaths_direct = info[0]
      deaths_indirect = info[1]
    elif text == "Injuries Direct/Indirect":
      info = tds[i+1].get_text().split("/")
      injuries_direct = info[0]
      injuries_indirect = info[1]
    elif text == "-- Scale":
      scale = tds[i+1].get_text()
    elif text == "-- Length":
      length = tds[i+1].get_text().split(" ")[0]
    elif text == "-- Width":
      width = tds[i+1].get_text().split(" ")[0]


  narrative = extraer_narrativa(contenido)
  if (len(narrative) > 0): 
    informes[informe] = narrative

    doc = nlp(informes[informe])
    destilado = {}

    #variables que guardan la info extra
    speedsOfThisTornado = {}
    foundInfos = {}
    ubicacionesStringed = ""

    for entidad in doc.ents:
      # label_ es una cadena de texto indicando el tipo de entidad.
      
      # ¡Atención! Los tipos de entidad dependen del modelo y el idioma pues
      # se obtuvieron por entrenamiento sobre datasets muy diversos

      etiqueta = entidad.label_

      # text es el texto del Span con que se modela la entidad

      texto = entidad.text

      #recorro el diccionario de interes
      #para la velocidad chequeo si el texto contiene "mph", y luego
      #que la etiqueta esté en el diccionario
      
      if "mph" in texto.lower():
        for unidad in infoInteres["velocidad"]:
          for ubicacion in infoInteres["velocidad"][unidad]:
            if etiqueta == ubicacion:
              infoExistente = speedsOfThisTornado.get(texto)
              if not infoExistente:
                speedsOfThisTornado[texto] = texto




      #para las ubicaciones recorremos el diccionario
      #por cada iteracion vemos si el índice esta contenido
      #en texto, y que la etiqueta esté en la lista de dicho texto:

      
      for indice in infoInteres["ubicaciones"]:
        if indice in texto.lower():
          for ubicacion in infoInteres["ubicaciones"][indice]:
            if etiqueta == ubicacion:
              infoExistente = foundInfos.get(texto)
              if not infoExistente and len(texto) > 0:
                foundInfos[texto] = texto
                ubicacionesStringed = ubicacionesStringed + texto + ", "
      
    ubicacionesStringed = ubicacionesStringed[:len(ubicacionesStringed) - 2]
          
    numeroVelocidades = len(speedsOfThisTornado)
    velocidadMediaTornado = 0
    
    if numeroVelocidades > 0:
      for velocidad in speedsOfThisTornado:
        numeric_speed = ''.join(filter(str.isdigit, velocidad))
        velf = 0
        if len(numeric_speed) > 3: #nadie ha visto tornados de velocidad > 1000mph ^^
          vel1 = numeric_speed[:len(numeric_speed)//2]
          vel2 = numeric_speed[len(numeric_speed)//2:]
          velf = (int(vel1) + int(vel2)) / 2

        if velf > 0:
          velocidadMediaTornado = velocidadMediaTornado + velf
        else:
          velocidadMediaTornado = velocidadMediaTornado + int(numeric_speed)
      
      velocidadMediaTornado = (velocidadMediaTornado/numeroVelocidades)
    
    # Creamos nodos
    node1 = (prefix_ex.tornado + str(tornado_idx), RDF.type, prefix_st.Tornado)
    init_datetime_literal = Literal(begin_date, datatype=XSD.dateTime)
    end_datetime_literal = Literal(end_date, datatype=XSD.dateTime)
    node2 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.initDateTime, init_datetime_literal)
    node3 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.endDateTime, end_datetime_literal)

    state = (prefix_ex.tornado_state + str(tornado_idx), RDF.type, prefix_schema.State)
    state_address = Literal(state_value, datatype=prefix_schema.address)
    state_county = Literal(county, datatype=XSD.string)
    state2 = (prefix_ex.tornado_state + str(tornado_idx), prefix_schema.address, state_address)
    state3 = (prefix_ex.tornado_state + str(tornado_idx), prefix_ex.county, state_county)

    node4 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.state, prefix_ex.tornado_state + str(tornado_idx))

    node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F0)

    max_wind_speed = Literal("120", datatype=XSD.integer)

    wind_speed = (prefix_ex.max_wind_speed + str(tornado_idx), RDF.type, prefix_oum.Measure)
    wind_speed2 = (prefix_ex.max_wind_speed + str(tornado_idx), prefix_oum.hasNumericalValue, max_wind_speed)
    wind_speed3 = (prefix_ex.max_wind_speed + str(tornado_idx), prefix_oum.hasUnit, prefix_oum.mileStatutePerHour)

    node6 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.max_wind_speed, prefix_ex.max_wind_speed + str(tornado_idx))

    deaths_direct_literal = Literal(deaths_direct, datatype=XSD.integer)
    deaths_indirect_literal = Literal(deaths_indirect, datatype=XSD.integer)
    injuries_direct_literal = Literal(injuries_direct, datatype=XSD.integer)
    injuries_indirect_literal = Literal(injuries_indirect, datatype=XSD.integer)
    node7 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.deathsDirect, deaths_direct_literal)
    node8 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.deathsIndirect, deaths_indirect_literal)
    node9 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.injuriesDirect, injuries_direct_literal)
    node10 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.injuriesIndirect, injuries_indirect_literal)

    report_source = (prefix_ex.reportSource + str(tornado_idx), RDF.type, prefix_schema.Report)
    report_number_literal = Literal(report_source_value, datatype=prefix_schema.reportNumber)
    report_source2 = (prefix_ex.reportSource + str(tornado_idx), prefix_schema.reportNumber, report_number_literal)

    node11 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.reportSource, prefix_ex.report_source + str(tornado_idx))

    duration_literal = Literal("P0Y0M0DT0H20M0S", datatype=prefix_schema.Duration)
    node12 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.duration, duration_literal)

    begin_location_literal = Literal("2NE METAMORA", datatype=prefix_schema.beginLocation)
    node13 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.beginLocation, begin_location_literal)
    end_location_literal = Literal("2NE METAMORA", datatype=prefix_schema.endLocation)
    node14 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.endLocation, end_location_literal)

    if not 'begin_lat' in locals():
        begin_lat = 0
        begin_lon = 0
    init_coordinates = (prefix_ex.init_coordinates + str(tornado_idx), RDF.type, prefix_schema.GeoCoordinates)
    begin_latitude_literal = Literal(begin_lat, datatype=prefix_schema.latitude)
    begin_longitude_literal = Literal(begin_lon, datatype=prefix_schema.longitude)
    init_coordinates2 = (prefix_ex.init_coodinates + str(tornado_idx), prefix_ex.latitude, begin_latitude_literal)
    init_coordinates3 = (prefix_ex.init_coodinates + str(tornado_idx), prefix_ex.longitude, begin_longitude_literal)
    node15 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.init, prefix_ex.init_coordinates + str(tornado_idx))

    # Check it was defined, some events dont have this variable
    if not 'end_lat' in locals():
        end_lat = 0
        end_lon = 0

    end_coordinates = (prefix_ex.end_coordinates + str(tornado_idx), RDF.type, prefix_schema.GeoCoordinates)
    end_latitude_literal = Literal(end_lat, datatype=prefix_schema.latitude)
    end_longitude_literal = Literal(end_lon, datatype=prefix_schema.longitude)
    end_coordinates2 = (prefix_ex.end_coordinates + str(tornado_idx), prefix_ex.latitude, end_latitude_literal)
    end_coordinates3 = (prefix_ex.end_coordinates + str(tornado_idx), prefix_ex.longitude, end_longitude_literal)

    node16 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.end, prefix_ex.end_coordinates + str(tornado_idx))

    if not 'width' in locals():
        width = 0
        length = 0

    width_node = (prefix_ex.width + str(tornado_idx), RDF.type, prefix_oum.Measure)
    width_numerical_value_literal = Literal(width, datatype=XSD.double)
    width_node_2 = (prefix_ex.width + str(tornado_idx), prefix_oum.hasNumericalValue, width_numerical_value_literal)
    width_node_3 = (prefix_ex.width + str(tornado_idx), prefix_oum.hasUnit, prefix_oum.yardinternational)

    node17 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.width, prefix_ex.width_node + str(tornado_idx))

    length_node = (prefix_ex.length + str(tornado_idx), RDF.type, prefix_oum.Measure)
    length_numerical_value_literal = Literal(length, datatype=XSD.double)
    length_node_2 = (prefix_ex.length + str(tornado_idx), prefix_oum.hasNumericalValue, width_numerical_value_literal)
    length_node_3 = (prefix_ex.length + str(tornado_idx), prefix_oum.hasUnit, prefix_oum.mileStatute)

    node18 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.width, prefix_ex.length_node + str(tornado_idx))

    ubicaciones_literal = Literal(ubicacionesStringed, datatype=XSD.string)
    node19 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.ubicaciones, ubicaciones_literal)
    
    speeds_literal = Literal(velocidadMediaTornado, datatype=XSD.double)
    node20 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.maxSpeed, speeds_literal)

    # Open a graph in the open store and set identifier to default graph ID0.
    # Se añaden los nodos al grafo.
    graph = Graph(store)
    graph.add((prefix_ex.listItem + str(tornado_idx), RDF.first, prefix_ex.tornado + str(tornado_idx)))
    graph.add(node1)
    graph.add(node2)
    graph.add(node3)
    graph.add(state)
    graph.add(state2)
    graph.add(state3)
    graph.add(node4)
    graph.add(node5)
    graph.add(wind_speed)
    graph.add(wind_speed2)
    graph.add(wind_speed3)
    graph.add(node6)
    graph.add(node7)
    graph.add(node8)
    graph.add(node9)
    graph.add(node10)
    graph.add(report_source)
    graph.add(report_source2)
    graph.add(node11)
    graph.add(node12)
    graph.add(node13)
    graph.add(node14)
    graph.add(init_coordinates)
    graph.add(init_coordinates2)
    graph.add(init_coordinates3)
    graph.add(node15)
    graph.add(end_coordinates)
    graph.add(end_coordinates2)
    graph.add(end_coordinates3)
    graph.add(node16)
    graph.add(width_node)
    graph.add(width_node_2)
    graph.add(width_node_3)
    graph.add(node17)
    graph.add(length_node)
    graph.add(length_node_2)
    graph.add(length_node_3)
    graph.add(node18)
    graph.add(node19)
    graph.add(node20)

    if tornado_idx < (len(informes) + 1000):
        graph.add((prefix_ex.listItem + str(tornado_idx), RDF.rest, prefix_ex.listItem + str(tornado_idx + 1)))
    # Rest if there are no more
    else:
        graph.add((prefix_ex.listItem + str(tornado_idx) + str(evento_idx), RDF.rest, RDF.nil))

    tornado_idx = tornado_idx + 1

    print(graph)

# Se guarda el grafo en fuseki.
print("enviando")
store.add_graph(graph)
print("enviado")