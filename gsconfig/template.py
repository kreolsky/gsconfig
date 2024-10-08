import os
import json
import re


"""
Template key command handlers
"""

def key_command_extract(array):
    """
    extract -- Вытаскивает элемент из списка (list or tuple) если это список единичной длины.

    Пример: По умолчанию парсер v1 не разворачивает словари и они приходят вида [{'a': 1, 'b': 2}],
    если обязательно нужен словарь, то extract развернёт полученный список до {'a': 1, 'b': 2}
    
    ПРИМЕЧАНИЕ: парсер v2 всегда разворачивает словари по умолчанию
    """
    if len(array) == 1 and type(array) in (list, tuple):
        return array[0]
    return array

def key_command_wrap(array):
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

def key_command_string(arg):
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

class Template(object):
    """
    Класс шаблона из которого будет генериться конфиг.
    Паттерн ключа и символ отделяющий команду можно переопределить.

    - path -- путь для файла шаблона  
    - body -- можно задать шаблон как строку
    - variable_pattern -- паттерн определения ключей (переменных) в шаблоне. r'\{%\s*([a-z0-9_!]+)\s*%\}' - по умолчанию. Пример: {% variable %}
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

    КОМАНДЫ В КЛЮЧАХ ШАБЛОНА:
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

    КОМАНДЫ УПРАВЛЕНИЯ СТРОКАМИ ШАБЛОНА:
    if -- сохранить строку между тегами условия если параметр True, иначе удалить
    Например, для `{% if params %} _KEEP_ME_OR_DELETE_ME_ {% endif %}`
        if -- ключевое слово условия, открывающий тег
        params -- параметр
        endif -- закрывающий тег
        строка "_KEEP_ME_OR_DELETE_ME_" будет сохранена если params == True
    
    КОММЕНТАРИИ:
    {# Комментариц в теле шаблона выглядит так #}
    """

    def __init__(self, path='', body='', pattern=None, strip=True, jsonify=False):
        self.path = path
        self.variable_pattern = pattern or r'\{%\s*([a-z0-9_!]+)\s*%\}'
        self.strip = strip
        self.jsonify = jsonify
        self.key_command_letter = '!'  # символ отделяющий команду от ключа
        self.key_command_handlers = {
            'dummy': lambda x: x,
            'float': lambda x: float(x),
            'int': lambda x: int(x),
            'json': lambda x: json.dumps(x),
            'string': key_command_string,
            'extract': key_command_extract,
            'wrap': key_command_wrap
        }
        self.string_comment_pattern = r'\{\#\s*(.*?)\s*\#\}'
        self.string_command_pattern = r'(\{%\s*([\w_]+)\s+([\w_]+)\s*%\}(.*?)\{%\s*end\2\s*%\})'
        self.string_command_handlers = {
            'if': lambda params, content, balance: content if balance.get(params) else '',
        }
        self._body = body
        self._keys = []

    def __str__(self):
        return self.title

    @property
    def title(self) -> str:
        return os.path.basename(self.path)

    @property
    def keys(self) -> list:
        """
        Возвращает все ключи используемые в шаблоне.
        """

        if not self._keys:
            self._keys = re.findall(self.variable_pattern, self.body)
        return self._keys

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

    def render(self, balance: dict):
        """
        Заполняет шаблон данными.
        ВАЖНО! Для сохранения в JSON необходимо заполнять все поля шаблона!

        balance -- словарь (dict) с балансом (данными для подстановки), где:
            key - переменная, которую необходимо заменить
            value - значение для замены

        Свойства класса влияющие на сборку конфига из шаблона:
        
        self.strip -- Будет ли отрезать от строк лишние кавычки. 
            True (по умолчанию) - Отрезает кавычки от строк. 
            В шаблоне НЕОБХОДИМО проставлять кавычки для всех строковых данных.
            Либо явно указывать трансформацию в строку при помощи команды !string

            False - Строки будут автоматически завернуты в кавычки. 
            Невозможно использовать переменные в подстроках.
        
        self.jsonify -- Забрать как словарь. False - по умолчанию, забирает как строку.

        :param balance: Словарь с данными для подстановки в шаблон.
        :return: Заполненный шаблон.
        """

        # Обработка комментариев в теле шаблона
        template_body = self._process_comments(self.body)

        # Управление строками, обработка команд управления строками (strings_command_handlers)
        template_body = self._process_template(template_body, balance)
        
        # Заполнение шаблона данными
        # Заменяем ключи в шаблоне на соответствующие значения из balance
        out = self._process_variables(template_body, balance)
        
        # Преобразуем результат в JSON, если необходимо
        if self.jsonify:
            try:
                out = json.loads(out)
            except json.JSONDecodeError as e:
                raise ValueError(f"\nError during jsonify in {self.title}\n{str(e)}\n{out}")

        return out
    
    # Алиас для метода render для обеспечения обратно совместимости
    make = render

    def _process_comments(self, template_body):
        """
        Удаление комментариев из шаблона.
        
        :param template_body: Содержимое файла.
        :return: Содержимое файла без комментариев.
        """
        # Регулярное выражение для поиска комментариев в шаблоне.
        comment_pattern = re.compile(self.string_comment_pattern, re.DOTALL)
        
        # Удаляем все комментарии из шаблона.
        template_body = comment_pattern.sub('', template_body)
        
        return template_body

    def _process_template(self, template_body, balance):
        """
        Управление строками, обработка команд управления строками (strings_command_handlers)
        Доступные команды:
        keep_it [param] -- сохраняет строку если param == true, иначе удаляет
        del_it [param] -- удаляет строку если param == true, иначе сохраняет
        
        :param template_body: Содержимое файла.
        :param balance: Словарь с данными для подстановки в шаблон.
        :return: Обработанное содержимое файла.
        """

        # Регулярное выражение для поиска строковых команд в шаблоне.
        string_command_pattern = re.compile(self.string_command_pattern, re.DOTALL)
        
        # Находим все строки, содержащие команды.
        matches = string_command_pattern.findall(template_body)
        
        # Обрабатываем каждую строку.
        for match in matches:
            full_match, command, params, content = match
            
            # Проверяем, что команда поддерживается.
            if command not in self.string_command_handlers:
                raise ValueError(f"String command '{command}' is not supported by Template class. Available only {list(self.string_command_handlers.keys())}")
            
            # Обрабатываем строку в соответствии с командой.
            processed_content = self.string_command_handlers[command](params, content, balance)
            
            # Заменяем исходную строку на обработанную.
            template_body = template_body.replace(full_match, processed_content)
        
        return template_body

    def _process_variables(self, template_body, balance):
        """
        Заполнение шаблона данными. Заменяет ключи в шаблоне на соответствующие значения из balance.
        
        :param template_body: Содержимое файла.
        :param balance: Словарь с данными для подстановки в шаблон.
        :return: Содержимое файла с замененными ключами.
        """

        # Регулярное выражение для поиска ключей в шаблоне.
        def replace_keys(match):
            """
            Заменяет ключ в шаблоне на соответствующее значение из balance.
            
            :param match: Сопоставление ключа в шаблоне.
            :return: Замененное значение.
            """

            # Разделяем ключ и команду.
            key_command_pair = match.group(1).split(self.key_command_letter)
            
            # Ключ, который необходимо заменить.
            key = key_command_pair[0]
            
            # Проверяем, что ключ существует в balance.
            if key not in balance:
                raise KeyError(f"Key '{key}' not found in balance.")
            
            # Значение для замены ключа.
            insert_balance = balance[key]
            
            # Если указана команда, обрабатываем значение.
            if self.key_command_letter in match.group(1):
                command = key_command_pair[-1]
                if command not in self.key_command_handlers:
                    raise ValueError(f"Key command '{command}' is not supported by Template class. Available only {list(self.key_command_handlers.keys())}")
                
                # Обрабатываем значение в соответствии с командой.
                insert_balance = self.key_command_handlers[command](insert_balance)
            
            # Если необходимо, отрезаем лишние кавычки от строки.
            if self.strip and isinstance(insert_balance, str):
                return insert_balance
            
            # Возвращаем замененное значение.
            return json.dumps(insert_balance)

        # Заменяем ключи в шаблоне на соответствующие значения из balance.
        return re.sub(self.variable_pattern, replace_keys, template_body)

