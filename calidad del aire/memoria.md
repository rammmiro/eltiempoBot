**Autor**: Ramiro Martínez Pinilla

**Título del proyecto**: El Bot del Tiempo

**Categoría**: Productos y Servicios

**Estudiante**: estudiante de doctorado en la Universitat Politècnica de Catalunya

**URL**: [https://telegram.me/eltiempoBot](https://telegram.me/eltiempoBot)

Memoria:
-------

Recientemente han aumentado las menciones a los índices de calidad del aire en los medios de comunicación. La información sobre la calidad del aire es relevante para poder decidir en qué horas es más conveniente ventilar los espacios, o si es adecuado realizar una actividad física en el exterior, especialmente para personas con afecciones respiratorias.

Actualmente esta información está disponible pero no es especialmente accesible. Las fuentes de información no están adaptadas a su visualización en dispositivos móviles, no incluyen todas las estaciones de la red de control de la calidad del aire, o directamente no funcionan.

Creeamos a su vez que una web o una aplicación específica con múltiples opciones de configuración puede ser de interés para los expertos, pero desincentiva el acceso a la información por parte de la población general.

Por ello es el objetivo de este proyecto hacer accesibles los datos sobre la calidad del aire en Castilla y León a través de un bot de Telegram. Esta popular aplicación de mensajería instantánea (con clientes móviles, de escritorio y vía web, y con una interfaz similar a Whatsapp) permite interactuar con nuestros contactos y con "bots", una suerte de programas que responden a nuestros mensajes de chat.

El autor de este proyecto desarrolló hace unos meses @eltiempoBot (disponible a través de [http://telegram.me/eltiempoBot](http://telegram.me/eltiempoBot)), especializado en enviar información metereológica obtenida de AEMet a través de esta aplicación de mensajería. Se trata de un proyecto personal que comenzó para conocer la previsión meteorológica del dia siguiente a través de mensajes de texto automáticos, sin necesidad de tener que buscar activamente la información ni instalar ninguna aplicación dedicada. Actualmente incluye la posibilidad de recibir predicciones meteorológicas por horas o días, alertas cuando haya posibilidad de precipitaciones y acceso a animaciones de radar con la cantidad de precipitaciones. Al ser accesible para cualquier usuario de Telegram actualmente alrededor de medio millar de personas lo utilizan diariamente en toda España.

Este proyecto ha consistido en la integración de @eltiempoBot con los datos abiertos de calidad del aire (por horas) que proporciona la Junta de Castilla y León. De esta forma, si el bot está configurado con un municipio de Castilla y León, responderá al comando `/calidadAire` con los datos más actualizados de la estación más cercana (y un enlace a la ubicación de esta estación en google maps). También es posible obtener esta información desde el menú accesible con el comando `/tiempoMenu`.

Además de los datos brutos con la cantidad de partículas en el aire el bot calcula y muestra el índice de calidad del aire. En concreto se utilizan los datos brutos para calcular el Indice de Calidad del Aire Común (CAQI por sus siglas en inglés) a partir de los umbrales establecidos. Este índice estandarizado a nivel europeo permite resumir la calidad del aire con una escala de 0 a 100, donde 0 representaría ausencia de partículas y 100 representaría un entorno muy contaminado. De esta forma con un vistazo es posible conocer el nivel relativo de contaminación y poder interpretar los valores absolutos de los datos brutos. Los valores obtenidos con este índice no permiten establecer el nivel exacto de riesgo para la salud que supone la contaminación, pero sí sirven como indicador, para poder establecer comparativas y para concienciar a la población. Creemos que es importante que las apliaciones que utilicen los datos abiertos tengan un valor añadido, como es en este caso el cálculo de este índice, para hacer la información más accesible y/o fácil de interpretar.

Para la obtención de estos datos se utilizan evidentemente las mediciones en tiempo real de la red de estaciones, pero además se han empleado el conjunto de datos referentes a las "Estaciones de control de la calidad del aire" y el "Registro de municipios de Castilla y León" sobre los municipios, pues es imprescindible conocer la ubicación exacta de las estaciones y las coordenadas de cada municipio para poder asignar a cada uno de estos últimos los datos de la estación más cercana.

En este punto quisiéramos comentar algunas cuestiones técnicas. La publicación de los datos hace posible su reutilización en proyectos como este, pero para ello es necesario que estén correctamente estructurados y actualizados.

Las coordenadas de las estaciones de calidad del aire utilizan hasta tres símbolos diferentes (’’ ” ") para indicar los segundos, y algo parecido sucede con los minutos. Esto dificulta el procesamiento automatizado de esta información.

La nomenclatura de algunos de los municipios no coincide con las denominaciones oficiales del Nomenclátor Geográfico Básico de España elaborado por el Instituto Geográfico Nacional. Esto sucede por la omisión (o inclusión) de tildes y otros errores tipográficos en algunos municipios que aparecen en el registro de la siguiente forma [¿incorrecta?]: Aguilar de Campoó, Andavias, Carrascal del Rio, Casaseca de Campean, Castillejo de Martin Viejo, Castillejo de Mesleon, Gallegos del Rio, La Vidola, Lanzahita, Lastras de Cuellar, Moriñigo, Piedrahita, Pobladura de Pelayo Garcia, Santa Maria del Mercadillo, Santa Maria Rivarredonda, Valdefuentes de Sangusin, Villacastin, Villamartíin de Don Sancho, Villaquiran de la Puebla, Villar del Rio.

Este tipo de erratas y discrepancias deberían ser corregidas para facilitar la reutilización de los conjuntos de datos, o su uso combinado con otras fuentes de información, como es en este caso el uso de datos de la Junta de Castilla y León combinados con datos de la Agencia Estatal de Meteorología.

Consideramos que el objetivo principal de la publicación de datos abiertos es la posibilidad de desarrollar las herramientas necesarias para que lleguen al público general, y creemos que esta integración en un bot en una plataforma tan utilizada como Telegram es una contribución importante en esta dirección de transparencia. Además, para fomentar el desarrollo futuro, todo el código está disponible en [https://github.com/rammmiro/eltiempoBot/](https://github.com/rammmiro/eltiempoBot/) bajo una licencia [GNU General Public License v3.0](https://github.com/rammmiro/eltiempoBot/blob/master/LICENSE).
