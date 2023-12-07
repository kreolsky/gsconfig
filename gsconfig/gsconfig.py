import os
import gspread
import json
import re
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property

from . import tools
from . import gsparser


class GSConfigError(Exception):
    def __init__(self, text='', value=-1):
        self.text = text
        self.value = value

    def __str__(self):
        return f'{self.text} Err no. {self.value}'


class Template(object):
    """
    Класс шаблона из которого будет генериться конфиг.
    Паттерн ключа и символ отделяющий команду можно переопределить.

    path -- путь для файла шаблона    
    body -- можно задать шаблон как строку
    pattern -- паттерн определения ключа в шаблоне. r'\{([a-z0-9_!]+)\}' - по умолчанию
    command_letter -- символ отделяющий команду от ключа. '!' - по умолчанию

    Пример ключа в шаблоне: {cargo_9!float}. Где, 
    'cargo_9' -- ключ для замены (допустимые символы a-z0-9_)
    'float' -- указывает что оно всегда должно быть типа float

    ВАЖНО! 
    1. command_letter всегда должен быть включен в pattern
    2. ключ + команда всегда должены быть в первой группе регулярного выражения

    Дополнительные команды парсера:
    dummy -- Пустышка, ничего не длает.

    float -- Переводит в начения с плавающей запятой.
    Пример: Получено число 10, в шаблон оно будет записано как 10.0

    int -- Переводит в целые значения отбрасыванием дробной части
    Пример: Получено число 10.9, в шаблон оно будет записано как 10

    extract -- Вытаскивает элемент из списка (list or tuple) если это список единичной длины.
    Пример: По умолчанию парсер не разворачивает словари и они приходят вида [{'a': 1, 'b': 2}],
    если обязательно нужен словарь, то extract развернёт полученный список до {'a': 1, 'b': 2}

    wrap -- Дополнительно заворачивает полученый список если первый элемент этого списка не является списком.
    Пример: Получен список [1, 2, 4], 1 - первый элемент, не список, тогда он дополнительно будет завернут [[1, 2, 4]].

    string -- Дополнительно заворачивает строку в кавычки. Все прочие типы данных оставляет как есть. 
    Используется когда заранее неизвестно будет ли там значение и выбор между null и строкой.
    Например, в новостях мультиивентов поле "sns": {news_sns!string}.
    Пример: Получена строка 'one,two,three', тогда она будет завернута в кавычки и станет '"one,two,three"'.


    """
    def __init__(self, path='', body='', pattern=None, command_letter=None):
        self.path = path
        self.pattern = pattern or r'\{([a-z0-9_!]+)\}'
        self.command_letter = command_letter or '!'
        self.command_handlers = {
            'dummy': lambda x: x,
            'float': lambda x: float(x),
            'int': lambda x: int(x),
            'string': tools.command_string,
            'extract': tools.command_extract,
            'wrap': tools.command_wrap
        }
        self._body = body
        self._keys = []

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

        if self._body:
            return self._body

        if not self.path:
            raise ValueError("Specify the path to the template file.")

        try:
            with open(self.path, 'r') as file:
                self._body = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file '{self.path}' not found.")
        
        return self._body

    @property
    def keys(self) -> list:
        """
        Возвращает все ключи используемые в шаблоне.
        """

        if not self._keys:
            self._keys = re.findall(self.pattern, self.body)
        return self._keys

    def __str__(self):
        return self.title

    def _calculate_name_and_extension(self) -> dict:
        r = self.title.split('.')
        return {'name': r[0], 'extension': r[-1]}
    
    def set_path(self, path=''):
        if not path:
            raise ValueError("Specify the path for template definition.")
        
        try:
            with open(path, 'r') as file:
                self._body = file.read()
            self.path = path
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file '{path}' not found.")

    def set_body(self, body=''):
        if not body:
            raise ValueError("Specify the body for template definition.")
        
        self._body = body

    def make(self, balance:dict, strip:bool=True) -> str:
        """
        Заполняет шаблон данными.
        ВАЖНО! Для сохранения в JSON необходимо заполнять все поля шаблона!
        
        balance -- словарь (dict) с балансом (данными для подстановки), где:
            key - переменная, которую необходимо заменить
            value - значение для замены

        strip -- Будет ли отрезать от строк лишние кавычки. 
            True (по умолчанию) - Отрезает кавычки от строк. 
            В шаблоне НЕОБХОДИМО проставлять кавычки для всех строковых данных.
            Либо явно указывать трансформацию в строку при помощи команды !string

            False - Строки будут автоматически завернуты в кавычки. 
            Невозможно использовать переменные в подстроках.
        """

        def replace_keys(match):
            key_command_pair = match.group(1).split(self.command_letter)

            # Ключ, который будет искаться для замены 
            key = key_command_pair[0]

            # Обработка ошибки отсутствия ключа
            if key not in balance:
                raise KeyError(f"Key '{key}' not found in balance.")
            
            insert_balance = balance[key]

            # Команда ВСЕГДА идет после command_letter!
            if self.command_letter in match.group(1):
                command = key_command_pair[-1]

                # Обработка ошибки отсутствия команды
                if command not in self.command_handlers:
                    raise ValueError(f"Command '{command}' is not supported by Template class")
                insert_balance = self.command_handlers[command](insert_balance)

            # Возвращаем строки как есть
            if strip and isinstance(insert_balance, str):
                return insert_balance

            return json.dumps(insert_balance)

        return re.sub(self.pattern, replace_keys, self.body)


