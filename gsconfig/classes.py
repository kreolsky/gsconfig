import gspread
import os
import json
import re
from datetime import datetime

from oauth2client.service_account import ServiceAccountCredentials
from concurrent.futures import ThreadPoolExecutor

from .parser import config_to_json
from . import tools


class GSConfigError(Exception):
    def __init__(self, text='', value=-1):
        self.text = text
        self.value = value

    def __str__(self):
        return f'{self.text} Err no. {self.value}'


class GoogleOauth():
    def __init__(self, oauth2_token_file_path):
        self._key_file_path = oauth2_token_file_path
        self._google_auth = None

    @property
    def connect(self):
        if not self._google_auth:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
                ]
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self._key_file_path, scope)
            self._google_auth = gspread.authorize(credentials)

        return self._google_auth


class Page(object):
    """
    Класс обёртка поверх gspread.Worksheet
    """

    def __init__(self, worksheet):
        self.worksheet = worksheet # исходный обьект gspread.Worksheet
        self._data_parser = {
            'json': self.get_as_json,
            'csv': self.get_as_csv,
            'raw': self.get_as_raw}
        # Ключи маркированные этими символами не экспортируются.
        self.key_skip_letters = []

    @property
    def title(self):
        return self.worksheet.title

    @property
    def type(self):
        title_type_list = self.title.split('.')
        if len(title_type_list) > 1:
            return title_type_list[-1]

        return 'json'

    def __repr__(self):
        return json.dumps(self.get())

    def set_key_skip_letters(self, key_skip_letters):
        """
        Символ комментария для ключей на страницах конфига.
        Ключи начинающиеся с этих символов не экспортируются.
        """

        if not isinstance(key_skip_letters, list):
            raise GSConfigError(f'It has to be a list!')
        self.key_skip_letters = key_skip_letters

    def get(self, page_type=None, raw_data=False):
        """
        Достаёт данные со страницы данные в формете адекватном их типу.
        Если тип не указан отдельно и не задан пользователем пытается достать как json.
        """

        page_type = page_type or self.type
        return self._data_parser[page_type]()

    def get_as_json(self, key='key', value='value', **params):
        """
        Парсит данные со страницы гуглодоки в формат JSON.
        См. parser.config_to_json

        key - заголовок столбца с ключами
        value - заголовок столбца с данными
        **params - все параметры доступные функции parser.config_to_json парсера
        """

        page_data = self.worksheet.get_all_values()

        headers = page_data[0]
        data = page_data[1:]

        # Если документ из двух колонок. Ключами в столбце key и значением в столбце value
        if key in headers and value in headers:
            key_index = headers.index(key)
            value_index = headers.index(value)

            out = {
                line[key_index]: config_to_json(line[value_index], **params)
                for line in data if len(line[0]) > 0
            }

            return out

        # Первая строка с заголовками, остальные строки с данными
        out = []
        for values in data:
            bufer = {
                key: config_to_json(value, **params)
                for key, value in zip(headers, values)
                if not any([key.startswith(x) for x in self.key_skip_letters]) and len(key) > 0
            }
            out.append(bufer)

        if len(out) == 1:
            out = out[0]

        return out

    def get_as_raw(self, **params):
        return self.get_as_json(is_raw=True, **params)

    def get_as_csv(self):
        return self.worksheet.get_all_values()


class Document(object):
    """
    Класс обертка поверх gspread.Spreadsheet.
    """

    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet # Исходный обьект gspread.Spreadsheet
        self.page_skip_letters = []
        self.key_skip_letters = []

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.spreadsheet.title}' id:{self.spreadsheet_id}>"

    def __getitem__(self, title):
        page = Page(self.spreadsheet.worksheet(title))
        page.set_key_skip_letters(self.key_skip_letters)
        return page

    def __iter__(self):
        for page in self.spreadsheet.worksheets():
            page = Page(page)
            page.set_key_skip_letters(self.key_skip_letters)
            yield page

    def set_page_skip_letters(self, page_skip_letters):
        """
        Символ комментария для страниц конфига.
        Страницы начинающиеся с этих символов не экспортируются.
        """

        if not isinstance(page_skip_letters, list):
            raise GSConfigError(f'It has to be a list!')
        self.page_skip_letters = page_skip_letters

    def set_key_skip_letters(self, key_skip_letters):
        """
        Символ комментария для ключей на страницах конфига.
        Ключи начинающиеся с этих символов не экспортируются.
        """

        if not isinstance(key_skip_letters, list):
            raise GSConfigError(f'It has to be a list!')
        self.key_skip_letters = key_skip_letters

    def pages(self):
        """
        Метод возвращает только основные страницы конфига.
        Те, которые НЕ начинаются с символов в page_skip_letters.
        """

        for page in self:
            if any([page.title.startswith(x) for x in self.page_skip_letters]):
                continue
            yield page


