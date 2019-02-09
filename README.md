[![Telegram bot](https://img.shields.io/badge/Telegram%20Bot-%40eltiempoBot-blue.svg)](https://t.me/eltiempoBot)
# eltiempoBot
El Bot del Tiempo

## Instalación
Asumimos que está instalado `python`, `pip`, `git` y `mongoDB`. Para instalar esta última base de datos visite [MongoDB](https://www.mongodb.com/download-center?jmp=nav#community).

Ha de disponer también de un TOKEN de telegram y una API KEY de Google Maps.

```
# clone el repositorio
git clone https://github.com/rammmiro/eltiempoBot.git

# entre en el directorio clonado
cd ./eltiempoBot

# instale los paquetes de python necesarios
pip install -r requirements.txt --user

# copie el archivo de configuración y añada el TOKEN de telegram y la API KEY de google maps.
cp config.example.py config.py
nano config.py

# ejecute la base de datos
sudo service mongod start

# ejecute el bot
python elbotdeltiempo.py
```

## Licencias

El logo utilizado es una versión del [icono](https://www.flaticon.com/free-icon/cloudy-day-outlined-weather-interface-symbol_53562) de [Rami McMin](https://www.flaticon.com/authors/rami-mcmin) publicado en [www.flaticon.com](https://www.flaticon.com/) con licencia CC 3.0 BY.

La librería de bots de telegram utilizada es [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot), publicada bajo licencia LGPL-3.
