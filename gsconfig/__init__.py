from .gsconfig import GoogleOauth
from .template import Template
from .gsconfig import GameConfigLite
from .gsconfig import GameConfig
from .gsparser import ConfigJSONConverter
from .extractor import Extractor
from .json_handler import JSONHandler as json
from . import tools

"""
gsconfig
~~~~~~~

Game Config Tools over gspread (Google Spreadsheets library).

Template -- класс шаблона из которого собирается конфиг
Extractor -- класс извлечения данных страницы с учётом их формата
GameConfigLite -- класс конфига состоящего из одной гуглодоки
GameConfig -- класс конфига из нескольких документов
ConfigJSONConverter -- класс конвертора из промежуточного формата в JSON
JSONHandler -- класс для работы с JSON. Чуть более аккуратно сохраняет данные, вытягивая в одну строку списки из чисел и строк специфичные для игровых конфигов

"""

__version__ = '0.14.0'
__author__ = 'Serge Zaigraeff'
