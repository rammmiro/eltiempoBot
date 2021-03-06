#!/usr/bin/env python
# -*- coding: utf-8 -*-
estados_cielo = {}
estados_cielo['Despejado'] = u'☀️'
estados_cielo['Despejado noche'] = u'🌙'
estados_cielo['Poco nuboso'] = u'🌤'
estados_cielo['Poco nuboso noche'] = u'🌤🌙'
estados_cielo['Intervalos nubosos'] = u'⛅️'
estados_cielo['Intervalos nubosos noche'] = u'⛅️'
estados_cielo['Nuboso'] = u'🌥'
estados_cielo['Nuboso noche'] = u'🌥🌙'
estados_cielo['Muy nuboso'] = u'☁️☁️'
estados_cielo['Cubierto'] = u'☁️☁️☁️'
estados_cielo['Nubes altas'] = u'🌤'
estados_cielo['Nubes altas noche'] = u'🌤🌙'
estados_cielo['Intervalos nubosos con lluvia escasa'] = u'🌦'
estados_cielo['Intervalos nubosos con lluvia escasa noche'] = u'🌦🌙'
estados_cielo['Nuboso con lluvia escasa'] = u'🌧'
estados_cielo['Nuboso con lluvia escasa noche'] = u'🌧🌙'
estados_cielo['Muy nuboso con lluvia escasa'] = u'🌧🌧'
estados_cielo['Cubierto con lluvia escasa'] = u'🌧🌧🌧'
estados_cielo['Intervalos nubosos con lluvia'] = u'🌦☔️'
estados_cielo['Intervalos nubosos con lluvia noche'] = u'🌦☔️🌙'
estados_cielo['Nuboso con lluvia'] = u'🌧☔️'
estados_cielo['Nuboso con lluvia noche'] = u'🌧☔️🌙'
estados_cielo['Muy nuboso con lluvia'] = u'🌧🌧☔️'
estados_cielo['Cubierto con lluvia'] = u'🌧🌧🌧☔️'
estados_cielo['Intervalos nubosos con nieve escasa'] = u'⛅️🌨'
estados_cielo['Intervalos nubosos con nieve escasa noche'] = u'⛅️🌨🌙'
estados_cielo['Nuboso con nieve escasa'] = u'🌨'
estados_cielo['Nuboso con nieve escasa noche'] = u'🌨🌙'
estados_cielo['Muy nuboso con nieve escasa'] = u'🌨🌨'
estados_cielo['Cubierto con nieve escasa'] = u'🌨🌨🌨'
estados_cielo['Intervalos nubosos con nieve'] = u'⛅️❄️'
estados_cielo['Intervalos nubosos con nieve noche'] = u'⛅️❄️🌙'
estados_cielo['Nuboso con nieve'] = u'🌨❄️'
estados_cielo['Nuboso con nieve noche'] = u'🌨❄️🌙'
estados_cielo['Muy nuboso con nieve'] = u'🌨🌨❄️'
estados_cielo['Cubierto con nieve'] = u'🌨🌨🌨❄️'
estados_cielo['Intervalos nubosos con tormenta'] = u'⛅️⚡️'
estados_cielo['Intervalos nubosos con tormenta noche'] = u'⛅️⚡️🌙'
estados_cielo['Nuboso con tormenta'] = u'🌩'
estados_cielo['Nuboso con tormenta noche'] = u'🌩🌙'
estados_cielo['Muy nuboso con tormenta'] = u'🌩🌩'
estados_cielo['Cubierto con tormenta'] = u'🌩🌩🌩'
estados_cielo['Intervalos nubosos con tormenta y lluvia escasa'] = u'🌦⛈'
estados_cielo['Intervalos nubosos con tormenta y lluvia escasa noche'] = u'🌦⛈🌙'
estados_cielo['Nuboso con tormenta y lluvia escasa'] = u'⛈'
estados_cielo['Nuboso con tormenta y lluvia escasa noche'] = u'⛈🌙'
estados_cielo['Muy nuboso con tormenta y lluvia escasa'] = u'⛈⛈'
estados_cielo['Cubierto con tormenta y lluvia escasa'] = u'⛈⛈⛈'
estados_cielo['Chubascos'] = u'💦'
estados_cielo['Tormenta'] = u'⚡️'
estados_cielo['Granizo'] = u'❄️'
estados_cielo['Bruma'] = u'💨'
estados_cielo['Niebla'] = u'💨'
estados_cielo['Calima'] = u'💨'

