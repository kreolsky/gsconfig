import os
import gspread
import json
import re
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property

from . import tools


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
    """
    def __init__(self, path='', body='', pattern=None, command_letter=None):
        self.path = path
        self.pattern = pattern or r'\{([a-z0-9_!]+)\}'
        self.command_letter = command_letter or '!'
        self.command_handlers = {
            'dummy': lambda x: x,
            'float': lambda x: float(x),
            'int': lambda x: int(x),
            'str': lambda x: str(x)
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

    def make(self, data) -> str:
        """
        Заполняет шаблон данными.
        ВАЖНО! Для сохранения в JSON необходимо заполнять все поля шаблона!
        """

        def replace_keys(match):
            key_command_pair = match.group(1).split(self.command_letter)

            # Ключ, который будет искаться для замены 
            key = key_command_pair[0]

            # Обработка ошибки отсутствия ключа
            if key not in data:
                raise KeyError(f"Key '{key}' not found in template data.")
            insert_data = data[key]

            # Команда ВСЕГДА идет после command_letter!
            if self.command_letter in match.group(1):
                command = key_command_pair[-1]

                # Обработка ошибки отсутствия команды
                if command not in self.command_handlers:
                    raise ValueError(f"Command '{command}' is not supported by Template class")
                insert_data = self.command_handlers[command](insert_data)

            return str(insert_data)

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

    def get(self, format=None, mode=None, **params):
        """
        Retrieves data from the page in a format appropriate for its type.
        If the format is not specified separately and not set by the user, it tries to get it as raw
        
        format -- data storage format
            json - collects into a dictionary and parses values
            csv - returns data as a two-dimensional array. Always WITHOUT parsing!
            raw - returns data as a two-dimensional array. Always WITHOUT parsing!
        
        mode -- whether to parse data or not
            raw - data will always be returned WITHOUT parsing
        """

        if not self._cache:
            self._cache = self.worksheet.get_all_values()

        params['is_raw'] = mode == 'raw'
        params['key_skip_letters'] = self.key_skip_letters
        params['version'] = self.parser_version
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
        page.parser_version = self.parser_version
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
        self.parser_version = 'v1'  # Available only 'v1' and 'v2' mode. See gsparser for details

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
