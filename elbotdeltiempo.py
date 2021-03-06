#!/usr/bin/env python
# -*- coding: utf-8 -*-

# mongod --dbpath ./data
# python elbotdeltiempo.py

"""El Bot del Tiempo (beta)

Este programa está bajo una licencia GNU GENERAL PUBLIC LICENSE.

La información metereológica que muestra El Bot del Tiempo ha sido elaborada por la Agencia Estatal de Meteorología (© AEMET). AEMET no participa, patrocina, o apoya la reutilización de sus datos que se lleva a cabo.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)
import googlemaps
import logging
import urllib
import urllib2
import requests
from cachecontrol import CacheControl
import xml.etree.ElementTree as etree
import datetime
import time
from pymongo import MongoClient
import subprocess
import os
from municipios import municipios
from municipiosCalidadAire import municipiosCalidadAire, estaciones
from auxiliar import estados_cielo, direccion_viento, num_emoji, active_emoji, alerta_text, dia_semana, predicciones, alertas, mapaCodigo
from config import TELEGRAMTOKEN, GOOGLEMAPSKEY, BOTNAME, ADMIN
from PIL import Image, ImageDraw, ImageFont
from cStringIO import StringIO
import imageio
import numpy
from bs4 import BeautifulSoup

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename='./logs/'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.log', filemode='w',level=logging.INFO)
logger = logging.getLogger(__name__)

gmaps = googlemaps.Client(key=GOOGLEMAPSKEY)

client = MongoClient()
db = client.elbotdeltiempodb
collection = db.users

sess = requests.session()
cached_sess = CacheControl(sess)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(u'¡Hola! Soy @' + BOTNAME + u'.')
    if collection.find_one({"_id":update.effective_chat.id}) is None:
        collection.insert({"_id":update.effective_chat.id})
    if update.effective_chat.type == "private":
        collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": True, "configurarTiempo": predicciones["3"], "viento": True, "sensacionTermica": True, "humedadRelativa": True, "alerta": 1, "configurarAlerta": alertas["1"], "tipo":update.effective_chat.type, "nombre": update.effective_chat.first_name, "alias": update.effective_chat.username}}, upsert=False)
    else:
        collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": True, "configurarTiempo": predicciones["3"], "viento": True, "sensacionTermica": True, "humedadRelativa": True, "alerta": 1, "configurarAlerta": alertas["1"], "tipo":update.effective_chat.type, "titulo": update.effective_chat.title}}, upsert=False)
    user = collection.find_one({"_id":update.effective_chat.id})
    logger.info(u'nuevo usuario con id: %s se ha registrado', str(user["_id"]))
    if "municipio" not in user:
        send_message(bot=bot,chat_id=update.effective_chat.id,
            text=textoMunicipio(None),
            parse_mode=ParseMode.MARKDOWN)
    else:
        send_message(bot=bot,chat_id=update.effective_chat.id,
            text=textoMunicipio(user["municipio"]),
            parse_mode=ParseMode.MARKDOWN)
    send_message(bot=bot,chat_id=update.effective_chat.id,
        text=u'Para que te diga el tiempo envía /tiempo.\nPara acceder a todas las opciones pulsa /configurar.\nPara tener más ayuda manda /ayuda.',
        parse_mode=ParseMode.MARKDOWN)

def getUser(bot, update):
    user = collection.find_one({"_id":update.effective_chat.id})
    if user is None:
        start(bot, update)
        user = collection.find_one({"_id":update.effective_chat.id})
    collection.update_one({'_id':user["_id"]}, {"$set": {"activo": True}}, upsert=False)
    return user


def new_chat_member(bot, update):
    if  any(user.username == BOTNAME for user in update.message.new_chat_members):
        start(bot,update)

def stop(bot, update):
    user = getUser(bot, update)
    logger.info(u'User %s canceled the conversation.', str(user["_id"]))
    collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": False}}, upsert=False)

def left_chat_member(bot, update):
    if  update.message.left_chat_member.username == BOTNAME:
        stop(bot, update)

def help(bot, update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    update.message.reply_text(text=u'Para que te diga el *tiempo* envía /tiempo.\n\nPara acceder a todas las opciones pulsa /configurar.\nAhí podrás elegir si quieres recibir datos sobre el _viento_, la _sensación térmica_ o la _humedad relativa_.\n\nTambién podrás seleccionar si quieres recibir el tiempo para mañana, para varios días o por horas.\n\nY finalmente si activas la _alerta_ cada día a las 21:00 te enviaré información sobre el tiempo del día siguiente. Si escoges como opción _solo lluvia_ lo haré sólo si va a llover, para que recuerdes que tienes que coger el paraguas.',parse_mode=ParseMode.MARKDOWN)

def textoMunicipio(municipio):
    if municipio is not None:
        return u'Estoy configurado para enviarte información de *' + municipio + u'*. Puedes cambiarlo enviando el comando `/municipio` seguido del nombre. Así:\n`/municipio ' + municipio +'`'
    else:
        return u'Tienes que decirme cuál es tu municipio. Hazlo enviando el comando `/municipio` seguido del nombre. Así:\n`/municipio Soria`'

def municipio(bot, update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.FIND_LOCATION)
    user = getUser(bot, update)
    if update.message.text == "/municipio":
        if "municipio" in user:
            send_message(bot=bot,chat_id=update.effective_chat.id,
                text=textoMunicipio(user["municipio"]),
                parse_mode=ParseMode.MARKDOWN)
        else:
            send_message(bot=bot,chat_id=update.effective_chat.id,
                text=textoMunicipio(None),
                parse_mode=ParseMode.MARKDOWN)
        return
    geocode_result = gmaps.geocode(address=update.message.text[update.message.text.index(' ') + 1:],components={"country":"ES"})
    if not geocode_result:
        logger.warning(u'El usuario %s ha buscado el municipio %s, que no existe.', str(user["_id"]),update.message.text[update.message.text.index(' ') + 1:])
        send_message(bot=bot,chat_id=update.effective_chat.id,
            text=u'No encuentro ese municipio. ¿Estás seguro de que lo has escrito bien?\nPrueba a ser más específico, así:\n\n`/municipio Santander, Cantabria`',
            parse_mode=ParseMode.MARKDOWN)
        return
    reverse_geocode_result = gmaps.reverse_geocode((geocode_result[0]["geometry"]["location"]["lat"], geocode_result[0]["geometry"]["location"]["lng"]))
    try:
        pais = next((item for item in reverse_geocode_result[0]['address_components'] if item['types'][0] == 'country'),None)['short_name']
    except StopIteration:
        logger.warning(u'stop iteration: sin país, %s ha escrito: %s', str(update.effective_chat.id), update.message.text)
        send_message(bot=bot,chat_id=update.effective_chat.id,
            text=u'No encuentro ese municipio. ¿Estás seguro de que lo has escrito bien?\nPrueba a ser más específico, así:\n\n`/municipio Santander, Cantabria`',
            parse_mode=ParseMode.MARKDOWN)
        return
    if pais != 'ES':
        send_message(bot=bot,chat_id=update.effective_chat.id,
            text=u'Solo conozco el tiempo de municipios españoles, lo siento. Si quieres recibir el tiempo de una localidad española comprueba que la hayas escrito bien.\nQuizás hay otro lugar en el mundo que se llama igual, prueba a ser más específico, así:\n\n`/municipio Santander, Cantabria`',
            parse_mode=ParseMode.MARKDOWN)
        logger.warning(u'Ubicación en: %s, %s ha escrito: %s',pais,str(update.effective_chat.id), update.message.text)
    else:
        for direccion in reverse_geocode_result:
            try:
                nombre = next(item for item in direccion['address_components'] if item['types'][0] == 'locality')['long_name'].encode('utf-8')
                if municipios.get(nombre.decode('utf-8').lower().encode('utf-8')) == None: nombre = next(item for item in direccion['address_components'] if item['types'][0] == 'administrative_area_level_4')['long_name'].encode('utf-8')
                codigoMunicipio = municipios[nombre.decode('utf-8').lower().encode('utf-8')]
                collection.update_one({'_id':update.effective_chat.id}, {"$set": {"municipio": nombre, "idMunicipio": codigoMunicipio}}, upsert=False)
                send_message(bot=bot,chat_id=update.effective_chat.id,
                    text=u'¡Municipio actualizado! 🌍\nAhora cuando me envíes el comando /tiempo te responderé con la predicción para *' + unicode(nombre, "utf-8") + '*.',
                    parse_mode=ParseMode.MARKDOWN)
                logger.info(u'%s ha cambiado su ubicación a %s (%s)',str(user["_id"]),unicode(nombre, "utf-8"),str(codigoMunicipio).decode('utf-8'))
                return
            except StopIteration:
                logger.warning('stop iteration, %s ha escrito: %s',str(update.effective_chat.id), update.message.text)
                continue
        send_message(bot=bot,chat_id=update.effective_chat.id,
            text=u'No encuentro ese municipio. ¿Estás seguro de que lo has escrito bien?\nPrueba a ser más específico, así:\n\n`/municipio Santander, Cantabria`',
            parse_mode=ParseMode.MARKDOWN)
def comandoTiempo(bot,update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user = getUser(bot, update)
    tiempo(bot,user,user["configurarTiempo"]["dias"],user["configurarTiempo"]["horas"]["hoy"],user["configurarTiempo"]["horas"]["manyana"],False)

def comandoTiempoMenu(bot,update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    keyboard = [[InlineKeyboardButton(u"1 día", callback_data='tiempoMenu1'),
                 InlineKeyboardButton(u"2 días", callback_data='tiempoMenu2')],
                [InlineKeyboardButton(u"3 días", callback_data='tiempoMenu3'),
                 InlineKeyboardButton(u"7 días", callback_data='tiempoMenu7')],
                [InlineKeyboardButton(u"Hoy (cada 2 horas)", callback_data='tiempoMenuHOY2H')],
                [InlineKeyboardButton(u"Mañana (cada 2 horas)", callback_data='tiempoMenuMANYANA2H')],
                [InlineKeyboardButton(u"Hoy y Mañana (cada 2 h)", callback_data='tiempoMenuHOYMANYANA2H')]]
    user = getUser(bot, update)
    if user["municipio"].lower().encode('utf-8') in municipiosCalidadAire:
        keyboard.append([InlineKeyboardButton(u"Calidad del aire", callback_data='calidadAire')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    send_message(bot=bot,text=u"Elige la predicción:",
                          chat_id=update.effective_chat.id,
                          reply_markup=reply_markup)
    return

def alerta(bot, job):
    logger.info(u'se está enviando la alerta')
    for user in collection.find({"$and":[{"activo": True}, {"alerta": {"$gte": 1}}, {"idMunicipio":{"$exists":True}}]}):
        time.sleep(0.5)
        try:
            if user["alerta"] == 1:
                tiempo(bot,user,user["configurarAlerta"]["dias"],user["configurarAlerta"]["horas"]["hoy"],user["configurarAlerta"]["horas"]["manyana"],False)
            elif user["alerta"] == 2:
                tiempo(bot,user,user["configurarAlerta"]["dias"],user["configurarAlerta"]["horas"]["hoy"],user["configurarAlerta"]["horas"]["manyana"],True)
        except Unauthorized:
            logger.warning(u"ha pasado algo enviando la alerta")
            collection.update_one({'_id':user["_id"]}, {"$set": {"activo": False}}, upsert=False)
            logger.error('unauthorized %s',str(user["_id"]))
        except TimedOut:
            logger.error('timedOut %s',str(user["_id"]))
        except TelegramError:
            # handle all other telegram related errors
            logger.error('telegram error %s', str(user["_id"]))
    #estadisticas al admin
    user = collection.find_one({"alias":ADMIN})
    send_message(bot=bot,chat_id=user["_id"], text=u'#usuariosTotales ' + str(collection.find().count()))
    send_message(bot=bot,chat_id=user["_id"], text=u'#usuariosLocalizados ' + str(collection.find({"idMunicipio":{"$exists":True}}).count()))
    send_message(bot=bot,chat_id=user["_id"], text=u'#usuariosLocalizadosActivos ' + str(collection.find({"$and":[{"activo": True}, {"idMunicipio":{"$exists":True}}]}).count()))
    send_message(bot=bot,chat_id=user["_id"], text=u'#usuariosSuscritos ' + str(collection.find({"$and":[{"activo": True}, {"alerta": {"$gte": 1}}, {"idMunicipio":{"$exists":True}}]}).count()))

def bugFix(bot,job):
    #logger.info(u'se está intentando solucionar el error')
    pass


def tiempo(bot,user,prediccionDias,prediccionHoy,prediccionManyana,soloLluvia):
    if "idMunicipio" not in user:
        send_message(bot=bot,chat_id=user["_id"],
            text=textoMunicipio(None),
            parse_mode=ParseMode.MARKDOWN)
        return
    try:
        treeDia = etree.ElementTree(etree.fromstring(requests.get('http://www.aemet.es/xml/municipios/localidad_' + str(user["idMunicipio"]) + '.xml',timeout=2).content))
    except requests.exceptions.RequestException as err:
        logger.error(u'URLError de %s porque pasa %s',str(user["_id"]),str(err))
        return

    rootDia = treeDia.getroot()
    dias = [rootDia[4][i] for i in prediccionDias]
    for dia in dias:
        lluvia = next(item for item in dia.findall('prob_precipitacion') if item.text is not None).text
        if not soloLluvia or lluvia != "0":
            time.sleep(0.5)
            send_message(bot=bot,chat_id=user["_id"],
                text=prediccion(dia,user),
                parse_mode=ParseMode.MARKDOWN)
    now = datetime.datetime.now()
    try:
        treeHora = etree.ElementTree(etree.fromstring(requests.get('http://www.aemet.es/xml/municipios_h/localidad_h_' + str(user["idMunicipio"]) + '.xml',timeout=2).content))
    except requests.exceptions.RequestException as err:
        logger.error(u'URLError de %s porque pasa %s',str(user["_id"]),str(err))
        return
    rootHora = treeHora.getroot()
    if now.date() == datetime.datetime.strptime(rootHora[4][0].attrib['fecha'], '%Y-%m-%d').date():
        today = rootHora[4][0]
        tomorrow = rootHora[4][1]
    else:
        today = rootHora[4][1]
        tomorrow = rootHora[4][2]
    for hora in prediccionHoy:
        if hora >= now.hour and today.find('./estado_cielo[@periodo="%s"]' % str(hora).zfill(2)) is not None:
            lluvia = today.find('./precipitacion[@periodo="%s"]' % str(hora).zfill(2)).text
            if not soloLluvia or lluvia != "0":
                time.sleep(0.5)
                send_message(bot=bot,chat_id=user["_id"],
                    text=prediccionHora(today,hora,user),
                    parse_mode=ParseMode.MARKDOWN)
    for hora in prediccionManyana:
        if tomorrow.find('./estado_cielo[@periodo="%s"]' % str(hora).zfill(2)) is not None:
            lluvia = tomorrow.find('./precipitacion[@periodo="%s"]' % str(hora).zfill(2)).text
            if not soloLluvia or lluvia != "0":
                time.sleep(0.5)
                send_message(bot=bot,chat_id=user["_id"],
                    text=prediccionHora(tomorrow,hora,user),
                    parse_mode=ParseMode.MARKDOWN)

def prediccion(dia,user):
    date = datetime.datetime.strptime(dia.attrib['fecha'], '%Y-%m-%d').date()
    estado = next(item for item in dia.findall('estado_cielo') if item.attrib['descripcion'] is not '').attrib['descripcion']
    probPrecipitacion = next(item for item in dia.findall('prob_precipitacion') if item.text is not None).text
    prediccion = u'*' + dia_semana[date.weekday()] + u' ' + date.strftime('%d') + u'*: ' + estados_cielo[estado] + u'\n' + estado + u'\nTemperatura: ' + dia.find('temperatura').find('maxima').text + u'ºC / ' + dia.find('temperatura').find('minima').text + u'ºC'
    if user["sensacionTermica"]:
        prediccion = prediccion + u'\nSens. térmica: ' + dia.find('sens_termica').find('maxima').text + u'ºC / ' + dia.find('sens_termica').find('minima').text + u'ºC'
    if probPrecipitacion != '0':
        prediccion = prediccion +'\nProbabilidad de lluvia: ' + probPrecipitacion + u'%'
    if user["viento"]:
        viento = next(item for item in dia.findall('viento') if item.find('velocidad').text is not None)
        prediccion = prediccion + u'\nViento: ' + viento.find('velocidad').text + u' km/h ' + direccion_viento[viento.find('direccion').text]
    if user["humedadRelativa"]:
        prediccion = prediccion + u'\nHumedad relativa: ' + dia.find('humedad_relativa').find('maxima').text + u'% / ' + dia.find('humedad_relativa').find('minima').text + u'%'
    return prediccion

def prediccionHora(dia,hora,user):
    date = datetime.datetime.strptime(dia.attrib['fecha'], '%Y-%m-%d').date()
    estado = dia.find('./estado_cielo[@periodo="%s"]' % str(hora).zfill(2)).attrib['descripcion']
    precipitacion = dia.find('./precipitacion[@periodo="%s"]' % str(hora).zfill(2)).text
    temperatura = dia.find('./temperatura[@periodo="%s"]' % str(hora).zfill(2)).text
    prediccion = u'*' + dia_semana[date.weekday()] + u' ' + date.strftime('%d') + u' - ' + str(hora).zfill(2) +  u'h*: ' + estados_cielo[estado] + u'\n' + estado + u'\nTemperatura: ' + temperatura + u'ºC'
    if user["sensacionTermica"]:
        sensTermica = dia.find('./sens_termica[@periodo="%s"]' % str(hora).zfill(2)).text
        prediccion = prediccion + u'\nSens. térmica: ' + sensTermica + u'ºC'
    if precipitacion != '0':
        if precipitacion == 'Ip':
            prediccion = prediccion + u'\nPrecipitación: 💦'
        else:
            prediccion = prediccion + u'\nPrecipitación: ' + precipitacion + u' mm ☔️'
    if user["viento"]:
        viento = dia.find('./viento[@periodo="%s"]' % str(hora).zfill(2))
        prediccion = prediccion + u'\nViento: ' + viento.find('velocidad').text + u' km/h ' + direccion_viento[viento.find('direccion').text]
    if user["humedadRelativa"]:
        humRel = dia.find('./humedad_relativa[@periodo="%s"]' % str(hora).zfill(2)).text
        prediccion = prediccion + u'\nHumedad relativa: ' + humRel + u'%'
    return prediccion

def configurar(bot, update):
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user = getUser(bot, update)
    logger.info(u'el usuario %s quiere configurar', str(user["_id"]))
    update.message.reply_text(u'Configuración:', reply_markup=crearTecladoConfigurar(user))

def crearTecladoConfigurar(user):
    keyboard = [[InlineKeyboardButton(alerta_text[user["alerta"]], callback_data='alerta')],
                [InlineKeyboardButton(u"⚙️ Configurar predicción", callback_data='configurarPrediccion')],
                [InlineKeyboardButton(u"⚙️ Configurar alerta", callback_data='configurarAlerta')],
                [InlineKeyboardButton(active_emoji[user["viento"]] + u" Viento", callback_data='viento')],
                [InlineKeyboardButton(active_emoji[user["sensacionTermica"]] + u" Sensación térmica", callback_data='sensacionTermica')],
                [InlineKeyboardButton(active_emoji[user["humedadRelativa"]] + u" Humedad Relativa", callback_data='humedadRelativa')]]
    return InlineKeyboardMarkup(keyboard)

def configuracionMenu(bot, update):
    query = update.callback_query
    user = collection.find_one({"_id":query["message"]["chat"]["id"]})
    if query["data"].startswith("tiempoMenu"):
        bot.delete_message(chat_id=query.message.chat_id,message_id=query.message.message_id)
        prediccion = predicciones[query["data"][len("tiempoMenu"):]]
        tiempo(bot,user,prediccionDias = prediccion["dias"],prediccionHoy = prediccion["horas"]["hoy"],prediccionManyana = prediccion["horas"]["manyana"],soloLluvia=False)
        return
    if query["data"] == "configurarPrediccion":
        keyboard = [[InlineKeyboardButton(u"1 día", callback_data='configurandoPrediccion1'),
                     InlineKeyboardButton(u"2 días", callback_data='configurandoPrediccion2')],
                    [InlineKeyboardButton(u"3 días", callback_data='configurandoPrediccion3'),
                     InlineKeyboardButton(u"7 días", callback_data='configurandoPrediccion7')],
                    [InlineKeyboardButton(u"Hoy (cada 2 horas)", callback_data='configurandoPrediccionHOY2H')],
                    [InlineKeyboardButton(u"Mañana (cada 2 horas)", callback_data='configurandoPrediccionMANYANA2H')],
                    [InlineKeyboardButton(u"Hoy y Mañana (cada 2 h)", callback_data='configurandoPrediccionHOYMANYANA2H')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(text=u"Configura la predicción:",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
        return
    if query["data"].startswith("configurandoPrediccion"):
        user["configurarTiempo"] = predicciones[query["data"][len("configurandoPrediccion"):]]
        collection.update_one({'_id':user["_id"]}, {"$set": {"configurarTiempo": user["configurarTiempo"]}}, upsert=False)
        bot.edit_message_text(text=u"Configuración:",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=crearTecladoConfigurar(user))
        return
    if query["data"] == "configurarAlerta":
        keyboard = [[InlineKeyboardButton(u"1 día", callback_data='configurandoAlerta1'),
                     InlineKeyboardButton(u"2 días", callback_data='configurandoAlerta2')],
                    [InlineKeyboardButton(u"3 días", callback_data='configurandoAlerta3'),
                     InlineKeyboardButton(u"7 días", callback_data='configurandoAlerta6')],
                    [InlineKeyboardButton(u"Mañana (cada 2 horas)", callback_data='configurandoAlertaMANYANA2H')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(text="Configura la alerta:",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
        return
    if query["data"].startswith("configurandoAlerta"):
        user["configurarAlerta"] = alertas[query["data"][len("configurandoAlerta"):]]
        collection.update_one({'_id':user["_id"]}, {"$set": {"configurarAlerta": user["configurarAlerta"]}}, upsert=False)
        bot.edit_message_text(text=u"Configuración:",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=crearTecladoConfigurar(user))
        return
    if query["data"] == "alerta":
        user["alerta"] = (user["alerta"]+1) %3
        collection.update_one({'_id':user["_id"]}, {"$set": {"alerta": user["alerta"]}}, upsert=False)
        query.edit_message_reply_markup(reply_markup=crearTecladoConfigurar(user))
        return
    if query["data"] == "calidadAire":
        bot.delete_message(chat_id=query.message.chat_id,message_id=query.message.message_id)
        calidadAire(bot, update)
        return
    #cambiar la configuración de viento / sensación térmica / humedad relativa
    cambiarConfiguracion(bot,user,query["data"],query)
    return

def cambiarConfiguracion(bot,user,opcion,query):
    user[opcion] = not user[opcion]
    collection.update_one({'_id':user["_id"]}, {"$set": {opcion: user[opcion]}}, upsert=False)
    query.edit_message_reply_markup(reply_markup=crearTecladoConfigurar(user))
    return

def calidadAire(bot, update):
    user = getUser(bot, update)
    if "municipio" not in user:
        send_message(bot=bot,chat_id=user["_id"],
            text=textoMunicipio(None),
            parse_mode=ParseMode.MARKDOWN)
        return
    if user["municipio"].lower().encode('utf-8') not in municipiosCalidadAire:
        send_message(bot=bot,chat_id=user["_id"],
            text=u'Lo siento, de momento solo dispongo de datos sobre la calidad del aire para municipios de Castilla y León.',
            parse_mode=ParseMode.MARKDOWN)
        return
    html_page = urllib2.urlopen("http://servicios.jcyl.es/esco/datosTiempoReal.action?provincia=" + municipiosCalidadAire[user["municipio"].lower().encode('utf-8')]["provincia"] + "&estacion=" + municipiosCalidadAire[user["municipio"].lower().encode('utf-8')]["value"] + "&tamanoPagina=50&consultar=1")
    soup = BeautifulSoup(html_page,"html.parser")
    table = soup.findAll('tr','success')
    if table:
        row = table[-1]
    else:
        send_message(bot=bot,chat_id=user["_id"],
            text=u'Todavía no hay datos sobre la calidad de aire de hoy, vuelve a consultarlo más tarde.',
            parse_mode=ParseMode.MARKDOWN)
        return

    data = [ cell.get_text(strip=True) for cell in row.findAll('td')]
    caqi = CAQI([float(x.replace(',','.').encode('utf-8')) if x is not u'' else 0 for x in data[1:8]])
    data[1:8] = ['{:5.1f}'.format(float(x.replace(',','.'))).replace('.',',') if x is not u'' else u'  —' for x in data[1:8]]

    send_message(bot=bot,chat_id=update.effective_chat.id,
        text=u'*Calidad del aire*: `' + caqi + u'`\n[' + data[-1] + u'](https://www.google.com/maps?q=' + str(estaciones[municipiosCalidadAire[user["municipio"].lower().encode('utf-8')]["estacion"]]["lat"]) + u',' + str(estaciones[municipiosCalidadAire[user["municipio"].lower().encode('utf-8')]["estacion"]]["lon"]) + u') ' + data[0] + u'\n```\nCO   (mg/m³): ' + data[1] + u'\nNO   (μg/m³): ' + data[2] + u'\nNO₂  (μg/m³): ' + data[3] + u'\nO₃   (μg/m³): ' + data[4] + u'\nPM10 (μg/m³): ' + data[5] + u'\nPM25 (μg/m³): ' + data[6] + u'\nSO₂  (μg/m³): ' + data[7] + u'```',
        parse_mode=ParseMode.MARKDOWN)

def CAQI(mediciones):
    CO,NO,NO2,O3,PM10,PM25,SO2 = mediciones
    indexes = [0,0,0,0,0,0]
    if CO < 5000:
        indexes[0] = 25*(CO - 0)/(5000 - 0) + 0
    elif CO < 7500:
        indexes[0] = 25*(CO - 5000)/(7500 - 5000) + 25
    elif CO < 10000:
        indexes[0] = 25*(CO - 7500)/(10000 - 7500) + 50
    elif CO < 20000:
        indexes[0] = 25*(CO - 10000)/(20000 - 10000) + 75
    else:
        indexes[0] = 101
    if NO2 < 50:
        indexes[1] = 25*(NO2 - 0)/(50 - 0) + 0
    elif NO2 < 100:
        indexes[1] = 25*(NO2 - 50)/(100 - 50) + 25
    elif NO2 < 200:
        indexes[1] = 25*(NO2 - 100)/(200 - 100) + 50
    elif NO2 < 400:
        indexes[1] = 25*(NO2 - 200)/(400 - 200) + 75
    else:
        indexes[1] = 101
    if O3 < 60:
        indexes[2] = 25*(O3 - 0)/(60 - 0) + 0
    elif O3 < 100:
        indexes[2] = 25*(O3 - 60)/(120 - 60) + 25
    elif O3 < 180:
        indexes[2] = 25*(O3 - 120)/(180 - 120) + 50
    elif O3 < 240:
        indexes[2] = 25*(O3 - 180)/(240 - 180) + 75
    else:
        indexes[2] = 101
    if PM10 < 25:
        indexes[3] = 25*(PM10 - 0)/(25 - 0) + 0
    elif PM10 < 50:
        indexes[3] = 25*(PM10 - 25)/(50 - 25) + 25
    elif PM10 < 90:
        indexes[3] = 25*(PM10 - 50)/(90 - 50) + 50
    elif PM10 < 180:
        indexes[3] = 25*(PM10 - 90)/(180 - 90) + 75
    else:
        indexes[3] = 101
    if PM25 < 15:
        indexes[4] = 25*(PM25 - 0)/(15 - 0) + 0
    elif PM25 < 30:
        indexes[4] = 25*(PM25 - 15)/(30 - 15) + 25
    elif PM25 < 55:
        indexes[4] = 25*(PM25 - 30)/(55 - 30) + 50
    elif PM25 < 110:
        indexes[4] = 25*(PM25 - 55)/(110 - 55) + 75
    else:
        indexes[4] = 101
    if SO2 < 50:
        indexes[5] = 25*(SO2 - 0)/(50 - 0) + 0
    elif SO2 < 100:
        indexes[5] = 25*(SO2 - 50)/(100 - 50) + 25
    elif SO2 < 350:
        indexes[5] = 25*(SO2 - 100)/(350 - 100) + 50
    elif SO2 < 500:
        indexes[5] = 25*(SO2 - 350)/(500 - 350) + 75
    else:
        indexes[5] = 101
    #print("CO " + str(CO) + " NO2 " + str(NO2) + " O3 " + str(O3) + " PM10 " + str(PM10) + " PM25 " + str(PM25) + " SO2 " + str(SO2))
    #print(indexes)
    caqi = max(indexes)
    if caqi == 101:
        return ">100"
    else:
        return str(int(caqi))

@run_async
def mapa(bot,update):
    if update.message.text.lower() == "/mapa regional":
        mapaRegional(bot,update)
        return
    logger.info(u'el usuario %s quiere un mapa',str(update.effective_chat.id))
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    espera = send_message(bot=bot,chat_id=update.effective_chat.id,text=u'_enviando mapa..._\n⏳ (puede tardar unos segundos)\n' + u'\[`' + u'.'*25 + u'`]',parse_mode=ParseMode.MARKDOWN)
    hora = datetime.datetime.utcnow()
    hora = hora - datetime.timedelta(minutes=hora.minute % 30)
    font = ImageFont.truetype("OpenSans.ttf",20)
    logo = Image.open('minilogo.png')
    images = []
    for i in range(23,0,-1):
        try:
            bot.edit_message_text(chat_id=update.effective_chat.id,message_id = espera.message_id,text=u'_enviando mapa..._\n⏳ (puede tardar unos segundos)\n' + u'\[`' + u':'*(25-i-1) + u'.'*(i+1) + u'`]',parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        url = u'http://www.aemet.es/imagenes_d/eltiempo/observacion/radar/' + (hora - datetime.timedelta(minutes=i*30)).strftime('%Y%m%d%H%M') + u'_r8pb.gif'
        try:
            img = Image.open(StringIO(cached_sess.get(url,timeout=2).content))
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((2,2),"@"+BOTNAME,fill="white",font=font)
            img.paste(logo,(2,399))
            images.append(numpy.array(img))
            del img
        except requests.exceptions.RequestException as err:
            logger.error(u'URLError de %s porque pasa %s',str(update.effective_chat.id),str(err))
            continue
    output = StringIO()
    imageio.mimsave(output,images,format = "gif", duration = 0.5)
    output.seek(0)
    send_document(bot,chat_id=update.effective_chat.id, document=output)
    output.close()
    try:
        bot.delete_message(chat_id=update.effective_chat.id,message_id = espera.message_id)
    except:
        bot.delete_message(chat_id=update.effective_chat.id,message_id = espera.message_id)
        pass

@run_async
def mapaRegional(bot,update):
    logger.info(u'el usuario %s quiere un mapa regional',str(update.effective_chat.id))
    user = getUser(bot, update)
    if "idMunicipio" not in user:
        send_message(bot=bot,chat_id=user["_id"],
            text=textoMunicipio(None),
            parse_mode=ParseMode.MARKDOWN)
        return
    bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    espera = send_message(bot=bot,chat_id=user["_id"],text=u'_enviando mapa..._\n⏳ (puede tardar unos segundos)\n' + u'\[`' + u'.'*25 + u'`]',parse_mode=ParseMode.MARKDOWN)
    hora = datetime.datetime.utcnow()
    hora = hora - datetime.timedelta(minutes=((hora.minute - 20) % 10))
    font = ImageFont.truetype("OpenSans.ttf",20)
    logo = Image.open('minilogo.png')
    images = []
    for i in range(47,0,-1):
        if i%2:
            try:
                bot.edit_message_text(chat_id=user["_id"],message_id = espera.message_id,text=u'_enviando mapa..._\n⏳ (puede tardar unos segundos)\n' + u'\[`' + u':'*((50-i)/2) + u'.'*(25-(50-i)/2) + u'`]',parse_mode=ParseMode.MARKDOWN)
            except:
                pass
        url = u'http://www.aemet.es/imagenes_d/eltiempo/observacion/radar/' + (hora - datetime.timedelta(minutes=i*10)).strftime('%Y%m%d%H%M') + u'_r8' + mapaCodigo[user["idMunicipio"][:2]] + u'.gif'
        try:
            img = Image.open(StringIO(cached_sess.get(url,timeout=2).content))
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((2,20),"@"+BOTNAME,fill="white",font=font)
            img.paste(logo,(428,2))
            images.append(numpy.array(img))
            del img
        except requests.exceptions.RequestException as err:
            logger.error(u'URLError de %s porque pasa %s',str(update.effective_chat.id),str(err))
            continue
    output = StringIO()
    imageio.mimsave(output,images,format = "gif", duration = 0.25)
    output.seek(0)
    send_document(bot,chat_id=update.effective_chat.id, document=output)
    output.close()
    try:
        bot.delete_message(chat_id=user["_id"],message_id = espera.message_id)
    except:
        bot.delete_message(chat_id=user["_id"],message_id = espera.message_id)
        pass

def send_message(bot,chat_id,text,parse_mode=ParseMode.HTML,reply_markup=None,repeticiones=0):
    if repeticiones < 5:
        try:
            time.sleep(0.1)
            bot.send_message(chat_id=chat_id,text=text,parse_mode=parse_mode,reply_markup=reply_markup,disable_web_page_preview=True)
            return
        except TimedOut:
            logger.info('timed out %s al enviar mensaje', str(repeticiones))
            send_message(bot=bot,chat_id=chat_id,text=text,parse_mode=parse_mode,reply_markup=reply_markup,repeticiones = (repeticiones+1))
    else:
        logger.error('timed out repetido al enviar mensaje')

def send_document(bot,chat_id,document,repeticiones=0):
    if repeticiones < 3:
        try:
            return bot.send_document(chat_id=chat_id,document=document)
        except TimedOut:
            logger.info('timed out %s al enviar documento', str(repeticiones))
            send_document(bot=bot,chat_id=chat_id,document=document,repeticiones = (repeticiones+1))
    else:
        logger.error('timed out repetido al enviar documento')

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    try:
        raise error
    except Unauthorized:
        # remove update.effective_chat.id from conversation list
        user = getUser(bot, update)
        collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": False}}, upsert=False)
        logger.error('unauthorized %s',update.effective_chat.id)
    except BadRequest:
        # handle malformed requests - read more below!
        logger.error('bad request')
    except TimedOut:
        # handle slow connection problems
        logger.error('timed out')
    except NetworkError:
        # handle other connection problems
        logger.error('network error')
    except ChatMigrated as e:
        # the chat_id of a group has changed, use e.new_chat_id instead
        logger.error('chat migrated')
    except TelegramError:
        # handle all other telegram related errors
        logger.error('telegram error')


def main():
    """Start the bot."""
    # Database
    mongod = subprocess.Popen(['mongod', '--dbpath', os.path.expanduser("./data")],stdout=open(os.devnull, 'wb'))

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TELEGRAMTOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    jq = updater.job_queue

    jq.run_daily(alerta,datetime.time(21))
    #jq.run_once(bugFix,60)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_member))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, left_chat_member))
    dp.add_handler(CommandHandler("ayuda", help))
    dp.add_handler(CommandHandler("tiempo", comandoTiempo))
    dp.add_handler(CommandHandler("tiempoMenu", comandoTiempoMenu))
    dp.add_handler(CommandHandler(u"tiempoMenú", comandoTiempoMenu))
    dp.add_handler(CommandHandler("municipio", municipio))
    dp.add_handler(CommandHandler("configurar", configurar))
    dp.add_handler(CommandHandler("configuracion", configurar))
    dp.add_handler(CommandHandler(u"configuración", configurar))
    dp.add_handler(CommandHandler("mapa", mapa))
    dp.add_handler(CommandHandler("mapaRegional", mapaRegional))
    dp.add_handler(CommandHandler("calidadAire", calidadAire))

    dp.add_handler(CallbackQueryHandler(configuracionMenu))

    # log all errors
    dp.add_error_handler(error)

    logger.info(u'comenzamos a las %s',datetime.datetime.now().time())

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