direccion_viento = {}
direccion_viento['NO'] = u'↖️'
direccion_viento['N'] = u'⬆️'
direccion_viento['NE'] = u'↗️'
direccion_viento['O'] = u'⬅️'
direccion_viento['C'] = u''
direccion_viento['E'] = u'➡️'
direccion_viento['SO'] = u'↙️'
direccion_viento['S'] = u'⬇️'
direccion_viento['SE'] = u'↘️'

num_emoji = {}
num_emoji[u'0️⃣'] = 0
num_emoji[u'1️⃣'] = 1
num_emoji[u'2️⃣'] = 2
num_emoji[u'3️⃣'] = 3
num_emoji[u'4️⃣'] = 4
num_emoji[u'5️⃣'] = 5
num_emoji[u'6️⃣'] = 6
num_emoji[u'7️⃣'] = 7
num_emoji[u'8️⃣'] = 8
num_emoji[u'9️⃣'] = 9
num_emoji[u'🔟'] = 10

#active_emoji = {True: 'ok', False: u'no'}
active_emoji = {True: u'✅', False: u'❌'}
alerta_text = {0: u'🔕 No molestar', 1: u'🔔 Alerta', 2: u'☔️ Solo lluvia'}
predicciones = {
    "1": {"dias": range(1), "horas": {"hoy": [], "manyana": []}},
    "2": {"dias": range(2), "horas": {"hoy": [], "manyana": []}},
    "3": {"dias": range(3), "horas": {"hoy": [], "manyana": []}},
    "7": {"dias": range(7), "horas": {"hoy": [], "manyana": []}},
    "HOY2H": {"dias": [], "horas": {"hoy": range(0,24,2), "manyana": []}},
    "MANYANA2H": {"dias": [], "horas": {"hoy": [], "manyana": range(8,24,2)}},
    "HOYMANYANA2H": {"dias": [], "horas": {"hoy": range(0,24,2), "manyana": range(0,24,2)}}
    }

alertas = {
    "1": {"dias": range(1,2), "horas": {"hoy": [], "manyana": []}},
    "2": {"dias": range(1,3), "horas": {"hoy": [], "manyana": []}},
    "3": {"dias": range(1,4), "horas": {"hoy": [], "manyana": []}},
    "6": {"dias": range(1,7), "horas": {"hoy": [], "manyana": []}},
    "MANYANA2H": {"dias": [], "horas": {"hoy": [], "manyana": range(8,24,2)}}
    }

dia_semana = [u'lun',u'mar',u'mié',u'jue',u'vie',u'sáb',u'dom']

mapaCodigo = {}
mapaCodigo["01"] = "ss"
mapaCodigo["02"] = "mu"
mapaCodigo["03"] = "va"
mapaCodigo["04"] = "am"
mapaCodigo["05"] = "vd"
mapaCodigo["06"] = "cc"
mapaCodigo["07"] = "pm"
mapaCodigo["08"] = "ba"
mapaCodigo["09"] = "vd"
mapaCodigo["10"] = "cc"
mapaCodigo["11"] = "ml"
mapaCodigo["12"] = "va"
mapaCodigo["13"] = "ma"
mapaCodigo["14"] = "se"
mapaCodigo["15"] = "co"
mapaCodigo["16"] = "ma"
mapaCodigo["17"] = "ba"
mapaCodigo["18"] = "am"
mapaCodigo["19"] = "ma"
mapaCodigo["20"] = "ss"
mapaCodigo["21"] = "se"
mapaCodigo["22"] = "za"
mapaCodigo["23"] = "am"
mapaCodigo["24"] = "sa"
mapaCodigo["25"] = "ba"
mapaCodigo["26"] = "ss"
mapaCodigo["27"] = "co"
mapaCodigo["28"] = "ma"
mapaCodigo["29"] = "ml"
mapaCodigo["30"] = "mu"
mapaCodigo["31"] = "ss"
mapaCodigo["32"] = "co"
mapaCodigo["33"] = "sa"
mapaCodigo["34"] = "vd"
mapaCodigo["35"] = "ca"
mapaCodigo["36"] = "co"
mapaCodigo["37"] = "cc"
mapaCodigo["38"] = "ca"
mapaCodigo["39"] = "ss"
mapaCodigo["40"] = "vd"
mapaCodigo["41"] = "se"
mapaCodigo["42"] = "vd"
mapaCodigo["43"] = "ba"
mapaCodigo["44"] = "za"
mapaCodigo["45"] = "ma"
mapaCodigo["46"] = "va"
mapaCodigo["47"] = "vd"
mapaCodigo["48"] = "ss"
mapaCodigo["49"] = "vd"
mapaCodigo["50"] = "za"
mapaCodigo["51"] = "ml"
mapaCodigo["52"] = "am"
