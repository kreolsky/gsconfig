import gspread
import json
from concurrent.futures import ThreadPoolExecutor

from . import tools


class GSConfigError(Exception):
    def __init__(self, text='', value=-1):
        self.text = text
        self.value = value

    def __str__(self):
        return f'{self.text} Err no. {self.value}'

parsers = {
    'raw': tools.parser_dummy,
    'csv': tools.parser_dummy,
    'json': tools.parser_json
}

class Page(object):
    """
    Класс обёртка поверх gspread.Worksheet
    """

    def __init__(self, worksheet, parsers = parsers):
        self.worksheet = worksheet # исходный обьект gspread.Worksheet
        self.parsers = parsers

        # Ключи маркированные этими символами не экспортируются.
        self.key_skip_letters = []
        self.cache = None
        self.parser_mode = None

    @property
    def title(self):
        """
        Заголовок страницы как есть, то как называется страница в таблице
        """

        return self.worksheet.title

    @property
    def name(self):
        """
        Название страницы.
        Из title удален суффикс определяющий формат данных,
        если для него указан парсер
        """

        name = self.title
        if any([name.endswith(f'.{x}') for x in self.parsers.keys()]):
            name = name[ : name.rfind('.')]

        return name

    @property
    def format(self):
        """
        Определяет формат данных по названию страницы.
        Если ничего не указано, то определяет как raw
        """

        format = 'raw'
        if any([self.title.endswith(f'.{x}') for x in self.parsers.keys()]):
            format = self.title[self.title.rfind('.') + 1 : ]

        return format

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

    def get(self, format=None, mode=None, **params):
        """
        Достаёт данные со страницы в формате адекватном их типу.
        Если формат не указан отдельно и не задан пользователем, то пытается достать как raw
        format - формат хранения данных
            json - собирает в словарь и парсит значения
            csv - возвращает данные как двумерный массив. Всегда БЕЗ парсинга!
            raw - возвращает данные как двумерный массив. Всегда БЕЗ парсинга!
        mode - указание парсить данные или нет
            raw - данные всегда будут возвращены БЕЗ парсинга
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
    Класс обертка поверх gspread.Spreadsheet
    """

    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet # Исходный обьект gspread.Spreadsheet
        # self.page_skip_letters = []
        # self.key_skip_letters = []

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.spreadsheet.title}' id:{self.spreadsheet.id}>"

    def __getitem__(self, title):
        page = Page(self.spreadsheet.worksheet(title))
        page.set_key_skip_letters(self.key_skip_letters)
        page.parser_mode = self.parser_mode
        return page

    def __iter__(self):
        for page in self.spreadsheet.worksheets():
            page = Page(page)
            page.set_key_skip_letters(self.key_skip_letters)
            page.parser_mode = self.parser_mode
            yield page

    @property
    def page1(self):
        """
        Возвращает первую основную страницу их тех,
        которые НЕ начинаются с символов в page_skip_letters.
        """
        for page in self.pages():
            return page

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

    def __init__(self, spreadsheet_id, client=None):
        self.client = client or gspread.oauth() # Обьект авторизации в гугле GoogleOauth
        self.spreadsheet_id = spreadsheet_id  # ID гуглотаблицы
        self.cache = None
        self.page_skip_letters = ['#', '.']
        self.key_skip_letters = ['#', '.']
        self.parser_mode = 'v1'

    @property
    def spreadsheet(self):
        """
        Возвращает обьект gspread.Spreadsheet
        """

        if not self.cache:
            self.cache = self.client.open_by_key(self.spreadsheet_id)

        return self.cache

    def save(self, path='', mode=''):
        """
        Если указано mode = 'full', то пытается сохранить все страницы документа.
        ВАЖНО! Рабочие страницы обычно не подготовлены к сохранению и будут падать.
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
            self._settingspage_name = settings['page_title']

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
