from .gsconfig import GoogleOauth
from .template import Template
from .gsconfig import GameConfigLite
from .gsconfig import GameConfig
from .gsparser import ConfigJSONConverter
from .extractor import Extractor
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

"""

__version__ = '0.7.4'
__author__ = 'Serge Zaigraeff'
