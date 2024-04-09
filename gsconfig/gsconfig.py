import os
import gspread
import json
import re
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property

from . import tools
from . import gsparser


"""
Data extractors for Page class
"""

def extractor_dummy(page_data, **params):
    return page_data

def extractor_json(page_data, **params):
    """
    Парсит данные из гуглодоки в формат JSON. См. parser.jsonify
    
    Когда формат не указан - возвращает сырые данные как двумерный массив.

    Понимает несколько схем компановки данных. Проверка по очереди:
    1. Используется схема данных. См. Page.schema и Page.set_schema()
    2. Свободный формат, первая строка - ключи, все последуюшие - данные соответствующие этим ключам

    **params - все параметры доступные для парсера parser.jsonify
    """

    schema = params.get('schema')
    key_skip_letters = params.get('key_skip_letters', [])

    headers = page_data[0]  # Заголовки
    data = page_data[1:]  # Данные

    # Парсер конфигов из гуглодоки в JSON
    parser = gsparser.ConfigJSONConverter(params)

    # Указана обычная схема (schema) хранения данных. Данные в несоклько колонок 
    # schema = {'key': 'key', 'data': ('value_1', 'value_2')}, где 
    # 'key' - название столбца с ключами 
    # 'data' - контеж названий столбцов с данными
    if isinstance(schema, dict):
        key_index = headers.index(schema['key'])
        data_indexes = [headers.index(x) for x in schema['data']]
        
        # Первый столбец проходит как дефолтный, из него буду взяты данные 
        # когда в соответствующих строках других столбцов будет пусто
        default_data_index = data_indexes[0]

        out = {}
        for data_index in data_indexes:
            bufer = {}
            for line in data:
                # Пропуск пустых строк
                if not line[key_index]:
                    continue
                
                line_data = line[data_index]
                # Если данные пустые, то брать из дефолтного столбца
                if not line_data:
                    line_data = line[default_data_index]
                
                bufer[line[key_index]] = parser.jsonify(line_data)

            out[headers[data_index]] = bufer

        return out

    # Простая схема данных. Документ из двух колонок schema = ('key', 'data'), где 
    # 'key' - название столбца с ключами 
    # 'data' - название столбца с данными 
    # Схема -- кортеж и все элементы схемы представлены в заголовке
    if isinstance(schema, tuple) and all(x in headers for x in schema):
        key_index = headers.index(schema[0])
        data_index = headers.index(schema[-1])

        out = {}
        for line in data:
            # Пропуск пустых строк
            if not line[key_index]:
                continue

            out[line[key_index]] = parser.jsonify(line[data_index])

        return out

    # Обычный документ, данные расположены строками
    # Первая строка с заголовками, остальные строки с данными
    out = []
    for values in data:
        bufer = [
            f'{key} = {{{str(value)}}}' for key, value in zip(headers, values)
            if not any([key.startswith(x) for x in key_skip_letters]) and len(key) > 0
        ]
        bufer = parser.jsonify(', '.join(bufer))
        out.append(bufer)

    # Оставлено для совместимость с первой версией
    # Если в результате только один словарь, он не заворачивается
    if len(out) == 1:
        return out[0]

    return out


"""
Template command handlers
"""

def command_extract(array):
    """
    extract -- Вытаскивает элемент из списка (list or tuple) если это список единичной длины.

    Пример: По умолчанию парсер не разворачивает словари и они приходят вида [{'a': 1, 'b': 2}],
    если обязательно нужен словарь, то extract развернёт полученный список до {'a': 1, 'b': 2}
    """
    if len(array) == 1 and type(array) in (list, tuple):
        return array[0]
    return array

def command_wrap(array):
    """
    wrap -- Дополнительно заворачивает полученый список если первый элемент этого списка не является списком.

    Пример: Получен список [1, 2, 4], 1 - первый элемент, не список, тогда он дополнительно будет завернут [[1, 2, 4]].
    Акутально для паралакса, когда остается только один слой.
    Параллакс состоит из нескольких слоев и данные каждого слоя должны быть списком, когда остается только один слой,
    то он разворачивается и на выходе получается список из значений одного слоя, что ломает клиент.
    В списке должен быть один элемент - параметры параллакса.
    """
    if type(array[0]) not in (list, dict):
        return [array]
    return array

def command_string(arg):
    """
    string -- Дополнительно заворачивает строку в кавычки. Все прочие типы данных оставляет как есть. Используется
    когда заранее неизвестно будет ли там значение и выбор между null и строкой.
    Например, в новостях мультиивентов поле "sns": {news_sns!string}.

    Пример: Получена строка 'one,two,three', тогда она будет завернута в кавычки и станет '"one,two,three"'.
    """

    if type(arg) is str:
        return f'"{arg}"'
    return arg

