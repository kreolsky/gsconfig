# Справочник API

В этом разделе представлено подробное описание API основных классов библиотеки GSConfig.

## GoogleOauth

Класс для авторизации в Google API.

```python
class GoogleOauth():
    def __init__(self, keyfile=None) -> None:
        """
        Инициализация объекта авторизации.
        
        :param keyfile: Путь к файлу ключа сервисного аккаунта. Если None, 
                       используется интерактивная OAuth авторизация.
        """
        
    @property
    @lru_cache(maxsize=1)
    def client(self):
        """
        Возвращает авторизованный клиент gspread.
        Результат кэшируется для повторного использования.
        
        :return: Объект gspread.Client
        """
```

## Page

Класс для работы с листом Google Sheets.

```python
class Page(object):
    def __init__(self, worksheet):
        """
        Инициализация объекта Page.
        
        :param worksheet: Объект gspread.Worksheet
        """
        
    @property
    def title(self):
        """
        Возвращает исходное название страницы в таблице.
        
        :return: Строка с названием страницы
        """
        
    @property
    def name(self):
        """
        Возвращает название страницы без расширения.
        
        :return: Строка с названием страницы без расширения
        """
        
    @property
    def format(self):
        """
        Возвращает формат страницы на основе расширения в названии.
        
        :return: Строка с форматом ('json', 'csv', 'raw')
        """
        
    def set_key_skip_letters(self, key_skip_letters):
        """
        Устанавливает символы для пропуска ключей.
        
        :param key_skip_letters: Список или множество символов
        """
        
    def set_parser_version(self, parser_version):
        """
        Устанавливает версию парсера ('v1' или 'v2').
        
        :param parser_version: Строка с версией парсера
        """
        
    def set_schema(self, schema):
        """
        Устанавливает схему данных.
        
        :param schema: Кортеж ('key', 'data') или словарь {'key': 'key', 'data': ['value1', 'value2']}
        """
        
    def set_format(self, format='json'):
        """
        Принудительно устанавливает формат для страницы.
        
        :param format: Строка с форматом ('json', 'csv', 'raw')
        """
        
    def set_raw_mode(self):
        """
        Устанавливает режим, при котором данные не парсятся.
        """
        
    def get(self, **params):
        """
        Возвращает данные страницы в соответствии с форматом и схемой.
        
        :param params: Дополнительные параметры для парсера
        :return: Данные в формате, соответствующем настройкам страницы
        """
        
    def save(self, path=''):
        """
        Сохраняет данные страницы в файл.
        
        :param path: Путь для сохранения
        """
```

## Document

Класс для работы с документом Google Sheets.

```python
class Document(object):
    def __init__(self, spreadsheet):
        """
        Инициализация объекта Document.
        
        :param spreadsheet: Объект gspread.Spreadsheet
        """
        
    def __getitem__(self, title):
        """
        Возвращает страницу по названию.
        
        :param title: Название страницы
        :return: Объект Page
        """
        
    def __iter__(self):
        """
        Итератор по основным страницам документа 
        (не начинающимся с символов в page_skip_letters).
        
        :yield: Объекты Page
        """
        
    @property
    def title(self):
        """
        Возвращает название документа.
        
        :return: Строка с названием документа
        """
        
    @property
    def page1(self):
        """
        Возвращает первую основную страницу документа.
        
        :return: Объект Page
        """
        
    @property
    def pages(self):
        """
        Итератор по всем страницам документа, включая служебные.
        
        :yield: Объекты Page
        """
        
    def set_page_skip_letters(self, page_skip_letters):
        """
        Устанавливает символы для пропуска страниц.
        
        :param page_skip_letters: Список или множество символов
        """
        
    def set_key_skip_letters(self, key_skip_letters):
        """
        Устанавливает символы для пропуска ключей.
        
        :param key_skip_letters: Список или множество символов
        """
        
    def set_parser_version(self, parser_version):
        """
        Устанавливает версию парсера ('v1' или 'v2').
        
        :param parser_version: Строка с версией парсера
        """
        
    def save(self, path='', mode=''):
        """
        Сохраняет все основные страницы документа.
        
        :param path: Путь для сохранения
        :param mode: Режим сохранения ('full' для сохранения всех страниц)
        """
```

## GameConfigLite

Класс для работы с игровой конфигурацией из одного документа.

```python
class GameConfigLite(Document):
    def __init__(self, spreadsheet_id: str, client=None, params: dict = {}):
        """
        Инициализация конфигурации игры.
        
        :param spreadsheet_id: ID таблицы Google Sheets
        :param client: Клиент авторизации GoogleOauth
        :param params: Дополнительные параметры конфигурации
        """
        
    @property
    @lru_cache(maxsize=1)
    def spreadsheet(self) -> gspread.Spreadsheet:
        """
        Возвращает объект gspread.Spreadsheet.
        Результат кэшируется для повторного использования.
        
        :return: Объект gspread.Spreadsheet
        """
```

## GameConfig

Класс для работы с игровой конфигурацией из нескольких документов.

