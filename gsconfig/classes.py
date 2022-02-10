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


class Worksheet(object):
    def __init__(self, page):
        self._sheet = page
        self._title = page['properties']['title']
        self.id = page['properties']['sheetId']
        self.index = page['properties']['index']
        self._data_parser = {
            'json': self.get_as_json,
            'csv': self.get_as_csv,
            'localization': self.get_as_localization}
        self.comment_letters = ['#', '@']  # Символ комментария. Ключи маркированные "#" не экспортируются.

    @property
    def rows(self):
        return self._sheet['properties']['gridProperties']['rowCount']

    @property
    def columns(self):
        return self._sheet['properties']['gridProperties']['columnCount']

    @property
    def title(self):
        return self._title

    @property
    def type(self):
        title_type_list = self._title.split('.')
        if len(title_type_list) > 1:
            return title_type_list[-1]

        return 'json'

    def __repr__(self):
        return json.dumps(self.get_page_data())

    def set_comment_letters(self, comment_letters):
        if not isinstance(comment_letters, list):
            raise GSConfigError(f'It have to be a list!')

        self.comment_letters = comment_letters

    def get_all_values(self, raw_data=False):
        data_type = 'effectiveValue'
        if raw_data:
            data_type = 'userEnteredValue'

        page = []
        bufer = []
        for raw_data_line in self._sheet['data'][0]['rowData']:
            line = []

            if not raw_data_line:
                bufer.append(line)
                continue

            for cell in raw_data_line['values']:
                if data_type not in cell:
                    line.append('')
                    continue

                line.append(list(cell[data_type].values())[0])

            # Отсеивание пустых строк в конце документа.
            # Пустые строки складываются в буфер, если после пустых окажется
            # заполненная, то пустые тоже будут добавлены в документ
            if not sum([len(str(x)) for x in line]):
                bufer.append(line)
                continue

            if bufer:
                page.extend(bufer)
                bufer = []

            page.append(line)

        return page

    def get_page_data(self, raw_data=False):
        return self._data_parser[self.type]()

    def get_as_json(self, key='key', value='value', to_num=True, unwrap_list=False, is_text=False):
        """
        Парсит данные со страницы гуглодоки в формат json и сохраняет в файл.
        См. tools.config_to_json

        key - заголовок столбца с ключами.
        value - заголовок столбца с данными.
        to_num - нужно ли пытаться преобразовывать значения в числа. True (по умолчанию) пытается преобразовать.
        unwrap_list - нужно ли вытаскивать словари из списков единичной длины.
            False (по умолчанию) вытаскивает из списков все обьекты КРОМЕ словарей.
            True - вынимает из список ВСЕ типы обьектов, включая словари.
        """
        page_data = self.get_all_values()

        headers = page_data[0]
        data = page_data[1:]

        # Если документ из двух колонок. Ключами в столбце key и значением в столбце value
        if key in headers and value in headers:
            key_index = headers.index(key)
            value_index = headers.index(value)

            out = {
                line[key_index]: config_to_json(line[value_index], to_num=to_num, unwrap_list=unwrap_list, is_text=is_text)
                for line in data if len(line[0]) > 0
            }

            return out

        # Первая строка с заголовками, остальные строки с данными
        out = []
        for values in data:
            bufer = {
                key: config_to_json(value, to_num=to_num, unwrap_list=unwrap_list, is_text=is_text)
                for key, value in zip(headers, values)
                if not any([key.startswith(x) for x in self.comment_letters])
                and len(key) > 0
            }

            out.append(bufer)

        if len(out) == 1:
            out = out[0]

        return out

    def get_as_localization(self):
        return self.get_as_json(is_text=True)

    def get_as_csv(self):
        data = self.get_all_values()

        columns = len(data[0])
        for line in data:
            add_columns_num = columns - len(line)
            line.extend([''] * add_columns_num)

        return data


class Spreadsheet(object):
    """
    Класс прокладка, создается из полного бекапа гуглотаблицы
    """
    def __init__(self, full_gspread_json):
        self._source = full_gspread_json
        self._properties = self._source['properties']
        self.id = self._source['spreadsheetId']
        self.url = self._source['spreadsheetUrl']
        self.ts = self._source['timestamp']
        self.comment_letters = ['@', '#', '.'] # Эскпортитуются только страницы начинающиеся с этого символа.
        self.notice = ''
        self._pages = None

    @property
    def _sheets(self):
        return self._source['sheets']

    @property
    def title(self):
        return self._properties['title'].split('.')[0]

    def __iter__(self):
        for page in self.worksheets():
            if any([page.title.startswith(x) for x in self.comment_letters]):
                continue

            yield(page)

    def __repr__(self):
        return f'{self.title}: ' + ', '.join(x.title for x in self.worksheets())

    def __contains__(self, value):
        return value in [x.title for x in self.worksheets()]

    def __getitem__(self, title):
        return self.worksheet(title)

    def set_notice(self, notice):
        self.notice = notice

    def set_comment_letters(self, comment_letters):
        if not isinstance(comment_letters, list):
            raise GSConfigError(f'It has to be a list!')

        self.comment_letters = comment_letters

    def worksheets(self):
        """
        Returns all worksheets from document.
        """
        if not self._pages:
            self._pages = [Worksheet(x) for x in self._sheets]

        return self._pages

    def worksheet(self, title):
        """
        Returns a worksheet with specified `title`.
        """
        return next(filter(lambda x: x.title == title, self.worksheets()))

    def get_raw_data(self):
        return self._source

    def find_and_replace(self, source, target):
        self._source['sheets'] = json.loads(re.sub(source, target, json.dumps(self._sheets)))