class GameConfigLite(Document):
    """
    Игровой конфиг состоящий только из одной гуглотаблички.
    """
    def __init__(self, client, spreadsheet_id):
        self.client = client  # Обьект авторизации в гугле GoogleOauth
        self.spreadsheet_id = spreadsheet_id  # ID гуглотаблицы
        self._spreadsheet = None
        self.page_skip_letters = ['#', '.']
        self.key_skip_letters = ['#', '.']

    @property
    def spreadsheet(self):
        """
        Возвращает обьект gspread.Spreadsheet
        """

        if not self._spreadsheet:
            self._spreadsheet = self.client.connect.open_by_key(self.spreadsheet_id)

        return self._spreadsheet

    def save(self, path='', mode=''):
        """
        Если указано mode = 'full', то пытается сохранить все страницы.
        ВАЖНО! Обычная страница обычно не подготовлена к сохранению и будет падать.
        """
        pages = self if mode == 'full' else self.pages()
        for page in pages:
            tools.save_page(page, path)


class GameConfig(object):
    """
    Обьект содержащий все конфиги указанные в настройках.
    Принимает настройки как из гуглотаблицы так и в виде словаря. Если указано и то и то,
    то будет использован словарь.

    settings -- словарь с настройками.
    Либо id документа и название вкладки со списком всех документов конфига
        spreadsheet_id -- id таблицы со списко конфигов
        page_title -- заголовок страницы в таблице со списком документов конфига

    Либо словарь вида {document_title: spreadsheet_id, ...}
        document_title -- название
        spreadsheet_id -- id документа

    backup -- словарь с со списком документов конфига и настройками конфига.
    Необходимо для восстановления обьекта конфига ииз бекапа.
    """

    def __init__(self, client, settings={}, backup=None):
        self.client = client
        self._settings = None
        self._settings_gspread_id = None
        self._documents = None
        self._documents_to_export = None

        if backup:
            self._documents = [Document(x) for x in backup['documents']]
            self._settings = backup['settings']

        elif 'spreadsheet_id' in settings:
            self._settings_gspread_id = settings['spreadsheet_id']
            self._settingspage_name= settings['page_title']

        elif settings:
            self._settings = {
                key : GSpreadsheet(self.client, value)
                for key, value in settings.items()
            }

    def __repr__(self):
        return f'{self.__class__.__name__}: ' + ', '.join([x.title for x in self.documents])

    def __iter__(self) -> Document:
        for document in self.documents:
            yield(document)

    def __getitem__(self, title):
        return self.document(title)

    @property
    def documents(self) -> list:
        if not self._documents:
            self.pull()

        return self._documents

    @property
    def documents_to_export(self):
        if not self._documents_to_export:
            self._documents_to_export = self.settings.values()

        return self._documents_to_export

    @property
    def settings(self):
        if not self._settings:
            settings_obj = GSpreadsheet(self.client, self._settings_gspread_id).pull()
            settings = settings_obj[self._settingspage_name].get_as_json()

            self._settings = {
                key : GSpreadsheet(self.client, value)
                for key, value in settings.items()
            }

        return self._settings

    def document(self, title):
        return next(filter(lambda x: x.title == title, self.documents))

    def set_documents_to_export(self, documents_list):
        if not all([x in self.settings for x in documents_list]):
            raise GSConfigError(f'Incorrect documents! Available documents is {list(self.settings.keys())}')

        self._documents_to_export = [self.settings[x] for x in documents_list]

    def _get_document(self, gspread_obj):
        return gspread_obj.pull()

    def pull(self, max_workers=5):
        if not self._documents:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                self._documents = list(pool.map(self._get_document, [x for x in self.documents_to_export]))

        return self._documents