```python
class GameConfig(object):
    def __init__(self, spreadsheet_ids: list, client: GoogleOauth, params: dict = {}):
        """
        Инициализация конфигурации игры.
        
        :param spreadsheet_ids: Список ID таблиц Google Sheets
        :param client: Клиент авторизации GoogleOauth
        :param params: Дополнительные параметры конфигурации
        """
        
    @property
    @lru_cache(maxsize=1)
    def documents(self) -> list:
        """
        Возвращает список объектов Document для всех документов.
        Результат кэшируется для повторного использования.
        
        :return: Список объектов Document
        """
        
    def __iter__(self):
        """
        Итератор по документам конфигурации.
        
        :yield: Объекты Document
        """
        
    def __getitem__(self, title):
        """
        Возвращает документ по названию.
        
        :param title: Название документа
        :return: Объект Document
        :raises KeyError: Если документ не найден
        """
        
    def set_parser_version(self, parser_version):
        """
        Устанавливает версию парсера ('v1' или 'v2').
        
        :param parser_version: Строка с версией парсера
        """
        
    def save(self, path='', mode=''):
        """
        Сохраняет все документы конфигурации.
        
        :param path: Путь для сохранения
        :param mode: Режим сохранения ('full' для сохранения всех страниц)
        """
```

## ConfigJSONConverter

Класс для конвертации промежуточного формата в JSON.

```python
class ConfigJSONConverter:
    AVAILABLE_VESRIONS = ('v1', 'v2')
    
    def __init__(self, params={}):
        """
        Инициализация конвертера.
        
        :param params: Параметры конвертера
        """
        
    def jsonify(self, string: str, is_raw: bool = False) -> dict | list:
        """
        Преобразует строку в промежуточном формате в структуры данных Python.
        
        :param string: Строка в промежуточном формате
        :param is_raw: Если True, строка не будет конвертироваться
        :return: Словарь или список с данными
        """
```

## Template

Класс для работы с шаблонами.

```python
class Template(object):
    def __init__(self, path='', body='', pattern=None, strip=True, jsonify=False):
        """
        Инициализация шаблона.
        
        :param path: Путь к файлу шаблона
        :param body: Шаблон в виде строки (альтернатива path)
        :param pattern: Паттерн для поиска переменных в шаблоне
        :param strip: Отрезать ли кавычки от строк при подстановке
        :param jsonify: Преобразовывать ли результат в JSON объект
        """
        
    @property
    def title(self) -> str:
        """
        Возвращает название файла шаблона.
        
        :return: Строка с названием шаблона
        """
        
    @property
    def keys(self) -> list:
        """
        Возвращает список ключей, используемых в шаблоне.
        
        :return: Список строк с ключами
        """
        
    @property
    def body(self) -> str:
        """
        Возвращает тело шаблона.
        
        :return: Строка с телом шаблона
        """
        
    def set_path(self, path=''):
        """
        Устанавливает путь к файлу шаблона.
        
        :param path: Путь к файлу шаблона
        """
        
    def set_body(self, body=''):
        """
        Устанавливает тело шаблона.
        
        :param body: Шаблон в виде строки
        """
        
    def render(self, balance: dict):
        """
        Заполняет шаблон данными.
        
        :param balance: Словарь с данными для подстановки
        :return: Заполненный шаблон в виде строки или структуры данных
        """
        
    # Алиас для метода render
    make = render
```

## Extractor

Класс для извлечения данных из страниц Google Sheets.

```python
class Extractor:
    def __init__(self):
        """
        Инициализация экстрактора.
        """
        
    def get(self, page_data, format='json', **params):
        """
        Извлекает данные в указанном формате.
        
        :param page_data: Двумерный массив данных (список списков)
        :param format: Формат данных ('json', 'csv', 'raw')
        :param params: Дополнительные параметры для парсера
        :return: Данные в указанном формате
        """
```

## tools

Модуль с утилитами для работы с данными.

```python
def save_page(page, path=''):
    """
    Сохраняет страницу по указанному пути.
    
    :param page: Объект Page
    :param path: Путь сохранения объекта
    """
    
def save_csv(data, title, path=''):
    """
    Сохраняет данные в формате CSV.
    
    :param data: Двумерный массив данных (список списков)
    :param title: Название файла
    :param path: Путь для сохранения
    """
    
def save_json(data, title, path=''):
    """
    Сохраняет данные в формате JSON.
    
    :param data: Данные для сохранения
    :param title: Название файла
    :param path: Путь для сохранения
    """
    
def save_raw(data, title, path=''):
    """
    Сохраняет данные в исходном формате.
    
    :param data: Данные для сохранения
    :param title: Название файла
    :param path: Путь для сохранения
    """
    
def dict_to_str(source, tab='', count=0):
    """
    Преобразует словарь в форматированную строку.
    
    :param source: Исходный словарь
    :param tab: Символ табуляции
    :param count: Начальный уровень вложенности
    :return: Строка с представлением словаря
    """
    
def load_json(filename, path=''):
    """
    Загружает данные из JSON файла.
    
    :param filename: Имя файла
    :param path: Путь к файлу
    :return: Загруженные данные
    """
```