"""
Classes
"""

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

    - path -- путь для файла шаблона  
    - body -- можно задать шаблон как строку
    - pattern -- паттерн определения ключа в шаблоне. r'\{([a-z0-9_!]+)\}' - по умолчанию
    - command_letter -- символ отделяющий команду от ключа. '!' - по умолчанию
    - jsonify  -- Отдавать результат как словарь. False - по умолчанию (отдает как строку)
    - strip -- Будет ли отрезать от строк лишние кавычки. 
        True (по умолчанию) -- Отрезает кавычки от строк. 
        В шаблоне НЕОБХОДИМО проставлять кавычки для всех строковых данных.
        Либо явно указывать трансформацию в строку при помощи команды !string
        False -- Строки будут автоматически завернуты в кавычки. 
        Невозможно использовать переменные в подстроках.

    Пример ключа в шаблоне: {cargo_9!float}. Где, 
    - 'cargo_9' -- ключ для замены (допустимые символы a-z0-9_)
    - 'float' -- дополнительная команда указывает что оно всегда должно быть типа float

    ВАЖНО! 
    1. command_letter всегда должен быть включен в pattern
    2. ключ + команда в pattern всегда должены быть в первой группе регулярного выражения

    Дополнительные команды доступные в ключах шаблона:
    dummy -- Пустышка, ничего не длает.

    float -- Переводит в начения с плавающей запятой.
    Пример: Получено число 10, в шаблон оно будет записано как 10.0

    int -- Переводит в целые значения отбрасыванием дробной части
    Пример: Получено число 10.9, в шаблон оно будет записано как 10

    json -- Сохраняет структура как JSON (применяет json.dumps())

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

    def __init__(self, path='', body='', pattern=None, command_letter=None, strip=True, jsonify=False):
        self.path = path
        self.pattern = pattern or r'\{([a-z0-9_!]+)\}'
        self.command_letter = command_letter or '!'
        self.strip = strip
        self.jsonify = jsonify
        self.command_handlers = {
            'dummy': lambda x: x,
            'float': lambda x: float(x),
            'int': lambda x: int(x),
            'json': lambda x: json.dumps(x),
            'string': command_string,
            'extract': command_extract,
            'wrap': command_wrap
        }
        self._body = body
        self._keys = []

    @property
    def title(self) -> str:
        return os.path.basename(self.path)

    @property
    def name(self) -> str:
        return self.name_and_extension[0]
    
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

    @property
    def name_and_extension(self) -> dict:
        return self.title.rsplit('.', 1)

    def __str__(self):
        return self.title
    
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

    def make(self, balance:dict):
        """
        Заполняет шаблон данными.
        ВАЖНО! Для сохранения в JSON необходимо заполнять все поля шаблона!
        
        balance -- словарь (dict) с балансом (данными для подстановки), где:
            key - переменная, которую необходимо заменить
            value - значение для замены

        Свойства класса влияющие на сборку конфига из шаблона:
        
        strip -- Будет ли отрезать от строк лишние кавычки. 
            True (по умолчанию) - Отрезает кавычки от строк. 
            В шаблоне НЕОБХОДИМО проставлять кавычки для всех строковых данных.
            Либо явно указывать трансформацию в строку при помощи команды !string

            False - Строки будут автоматически завернуты в кавычки. 
            Невозможно использовать переменные в подстроках.
        
        jsonify -- Забрать как словарь. False - по умолчанию, забирает как строку.
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
            if self.strip and isinstance(insert_balance, str):
                return insert_balance

            return json.dumps(insert_balance)

        out = re.sub(self.pattern, replace_keys, self.body)
        
        # Преобразовать в JSON
        if self.jsonify:
            try:
                out = json.loads(out)
            except json.JSONDecodeError as e:
                raise ValueError(f"\nError during jsonify in {self.title}\n{str(e)}\n{out}")

        return out


class Page(object):
    """
    Wrapper class for gspread.Worksheet
    """

    def __init__(self, worksheet):
        self.worksheet = worksheet  # Source gspread.Worksheet object
        self.key_skip_letters = set()
        self.parser_version = None
        self.schema = ('key', 'data')  # Схема хранение данных в двух столбцах
        self.is_raw = False  # По умолчанию всегда будет парсить данные при сохранении в json 
        self._format = None
        self._cache = None
        self._name_and_format = None
        self._extractors = {
            'raw': extractor_dummy,
            'csv': extractor_dummy,
            'json': extractor_json
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
        Формат определяется расширением указанным в названии страницы. 
        'raw' - если ничего не указано.

        Доступные формата:
        - json - Возвращает словарь. ПАРСИТ данные
        - csv - Воззвращает двумерный массив. НЕ парсит данные!
        - raw - Воззвращает двумерный массив. НЕ парсит данные!
        """

        if self._format:
            return self._format

        if not self._name_and_format:
            self._calculate_name_and_format()

        return self._name_and_format["format"]

    def _calculate_name_and_format(self):
        name = self.title
        format = 'raw'
        for parser_key in self._extractors.keys():
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
        Указать версию парсера (конвертора из формата конфигов в JSON)
        """
        
        # Взять версии парсера из обьекта парсера
        available_versions = gsparser.ConfigJSONConverter.AVAILABLE_VESRIONS
        if parser_version not in available_versions:
            raise ValueError(f'The version is not available. Available versions are: {available_versions}')

        self.parser_version = parser_version

    def set_schema(self, schema):
        """
        Задает схему формата данных в столбцах.

        schema -- схема хранения данных в несколько колонок на странице.

        Упрощенная схема. Всегда указана по умолчанию. 
        Данные будут выгружены как словарь из пар в столбцах key = data
        Кортеж из 2х элементов: schema = ('key', 'data'), где
        'key' - названия столбца с ключами
        'data' - названия столбца с данными
        
        Обычная схема. Данные будут дополнительно завернуты в словари с названием столбца данных.
        Словарь вида (Названия ключей словаря фиксированы!):
        schema = {
            'key': 'key'  # Название столбца с данными
            'data': ['value_1', 'value_2']  # Список названий столбцов данных
        }
        """

        if type(schema) not in (tuple, dict):
            raise ValueError(f'The schema should be tuple or dict!')

        self.schema = schema

    def set_format(self, format='json'):
        """
        Принудительно задать формат для страницы. JSON по умолчанию
        """

        available_formats = list(self._extractors.keys())
        if format not in available_formats:
            raise ValueError(f'Available formats are {available_formats}')

        self._format = format

    def set_raw_mode(self):
        """
        Если установлено, данные при сохранении в json не будут парсится.
        """

        self.is_raw = True

    def get(self, **params):
        """
        Возвращает данные в формате страницы. См. описание format ниже
        Когда формат не указан - возвращает сырые данные как двумерный массив.

        Понимает несколько схем компановки данных. Проверка по очереди:
        1. Используется схема данных. См. self.schema и self.set_schema()
        2. Свободный формат, первая строка - ключи, все последуюшие - данные

        **params - все параметры доступные для парсера parser.jsonify
        """

        if not self._cache:
            self._cache = self.worksheet.get_all_values()

        params['is_raw'] = self.is_raw
        params['schema'] = self.schema
        params['key_skip_letters'] = self.key_skip_letters
        params['parser_version'] = self.parser_version  # available version: v1, v2
        
        return self._extractors[self.format](self._cache, **params)
    
    def save(self, path=''):
        """
        Сохраняет страницу по указанному пути
        """

        tools.save_page(self, path)


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

        for page in self:
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
        Указать версию парсера (конвертора из формата конфигов в JSON)
        """
        
        # Взять версии парсера из класса парсера
        available_versions = gsparser.ConfigJSONConverter.AVAILABLE_VESRIONS
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
            page.save(path)