class Page(object):
    """
    Wrapper class for gspread.Worksheet
    """

    def __init__(self, worksheet):
        self.worksheet = worksheet  # Source gspread.Worksheet object
        self.key_skip_letters = set()
        self.parser_version = None
        self._cache = None
        self._name_and_format = None
        self.parsers = {
            'raw': tools.parser_dummy,
            'csv': tools.parser_dummy,
            'json': tools.parser_json
        }

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
    
    def __iter__(self):
        yield from self.get()

    def set_key_skip_letters(self, key_skip_letters):
        """
        Comment symbol for keys on config pages.
        Keys starting with these symbols are not exported.
        """

        if not isinstance(key_skip_letters, (list, set)):
            raise TypeError('key_skip_letters must be a list or a set!')
        self.key_skip_letters = set(key_skip_letters)

    def set_parser_version(self, parser_version):
        """
        Указать версию парсера
        """
        
        # Взять версии парсера из обьекта парсера
        available_versions = gsparser.ConfigJSONConverter.AVAILABLE_PARSER_VESRION
        if parser_version not in available_versions:
            raise ValueError(f'The version is not available. Available versions are: {available_versions}')

        self.parser_version = parser_version

    def get(self, format=None, mode=None, scheme=None, **params):
        """
        Возвращает данные в формате страницы. См. описание format ниже
        В случае, когда формат не указан возвращает сырые данные как двумерный массив.

        Понимает несколько схем компановки данных. Проверка по очереди:
        1. Указана схема данных (заголовки столбца ключей и данных). См. описание scheme ниже
        2. ДВЕ колонки. В первой строке есть ОБА ключа 'key' и 'value'
        3. Свободный формат, первая строка - ключи, все последуюшие - данные

        Схема в две колонки упрощенная версия формата со схемой. Результатом будет словарь 
        с парами ключ = значение. В случае указания схемы, данные будут дополнительно 
        завернуты в словари с названием столбца данных.
        
        format -- data storage format
            json - collects into a dictionary and parses values
            csv - returns data as a two-dimensional array. Always WITHOUT parsing!
            raw - returns data as a two-dimensional array. Always WITHOUT parsing!
        
        mode -- whether to parse data or not
            raw - data will always be returned WITHOUT parsing

        scheme -- схема хранения данных в несколько колонок на странице.
            Словарь вида (Названия ключей словаря фиксированы!):
            scheme = {
                'key': 'key'  # Название столбца с данными
                'data': [value_1, value_2]  # Список столбцов данных
            }

        Параметры только для формата в ДВЕ колонки. 
        Можно задать кастомные значения названия полей ключей и данных
            key - заголовок столбца ключей
            value - заголовок столбца данных

        **params - все параметры доступные для парсера parser.jsonify
        """

        if not self._cache:
            self._cache = self.worksheet.get_all_values()

        params['is_raw'] = mode == 'raw'
        params['key_skip_letters'] = self.key_skip_letters
        params['parser_version'] = self.parser_version
        params['scheme'] = scheme
        
        format = format or self.format

        return self.parsers[format](self._cache, **params)