class GSpreadsheet():
    def __init__(self, client, spreadsheet_id):
        self.client = client  # Обьект авторизации в гугле GoogleOauth
        self.spreadsheet_id = spreadsheet_id  # ID гуглотаблицы
        self._spreadsheet = None

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.title}' id:{self.spreadsheet_id}>"

    def __iter__(self):
        for page in self.spreadsheet:
            yield page

    def __getitem__(self, title):
        return self.spreadsheet[title]

    @property
    def spreadsheet(self):
        """
        Возвращает обьект Spreadsheet.
        """
        if not self._spreadsheet:
            gspread = self.client.connect.open_by_key(self.spreadsheet_id)
            local_gspread_json = gspread.fetch_sheet_metadata(params = {"includeGridData": "true"})  # Весь документ
            local_gspread_json['timestamp'] = str(datetime.now())

            self._spreadsheet = Spreadsheet(local_gspread_json)

        return self._spreadsheet


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


class GameConfigLite(GSpreadsheet):
    def save_config(self):
        pass

    def save_backup(self, path=''):
        pass

    def backup_load(self, path=''):
        pass

    def pages(self):
        pass

    def get_raw_data(self):
        return self.spreadsheet.get_raw_data()


class GameConfig(object):
    """
    Обьект содержащий все конфиги указанные в настройках.
    Принимает настройки как из гуглотаблицы так и в виде словаря вида. Если указано и то и то,
    то будет использован словарь.

    settings -- словарь с настройками.
    Либо id документа и название вкладки со списком всех документов конфига
        gspread_id -- id таблицы со списко конфигов
        page_title -- заголовок страницы в таблице со списком документов конфига

    Либо словарь вида {document_title: gspread_id, ...}
        document_title -- название
        gspread_id -- id документа

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
            self._documents = [Spreadsheet(x) for x in backup['documents']]
            self._settings = backup['settings']

        elif 'gspread_id' in settings:
            self._settings_gspread_id = settings['gspread_id']
            self._settings_page_name= settings['page_title']

        elif settings:
            self._settings = {
                key : GSpreadsheet(self.client, value)
                for key, value in settings.items()
            }

    def __repr__(self):
        return f'{self.__class__.__name__}: ' + ', '.join([x.title for x in self.documents])

    def __iter__(self) -> Spreadsheet:
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
            settings = settings_obj[self._settings_page_name].get_as_json()

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

    def _create_gspread(self, title, owner, dummy_page):
        """
        title -- название документа.

        owner -- мыло владельца документы.
        Обязательный параметр, иначе доступ к доке будет только у бота.

        dummy_page -- id страницы которую брать в качестве донора,
        актуально для конфигов которые сожержат кастомные формулы.
        По уморочанию они не сохраняются, тогда есть смысл страницы не создавать,
        а копировать с той в которой эти формулы есть.
        """
        if dummy_page:
            new_gspread = self.client.connect.copy(dummy_page, title)
        else:
            new_gspread = self.client.connect.create(title)

        new_gspread.share(owner, perm_type='user', role='owner')
        return new_gspread

    def fork(self, gspread_id='', owner='', dummy_page=''):
        # Создать гуглодокумент для каждого документа конфигов и запомнить новые id
        # Создасть словарь замены id
        # Заменить старые id на новые
        # Залить в каждый документ его содержимое
        # Залить список новых документов в указанный гуглофайл или создать новый если не указано

        new_config = {x.title: self._create_gspread(x.title, owner, dummy_page) for x in self.documents}

        # Словарь замены id подгружаемых документов
        # Конфиг должен быть изолирован от внешних ссылок
        old_to_new = {}
        for title, gspread in new_config.items():
            old_to_new[title] = {
                'old': self.document(title).id,
                'new': gspread.id
            }

        for document in self.documents:
            # Замена ссылок.
            # Важно! Конфиг должен быть изначально самодостаточен
            for x in old_to_new.values():
                document.find_and_replace(x['old'], x['new'])

            new_document = new_config[document.title]
            sheet_to_del = new_document.get_worksheet(0)

            # Заполнение новых документов
            for page in document.worksheets():
                sheet = new_document.add_worksheet(page.title, page.rows, page.columns)
                sheet.append_rows(page.get_all_values(raw_data=True), value_input_option='USER_ENTERED')

            new_document.del_worksheet(sheet_to_del)

        out = {key: value['new'] for key, value in old_to_new.items()}
        return out
