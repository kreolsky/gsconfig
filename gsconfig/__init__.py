from .gsconfig import Template
from .gsconfig import GameConfigLite
from .gsconfig import GameConfig
from .gsparser import ConfigJSONConverter
from . import tools

"""
gsconfig
~~~~~~~

Game Config Tools over gspread (Google Spreadsheets library).

Template -- класс шаблона из которого собирается конфиг
GameConfigLite -- класс конфига состоящего из одной гуглодоки
ConfigJSONConverter -- класс конфертора из промежуточного формата гуглодоки в JSON

"""


__version__ = '0.3.0'
__author__ = 'Serge Zaigraeff'
