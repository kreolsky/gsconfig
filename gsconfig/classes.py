import os
import gspread
import json
import re
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property

from . import tools


parsers = {
    'raw': tools.parser_dummy,
    'csv': tools.parser_dummy,
    'json': tools.parser_json
}


class GSConfigError(Exception):
    def __init__(self, text='', value=-1):
        self.text = text
        self.value = value

    def __str__(self):
        return f'{self.text} Err no. {self.value}'


class Template(object):
    """
    Класс шаблона из которого будет генериться конфиг.
    Ключи в тексте выделяются '{}' (фигурные скобки), внутри допустимы [a-z0-9_!]+
    Паттерн ключа можно переопределить, главно не сломать json формат.

    ВАЖНО! Паттерн содержит '!' для разделения ключа и команды
    """
    def __init__(self, path, pattern=None):
        self.path = path
        self.pattern = pattern or r'\{([a-z0-9_!]+)\}'
        self.cache = None

    @property
    def title(self) -> str:
        return os.path.basename(self.path)

    @property
    def name(self) -> str:
        return self._calculate_name_and_extension()['name']
    
    @property
    def body(self) -> str:
        """
        Возвращает тело шаблона как строку.
        """
        
        with open(self.path, 'r') as file:
            return file.read()

    @property
    def keys(self) -> list:
        """
        Возвращает все ключи используемые в шаблоне.
        """

        return re.findall(self.pattern, self.body)

    def _calculate_name_and_extension(self) -> dict:
        r = self.title.split('.')
        return {'name': r[0], 'extension': r[-1]}
    
    def make(self, data) -> str:
        """
        Заполняет шаблон данными.
        ВАЖНО! Для сохранения в JSON необходимо заполнять все поля шаблона!
        """

        def replace_keys(match):
            group = match.group(1).split('!')
            # Ключ, то что будет искаться для замены
            key = group[0]

            # Команда всегда после '!' нужен дополнительный обрабочик
            # TODO: Прикрутить обработчик команд (взять решение из gsparser)
            command = group[-1]

            # Если ключ не найден, падать с ошибкой!
            # TODO: Вставить обработчик варнингов
            return str(data[key])  # str(data.get(key, f'"{{{key}}}"'))

        return re.sub(self.pattern, replace_keys, self.body)


class Page(object):
    """
    Wrapper class for gspread.Worksheet
    """

    def __init__(self, worksheet, parsers=parsers):
        self.worksheet = worksheet  # Source gspread.Worksheet object
        self.parsers = parsers or {}
        self.key_skip_letters = set()
        self.cache = None
        self.parser_mode = None
        self._name_and_format = None

    @property
    def title(self):
        """
        Page title as is, the page name in the table.
        """
        return self.worksheet.title

    @property
    def name(self):
        """
        Page name.
        The title suffix determining the data format is removed,
        if a parser is specified for it.
        """
        if not self._name_and_format:
            self._calculate_name_and_format()
        return self._name_and_format["name"]

    @property
    def format(self):
        """
        Determines the data format based on the page title.
        If nothing is specified, it is determined as raw.
        """
        if not self._name_and_format:
            self._calculate_name_and_format()
        return self._name_and_format["format"]

    def _calculate_name_and_format(self):
        name = self.title
        format = 'raw'
        for parser_key in self.parsers.keys():
            if name.endswith(f'.{parser_key}'):
                name = name[:-len(parser_key) - 1]
                format = parser_key
                break
        self._name_and_format = {"name": name, "format": format}

    def __repr__(self):
        return json.dumps(self.get(), ensure_ascii=False)

    def set_key_skip_letters(self, key_skip_letters):
        """
        Comment symbol for keys on config pages.
        Keys starting with these symbols are not exported.
        """
        if not isinstance(key_skip_letters, (list, set)):
            raise TypeError('key_skip_letters must be a list or a set!')
        self.key_skip_letters = set(key_skip_letters)

    def get(self, format=None, mode=None, **params):
        """
        Retrieves data from the page in a format appropriate for its type.
        If the format is not specified separately and not set by the user, it tries to get it as raw
        format - data storage format
            json - collects into a dictionary and parses values
            csv - returns data as a two-dimensional array. Always WITHOUT parsing!
            raw - returns data as a two-dimensional array. Always WITHOUT parsing!
        mode - whether to parse data or not
            raw - data will always be returned WITHOUT parsing
        """

        if not self.cache:
            self.cache = self.worksheet.get_all_values()

        params['is_raw'] = mode == 'raw'
        params['key_skip_letters'] = self.key_skip_letters
        params['mode'] = self.parser_mode
        format = format or self.format

        return self.parsers[format](self.cache, **params)