class Document(object):
    """
    Wrapper class for gspread.Spreadsheet
    """

    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet  # Source gspread.Spreadsheet object
        self.page_skip_letters = set()
        self.key_skip_letters = set()
        self.parser_version = None

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
        page.set_parser_version(self.parser_version)
        return page

    @property
    def title(self):
        return self.spreadsheet.title

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
    
    def set_parser_version(self, parser_version):
        """
        Указать версию парсера
        """
        
        # Взять версии парсера из обьекта парсера
        available_versions = gsparser.ConfigJSONConverter.AVAILABLE_PARSER_VESRION
        if parser_version not in available_versions:
            raise ValueError(f'The version is not available. Available versions are: {available_versions}')

        self.parser_version = parser_version

    def save(self, path='', mode=''):
        """
        If mode = 'full' is specified, it tries to save all pages of the document.
        IMPORTANT! Working pages are usually not prepared for saving and will fail.
        """

        pages = self.pages() if mode == 'full' else self
        for page in pages:
            tools.save_page(page, path)


class GameConfigLite(Document):
    """
    Game configuration consisting of only one Google Sheet.
    """

    def __init__(self, spreadsheet_id, client=None):
        self.client = client or gspread.oauth()  # GoogleOauth object
        self.spreadsheet_id = spreadsheet_id  # Google Sheet ID
        self.page_skip_letters = {'#', '.'}
        self.key_skip_letters = {'#', '.'}
        self.parser_version = 'v1'  # Available only 'v1' and 'v2' mode. See gsparser for details

    @cached_property
    def spreadsheet(self):
        """
        Returns a gspread.Spreadsheet object
        """

        return self.client.open_by_key(self.spreadsheet_id)


class GameConfig(object):
    """
    Обьект содержащий все конфиги указанные в настройках.
    Принимает настройки в виде словаря.

    settings -- словарь настроек вида {document_title: document_id, ...}
        document_title -- название
        document_id -- id таблицы

        ВАЖНО! Для получения из конфига документа по названию используется имя таблицы! 
        document_title исключительно как подсказка для визуального представления конфига.
        Рекомендую забирать настройки из таблицы где поддерживается консистентность.

    client -- Клиент авторизации
    """

    def __init__(self, settings={}, client=None):
        self.client = client or gspread.oauth()
        self.settings = settings

        self.page_skip_letters = {'#', '.'}
        self.key_skip_letters = {'#', '.'}
        self.parser_version = 'v1'  # Available only 'v1' and 'v2' mode. See gsparser for details

        self._cache = {}
        self._max_workers = 5

    @property
    def documents(self) -> list:
        if not self._cache:
            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                self._cache = list(pool.map(self._create_document, self.settings.values()))

        return self._cache
    
    def __iter__(self):
        for document in self.documents:
            yield(document)
    
    def __getitem__(self, title):
        result = next(filter(lambda x: x.title == title, self.documents), None)
        if result is None:
            raise KeyError(f'No document found with title "{title}"')
        
        return result

    def _create_document(self, document_id):
        document = Document(self.client.open_by_key(document_id))
        document.set_page_skip_letters(self.page_skip_letters)
        document.set_key_skip_letters(self.key_skip_letters)
        document.set_parser_version(self.parser_version)

        return document