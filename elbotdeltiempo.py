#!/usr/bin/env python
# -*- coding: utf-8 -*-

# mongod --dbpath ./data
# python elbotdeltiempo.py

"""El Bot del Tiempo (beta)

Este programa está bajo una licencia GNU GENERAL PUBLIC LICENSE.

La información metereológica que muestra El Bot del Tiempo ha sido elaborada por la Agencia Estatal de Meteorología (© AEMET). AEMET no participa, patrocina, o apoya la reutilización de sus datos que se lleva a cabo.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)
import googlemaps
import logging
import urllib
import urllib2
import xml.etree.ElementTree as etree
import datetime
from pymongo import MongoClient
import subprocess
import os
from municipios import municipios
from auxiliar import estados_cielo, direccion_viento, num_emoji, active_emoji, alerta_text, dia_semana, predicciones, alertas
from config import TELEGRAMTOKEN, GOOGLEMAPSKEY, BOTNAME

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename='./logs/'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.log', filemode='w',level=logging.INFO)
logger = logging.getLogger(__name__)

gmaps = googlemaps.Client(key=GOOGLEMAPSKEY)

client = MongoClient()
db = client.elbotdeltiempodb
collection = db.users

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text(u'¡Hola! Soy @' + BOTNAME + u'.')
    if collection.find_one({"_id":update.effective_chat.id}) is None:
        collection.insert({"_id":update.effective_chat.id})
    if update.message.chat.type == "private":
        collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": True, "configurarTiempo": predicciones["configurandoPrediccion3"], "viento": True, "sensacionTermica": True, "humedadRelativa": True, "alerta": 1, "configurarAlerta": alertas["configurandoAlerta1"], "tipo":update.message.chat.type, "nombre": update.message.chat.first_name, "alias": update.message.chat.username}}, upsert=False)
    else:
        collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": True, "configurarTiempo": predicciones["configurandoPrediccion3"], "viento": True, "sensacionTermica": True, "humedadRelativa": True, "alerta": alertas["configurandoAlerta1"], "configurarAlerta": {"dias":[1]}, "tipo":update.message.chat.type, "titulo": update.message.chat.title}}, upsert=False)
    user = collection.find_one({"_id":update.effective_chat.id})
    logger.info(u'nuevo usuario con id: ' + user["_id"] + u' se ha registrado')
    if "municipio" not in user:
        bot.send_message(chat_id=update.effective_chat.id,
            text=u'Para empezar tienes que decirme cuál es tu municipio. Hazlo enviando el comando `/municipio` seguido del nombre. Así:\n`/municipio Soria`',
            parse_mode=ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=update.effective_chat.id,
            text=u'Estoy configurado para enviarte información de *' + user["municipio"] + u'*. Puedes cambiarlo enviando el comando `/municipio` seguido del nombre. Así:\n`/municipio ' + user["municipio"] +'`',
            parse_mode=ParseMode.MARKDOWN)
    bot.send_message(chat_id=update.effective_chat.id,
        text=u'Para que te diga el tiempo envía /tiempo.\nPara acceder a todas las opciones pulsa /configuracion.\nPara tener más ayuda manda /ayuda.',
        parse_mode=ParseMode.MARKDOWN)

def getUser(bot, update):
    user = collection.find_one({"_id":update.effective_chat.id})
    if user is None:
        start(bot, update)
        user = collection.find_one({"_id":update.effective_chat.id})
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
    update.message.reply_text(u'Todavía estoy en beta! Pronto añadiré más ayuda.')

def municipio(bot, update):
    user = getUser(bot, update)
    if update.message.text == "/municipio":
        if "municipio" in user:
            bot.send_message(chat_id=update.effective_chat.id,
                text=u'Estoy configurado para enviarte información de *' + user["municipio"] + u'*. Puedes cambiarlo enviando el comando `/municipio` seguido del nombre. Así:\n`/municipio ' + user["municipio"] +'`',
                parse_mode=ParseMode.MARKDOWN)
        else:
            bot.send_message(chat_id=update.effective_chat.id,
                text=u'Envia el comando `/municipio` seguido del nombre. Así:\n`/municipio Soria`',
                parse_mode=ParseMode.MARKDOWN)
        return
    geocode_result = gmaps.geocode(update.message.text[update.message.text.index(' ') + 1:])
    if not geocode_result:
        logger.warning(u'El usuario %s ha buscado el municipio %s, que no existe.', str(user["_id"]),update.message.text[update.message.text.index(' ') + 1:])
        bot.send_message(chat_id=update.effective_chat.id,
            text=u'¿Estás seguro de que has escrito bien el nombre de tu municipio? Envia el comando `/municipio` seguido del nombre. Así:\n`/municipio Soria`',
            parse_mode=ParseMode.MARKDOWN)
        return
    reverse_geocode_result = gmaps.reverse_geocode((geocode_result[0]["geometry"]["location"]["lat"], geocode_result[0]["geometry"]["location"]["lng"]))
    try:
        pais = next((item for item in reverse_geocode_result[0]['address_components'] if item['types'][0] == 'country'),None)['short_name']
    except StopIteration:
        logger.warning(u'stop iteration: sin país')
        bot.send_message(chat_id=update.effective_chat.id,
            text=u'¿Estás seguro de que has escrito bien el nombre de tu municipio? Envia el comando `/municipio` seguido del nombre. Así:\n`/municipio Soria`',
            parse_mode=ParseMode.MARKDOWN)
        return
    if pais != 'ES':
        bot.send_message(chat_id=update.effective_chat.id,
            text=u'Solo conozco el tiempo de municipios españoles, lo siento.',
            parse_mode=ParseMode.MARKDOWN)
        logger.warning(u'Ubicación en: %s',pais)
    else:
        for direccion in reverse_geocode_result:
            try:
                nombre = next(item for item in direccion['address_components'] if item['types'][0] == 'locality')['long_name'].encode('utf-8')
                if municipios.get(nombre.decode('utf-8').lower().encode('utf-8')) == None: nombre = next(item for item in direccion['address_components'] if item['types'][0] == 'administrative_area_level_4')['long_name'].encode('utf-8')
                codigoMunicipio = municipios[nombre.decode('utf-8').lower().encode('utf-8')]
                collection.update_one({'_id':update.effective_chat.id}, {"$set": {"municipio": nombre, "idMunicipio": codigoMunicipio}}, upsert=False)
                bot.send_message(chat_id=update.effective_chat.id,
                    text=u'¡Municipio actualizado! 🌍\nAhora cuando me envíes el comando /tiempo te responderé con la predicción para *' + nombre + '*.',
                    parse_mode=ParseMode.MARKDOWN)
                logger.info(u'%s ha cambiado su ubicación a %s (%s)',str(user["_id"]),nombre,str(codigoMunicipio).decode('utf-8'))
                return
            except StopIteration:
                logger.warning('stop iteration')
                bot.send_message(chat_id=update.effective_chat.id,
                    text=u'¿Estás seguro de que has escrito bien el nombre de tu municipio? Envia el comando `/municipio` seguido del nombre. Así:\n`/municipio Soria`',
                    parse_mode=ParseMode.MARKDOWN)
                continue
def comandoTiempo(bot,update):
    user = getUser(bot, update)
    tiempo(bot,user,user["configurarTiempo"]["dias"],user["configurarTiempo"]["horas"]["hoy"],user["configurarTiempo"]["horas"]["manyana"],False)

def alerta(bot, job): #se puede combinar con tiempo
    logger.info(u'se está enviando la alerta')
    for user in collection.find({"$and":[{"activo": True}, {"alerta": {"$gte": 1}}]}):
        if user["alerta"] == 1:
            tiempo(bot,user,user["configurarAlerta"]["dias"],user["configurarAlerta"]["horas"]["hoy"],user["configurarAlerta"]["horas"]["manyana"],False)
        elif user["alerta"] == 2:
            tiempo(bot,user,user["configurarAlerta"]["dias"],user["configurarAlerta"]["horas"]["hoy"],user["configurarAlerta"]["horas"]["manyana"],True)

def tiempo(bot,user,prediccionDias,prediccionHoy,prediccionManyana,soloLluvia):
    if "idMunicipio" not in user:
        bot.send_message(chat_id=user["_id"],
            text=u"Primero tienes que decirme tu municipio con `/municipio`. Por ejemplo:\n`/municipio Soria`",
            parse_mode=ParseMode.MARKDOWN)
        return
    treeDia = etree.parse(urllib2.urlopen('http://www.aemet.es/xml/municipios/localidad_' + str(user["idMunicipio"]) + '.xml'))
    rootDia = treeDia.getroot()
    dias = [rootDia[4][i] for i in prediccionDias]
    for dia in dias:
        lluvia = next(item for item in dia.findall('prob_precipitacion') if item.text is not None).text
        if not soloLluvia or lluvia != "0":
            bot.send_message(chat_id=user["_id"],
                text=prediccion(dia,user),
                parse_mode=ParseMode.MARKDOWN)
    now = datetime.datetime.now()
    treeHora = etree.parse(urllib2.urlopen('http://www.aemet.es/xml/municipios_h/localidad_h_' + str(user["idMunicipio"]) + '.xml'))
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
                bot.send_message(chat_id=user["_id"],
                    text=prediccionHora(today,hora,user),
                    parse_mode=ParseMode.MARKDOWN)
    for hora in prediccionManyana:
        if tomorrow.find('./estado_cielo[@periodo="%s"]' % str(hora).zfill(2)) is not None:
            lluvia = tomorrow.find('./precipitacion[@periodo="%s"]' % str(hora).zfill(2)).text
            if not soloLluvia or lluvia != "0":
                bot.send_message(chat_id=user["_id"],
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
    if query["data"] == "configurarPrediccion":
        keyboard = [[InlineKeyboardButton(u"1 día", callback_data='configurandoPrediccion1'),
                     InlineKeyboardButton(u"2 días", callback_data='configurandoPrediccion2')],
                    [InlineKeyboardButton(u"3 días", callback_data='configurandoPrediccion3'),
                     InlineKeyboardButton(u"7 días", callback_data='configurandoPrediccion7')],
                    [InlineKeyboardButton(u"Hoy (cada 2 horas)", callback_data='configurandoPrediccionHOY2H')],
                    [InlineKeyboardButton(u"Mañana (cada 2 horas)", callback_data='configurandoPrediccionMANYANA2H')],
                    [InlineKeyboardButton(u"Hoy y Mañana (cada 2 h)", callback_data='configurandoPrediccionHOYMANYANA2H')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(text=u"Configura la predicción",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
        return
    if query["data"].startswith("configurandoPrediccion"):
        user["configurarTiempo"] = predicciones[query["data"]]
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
        bot.edit_message_text(text="Configura la alerta",
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=reply_markup)
        return
    if query["data"].startswith("configurandoAlerta"):
        user["configurarAlerta"] = alertas[query["data"]]
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
    #cambiar la configuración de viento / sensación térmica / humedad relativa
    cambiarConfiguracion(bot,user,query["data"],query)
    return

def cambiarConfiguracion(bot,user,opcion,query):
    user[opcion] = not user[opcion]
    collection.update_one({'_id':user["_id"]}, {"$set": {opcion: user[opcion]}}, upsert=False)
    query.edit_message_reply_markup(reply_markup=crearTecladoConfigurar(user))
    return

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    try:
        raise error
    except Unauthorized:
        # remove update.message.chat_id from conversation list
        user = getUser(bot, update)
        collection.update_one({'_id':update.effective_chat.id}, {"$set": {"activo": False}}, upsert=False)
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

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_member))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, left_chat_member))
    dp.add_handler(CommandHandler("ayuda", help))
    dp.add_handler(CommandHandler("tiempo", comandoTiempo))
    dp.add_handler(CommandHandler("municipio", municipio))
    dp.add_handler(CommandHandler("configurar", configurar))

    dp.add_handler(CallbackQueryHandler(configuracionMenu))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()