class Document(object):
    """
    Wrapper class for gspread.Spreadsheet
    """

    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet  # Source gspread.Spreadsheet object
        self.page_skip_letters = set()
        self.key_skip_letters = set()
        self.parser_mode = None

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.spreadsheet.title}' id:{self.spreadsheet.id}>"

    def __getitem__(self, title):
        return self._create_page(self.spreadsheet.worksheet(title))

    def __iter__(self):
        """
        This method returns only the main config pages.
        Those that do NOT start with symbols in page_skip_letters.
        """
    
        for page in self.spreadsheet.worksheets():
            if any([page.title.startswith(x) for x in self.page_skip_letters]):
                continue            
            yield self._create_page(page)

    def _create_page(self, worksheet):
        page = Page(worksheet)
        page.set_key_skip_letters(self.key_skip_letters)
        page.parser_mode = self.parser_mode
        return page

    @property
    def page1(self):
        """
        Returns the first main page among those
        that do NOT start with symbols in page_skip_letters.
        """

        for page in self.pages():
            return page

    @property
    def pages(self):
        """
        This method returns all config pages.
        """

        for page in self.spreadsheet.worksheets():
            yield self._create_page(page)

    def set_page_skip_letters(self, page_skip_letters):
        """
        Comment symbol for config pages.
        Pages starting with these symbols are not exported.
        """

        if not isinstance(page_skip_letters, (list, set)):
            raise TypeError('page_skip_letters must be a list or a set!')
        self.page_skip_letters = set(page_skip_letters)

    def set_key_skip_letters(self, key_skip_letters):
        """
        Comment symbol for keys on config pages.
        Keys starting with these symbols are not exported.
        """

        if not isinstance(key_skip_letters, (list, set)):
            raise TypeError('key_skip_letters must be a list or a set!')
        self.key_skip_letters = set(key_skip_letters)


class GameConfigLite(Document):
    """
    Game configuration consisting of only one Google Sheet.
    """

    def __init__(self, spreadsheet_id, client=None):
        self.client = client or gspread.oauth()  # GoogleOauth object
        self.spreadsheet_id = spreadsheet_id  # Google Sheet ID
        self.page_skip_letters = {'#', '.'}
        self.key_skip_letters = {'#', '.'}
        self.parser_mode = 'v1'

    @cached_property
    def spreadsheet(self):
        """
        Returns a gspread.Spreadsheet object
        """

        return self.client.open_by_key(self.spreadsheet_id)

    def save(self, path='', mode=''):
        """
        If mode = 'full' is specified, it tries to save all pages of the document.
        IMPORTANT! Working pages are usually not prepared for saving and will fail.
        """

        pages = self if mode == 'full' else self.pages()
        for page in pages:
            tools.save_page(page, path)


class GameConfig(object):
    """
    Обьект содержащий все конфиги указанные в настройках.
    Принимает настройки как из гуглотаблицы так и в виде словаря. Если указано и то и то,
    то будет использован словарь.

    settings -- словарь настроек.
    Либо id документа и название вкладки со списком всех документов конфига
        spreadsheet_id -- id таблицы со списко конфигов
        page_title -- заголовок страницы в таблице со списком документов конфига

    Либо словарь вида {document_title: spreadsheet_id, ...}
        document_title -- название
        spreadsheet_id -- id документа

    backup -- словарь со списком документов конфига и настройками конфига.
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
            self._settings_page_title = settings['page_title']

        elif settings:
            self._settings = {
                key : self.client.open_by_key(value)
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
            settings_obj = self.client.open_by_key(self._settings_gspread_id).pull()
            settings = settings_obj[self._settings_page_title].get_as_json()

            self._settings = {
                key : self.client.open_by_key(value)
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