class GameConfigLite(Document):
    """
    GameConfigLite - Игровой конфиг состоящий только из одного документа. 
    Наследуется от класса Document и определяется id документа и обьектом GoogleOauth.
    
    См подробности по аутентификации тут: https://docs.gspread.org/en/latest/oauth2.html
    
    - spreadsheet_id -- id таблицы
    - client -- клиент авторизации GoogleOauth. 
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
    GameConfig - Обьект содержащий все документы конфигов указанные в настройках.
    Для получения из конфига документа по названию используется имя таблицы.
    Определяется списком id входящих в конфиг документов и обьектом GoogleOauth.
    
    См подробности по аутентификации тут: https://docs.gspread.org/en/latest/oauth2.html

    - spreadsheet_ids -- Список id входящих в конфиг документов
    - client -- клиент авторизации GoogleOauth. 
    """

    def __init__(self, spreadsheet_ids=[], client=None):
        self.client = client or gspread.oauth()
        self.spreadsheet_ids = spreadsheet_ids

        self.page_skip_letters = {'#', '.'}
        self.key_skip_letters = {'#', '.'}
        self.parser_version = 'v1'  # Available only 'v1' and 'v2' mode. See gsparser for details

        self._cache = []
        self._max_workers = 5

    @property
    def documents(self) -> list:
        if not self._cache:
            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                self._cache = list(pool.map(self._create_document, self.spreadsheet_ids))

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

    def set_parser_version(self, parser_version):
        """
        Указать версию парсера (конвертора из формата конфигов в JSON)
        """
        
        # Взять версии парсера из класса парсера
        available_versions = gsparser.ConfigJSONConverter.AVAILABLE_VESRIONS
        if parser_version not in available_versions:
            raise ValueError(f'The version is not available. Available versions are: {available_versions}')

        self.parser_version = parser_version
    
    def save(self, path='', mode=''):
        """
        If mode = 'full' is specified, it tries to save all pages of the document.
        IMPORTANT! Working pages are usually not prepared for saving and will fail.
        """

        for document in self.documents:
            document.save(path, mode)


