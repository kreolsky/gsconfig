import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from . import tools
from . import gsparser


"""
Data extractors for Page class
"""

def filter_page_data(required_keys, page_data):
    """
    Фильтрует данные, оставляет только запрошенные столбцы и удаляет пустые строки.

    :param required_keys: список ключей (заголовков), которые нужно оставить
    :param page_data: двумерный массив (список списков)
    :return: отфильтрованный двумерный массив
    """

    # Словарь индексов всех ключей (оптимизация скорости исполнения)
    # Ключи (заголовки) всегда идут нулевой строкой (page_data[0])
    header_to_index = {header: idx for idx, header in enumerate(page_data[0])}
    indices = [header_to_index[h] for h in required_keys]

    # Фильтрация данных по указанным индексам столбцов и удаление пустых строк
    # Распаковывает на заголовки и данные
    heades, *data = [
        # Оставляем только указанные столбцы
        [row[idx] for idx in indices] for row in page_data
        # ... и непустые строки
        if any(row[idx].strip() != '' for idx in indices)
    ]
    
    return heades, data

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

    # Исходные заголовки импортируемых данных
    headers_raw = page_data[0]

    # Парсер конфигов в JSON
    parser = gsparser.ConfigJSONConverter(params)

    # Указана обычная схема (schema) хранения данных. Данные в несоклько колонок 
    # schema = {'key': 'key', 'data': ('value_1', 'value_2'), 'default'='value_2'}, где 
    # 'key' - название столбца с ключами 
    # 'data' - кортеж названий столбцов с данными 
    # 'default' - столбец с данными по умолчанию
    if isinstance(schema, dict):
        required_keys = [schema['key']] + list(schema['data'])
        headers, data = filter_page_data(required_keys, page_data)

        key_index = headers.index(schema['key'])  # Индекс столбца ключей
        data_indices = [headers.index(x) for x in schema['data']]  # Индексы столбцов данных
        
        # Указать столбец с дефолтными данными. 
        # Если в схеме default не указан, тогда дефолтным проходит значение первого столбца данных
        # Из него буду взяты данные когда в соответствующих строках других столбцов пусто
        default_data_key = schema.get('default', schema['data'][0])
        default_data_index = headers.index(default_data_key)

        out = {}
        for data_index in data_indices:
            bufer = {}
            for line in data:                
                # Если данные пустые, то брать из дефолтного столбца
                line_data = line[data_index] or line[default_data_index]                
                bufer[line[key_index]] = parser.jsonify(line_data)

            out[headers[data_index]] = bufer

        return out

    # Простая схема данных. Документ из двух колонок schema = ('key', 'data'), где 
    # 'key' - название столбца с ключами 
    # 'data' - название столбца с данными 
    # Схема -- кортеж и все элементы схемы представлены в заголовке
    if isinstance(schema, tuple) and all(x in headers_raw for x in schema):
        headers, data = filter_page_data(schema, page_data)

        key_index = headers.index(schema[0])  # Столбец ключей
        data_index = headers.index(schema[-1])  # Столбец данным

        out = {row[key_index]: parser.jsonify(row[data_index]) for row in data}
        return out

    # Обычный документ, данные расположены строками
    # Первая строка с заголовками, остальные строки с данными
    required_keys = [key for key in headers_raw if not any(key.startswith(x) for x in key_skip_letters) and len(key) > 0]
    headers, data = filter_page_data(required_keys, page_data)
    
    out = []
    for line in data:
        bufer = [f'{key} = {{{str(value)}}}' for key, value in zip(headers, line)]
        bufer = parser.jsonify(', '.join(bufer))
        out.append(bufer)

    # Развернуть лишнюю вложенность когда только один элемент
    if len(out) == 1:
        return out[0]

    return out

"""
Classes
"""

class GoogleOauth():
    def __init__(self, keyfile=None) -> None:
        self.keyfile = keyfile

    @property
    @lru_cache(maxsize=1)
    def client(self):
        """
        Коннект к гуглотабличкам. См подробности в офф доке gspread

        https://github.com/burnash/gspread
        http://gspread.readthedocs.io/en/latest/
        """

        if not self.keyfile: 
            return gspread.oauth()
        
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.keyfile, scope)
        return gspread.authorize(credentials)


class GSConfigError(Exception):
    def __init__(self, text='', value=-1):
        self.text = text
        self.value = value

    def __str__(self):
        return f'{self.text} Err no. {self.value}'


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
            'default': 'value_2  # Определяет какой столбец будет дефолтным (из него берутся данные когда других пусто)
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

        params['is_raw'] = params.get('is_raw', self.is_raw)
        params['schema'] = params.get('schema', self.schema)
        params['key_skip_letters'] = params.get('key_skip_letters', self.key_skip_letters)
        params['parser_version'] = params.get('parser_version', self.parser_version)  # available version: v1, v2

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

    :param spreadsheet_id: ID таблицы Google Sheets
    :param client: Клиент авторизации GoogleOauth
    :param params: Дополнительные параметры конфигурации
    """

    def __init__(self, spreadsheet_id: str, client=None, params: dict = {}):
        """
        Инициализация конфигурации игры

        Допустимые дополнительные параметры:
        - page_skip_letters: набор символов для пропуска страниц (по умолчанию: {'#', '.'})
        - key_skip_letters: набор символов для пропуска ключей (по умолчанию: {'#', '.'})
        - parser_version: версия парсера (доступны 'v1' и 'v2', по умолчанию: 'v1')
        """
        self.client = client  # GoogleOauth object
        self.spreadsheet_id = spreadsheet_id  # Google Sheet ID

        self.page_skip_letters = params.get('page_skip_letters', {'#', '.'})
        self.key_skip_letters = params.get('key_skip_letters', {'#', '.'})
        self.parser_version = params.get('parser_version', 'v1')  # TODO: добавить валидацию

    @property
    @lru_cache(maxsize=1)
    def spreadsheet(self) -> gspread.Spreadsheet:
        """
        Возвращает объект gspread.Spreadsheet
        """
        return self.client.open_by_key(self.spreadsheet_id)


class GameConfig(object):
    """
    GameConfig - Обьект содержащий все документы конфигов указанные в настройках.
    Для получения из конфига документа по названию используется имя таблицы.
    Определяется списком id входящих в конфиг документов и обьектом GoogleOauth.
    
    См подробности по аутентификации тут: https://docs.gspread.org/en/latest/oauth2.html

    :param spreadsheet_id: ID таблицы Google Sheets
    :param client: Клиент авторизации GoogleOauth
    :param params: Дополнительные параметры конфигурации
    """

    def __init__(self, spreadsheet_ids: list, client: GoogleOauth, params: dict = {}):
        """
        Инициализация конфигурации игры

        Допустимые дополнительные параметры:
        - page_skip_letters: набор символов для пропуска страниц (по умолчанию: {'#', '.'})
        - key_skip_letters: набор символов для пропуска ключей (по умолчанию: {'#', '.'})
        - parser_version: версия парсера (доступны 'v1' и 'v2', по умолчанию: 'v1')
        """
        self.client = client  # GoogleOauth object
        self.spreadsheet_ids = spreadsheet_ids  # Config ids

        self.page_skip_letters = params.get('page_skip_letters', {'#', '.'})
        self.key_skip_letters = params.get('key_skip_letters', {'#', '.'})
        self.parser_version = params.get('parser_version', 'v1')  # TODO: добавить валидацию

        self._max_workers = 5

    @property
    @lru_cache(maxsize=1)
    def documents(self) -> list:
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            return list(pool.map(self._create_document, self.spreadsheet_ids))
    
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
