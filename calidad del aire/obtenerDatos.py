# wget https://datosabiertos.jcyl.es/web/jcyl/risp/es/medio-ambiente/calidad_aire_estaciones/1284212701893.csv -O estaciones.csv

# wget https://datosabiertos.jcyl.es/web/jcyl/risp/es/sector-publico/municipios/1284278782067.csv -O municipios.csv

# es necesario arreglar la codificación del primero de estos archivos

from bs4 import BeautifulSoup
import urllib.request
import csv
import re
from math import cos, asin, sqrt

def dms2dd(dms):
  deg, minutes, seconds, direction = re.split('[º\'"]+', dms.replace(' ',''))
  return (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if direction in ['W', 'S'] else 1)

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295     #Pi/180
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) #2*R*asin...

provincias = [5,9,24,34,37,40,42,47,49]
estaciones = {}
for provincia in provincias:
  html_page = urllib.request.urlopen("http://servicios.jcyl.es/esco/datosTiempoReal.action?provincia="+str(provincia))
  soup = BeautifulSoup(html_page,"html.parser")
  estacionesProvincia = soup.find("select", {"id": "estacion"})
  for estacion in estacionesProvincia.findAll('option'):
    if not estacion.get_text() == 'Todas':
      estaciones[estacion.get_text()] = {"value":estacion['value'], "provincia":str(provincia)}

with open('estaciones.csv', 'r') as csvfile:
  spamreader = csv.reader(csvfile, delimiter=';')
  for row in spamreader:
    if row[0] in estaciones:
      estaciones[row[0]]["lon"] = dms2dd(row[3])
      estaciones[row[0]]["lat"] = dms2dd(row[4])

if "lon" not in estaciones["Puente Poniente-Mº Luisa Sánchez"]:
    del estaciones["Puente Poniente-Mº Luisa Sánchez"]

municipios = {}

with open('municipios.csv', 'r', encoding='latin') as csvfile:
  spamreader = csv.reader(csvfile, delimiter=';')
  next(spamreader)
  for row in spamreader:
    dist = float('inf')
    value = ""
    provincia = ""
    for nombre, estacion in estaciones.items():
      newdist = distance(float(row[9].replace(',','.')),float(row[10].replace(',','.')),estacion["lon"],estacion["lat"])
      if newdist < dist:
        dist = newdist
        value = estacion["value"]
        provincia = estacion["provincia"]
    municipios[row[0].lower()] = {"value": value, "provincia": provincia}




f = open('municipiosCalidadAire.py','w')
f.write("municipiosCalidadAire = " + str(municipios) + "\n")
f.write("\n")
f.write("estaciones = " + str(estaciones) + "\n")
f.close()
