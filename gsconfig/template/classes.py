"""
Classes
"""

import os
import json
import re

from .constants import (
    DEFAULT_COMMAND_LETTER,
    RE_VARIABLE_PATTERN,
    RE_COMMENT_PATTERN,
    RE_TEMPLATE_COMMAND_PATTERN,
    RE_PARAM_VALUE
)
from .key_commands import (
    key_command_extract,
    key_command_wrap,
    key_command_list,
    key_command_string,
    key_command_none,
    key_command_get_by_index,
)
from .template_commands import (
    template_command_if,
    template_command_comment,
    template_command_foreach,
    template_command_for,
)
from ..json_handler import JSONHandler


class Template(object):
    r"""
    Класс шаблона из которого будет генериться конфиг.
    Паттерн ключа и символ отделяющий команду можно переопределить.

    path -- путь для файла шаблона

    body -- можно задать шаблон как строку

    variable_pattern -- паттерн определения ключей (переменных) в шаблоне. r'\{%\s*([a-z0-9_!]+)\s*%\}' - по умолчанию. Пример: {% variable %}

    command_letter -- символ отделяющий команду от ключа. '!' - по умолчанию
    
    jsonify  -- Отдавать результат как словарь. False - по умолчанию (отдает как строку)

    strip -- Будет ли отрезать от строк лишние кавычки. 
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
    dummy -- Пустышка, ничего не делает.

    float -- Переводит значение в число с плавающей запятой.
    Пример: Получено число 10, в шаблон оно будет записано как 10.0

    int -- Переводит значение в целое число, отбрасывая дробную часть.
    Пример: Получено число 10.9, в шаблон оно будет записано как 10

    json -- Сохраняет структуру как JSON (применяет json.dumps())

    list -- Заворачивает в список если это еще не список

    extract -- Вытаскивает элемент из списка (list или tuple) если это список единичной длины.
    Пример: По умолчанию парсер не разворачивает словари и они приходят вида [{'a': 1, 'b': 2}],
    если обязательно нужен словарь, то extract развернёт полученный список до {'a': 1, 'b': 2}

    wrap -- Дополнительно заворачивает полученный список если первый элемент этого списка не является списком.
    Пример: Получен список [1, 2, 4], 1 - первый элемент, не список, тогда он дополнительно будет завернут [[1, 2, 4]].

    string -- Дополнительно заворачивает строку в кавычки. Все прочие типы данных оставляет как есть. 
    Используется когда заранее неизвестно будет ли там значение и выбор между null и строкой.
    Например, в новостях мультиивентов поле "sns": {news_sns!string}.
    Пример: Получена строка 'one,two,three', тогда она будет завернута в кавычки и станет '"one,two,three"'.

    get_N -- Берет элемент с индексом N из списка.
    Пример: Получен список (допустимы только списки и кортежи) ['Zero', 'One', 'Two'] и команда get_2
    Тогда будет подставлено значение  'Two'


    КОМАНДЫ УПРАВЛЕНИЯ СТРОКАМИ ШАБЛОНА:
    if -- Обрабатывает команду 'if' в шаблоне. Команда 'if' позволяет сохранить строку между тегами 'if' и 'endif' если параметр 'params' равен True, иначе удаляет.
    Шаблон: {% if cargo_9 %} строка {% endif %}
    Баланс: {'cargo_9': True}

    comment -- Обрабатывает команду 'comment' в шаблоне. Команда 'comment' позволяет удалить строку между тегами 'comment' и 'endcomment' независимо от значения параметра 'params'.
    Шаблон: {% comment %} строка {% endcomment %}

    foreach -- Обрабатывает команду 'foreach' в шаблоне. Команда 'foreach' позволяет повторять содержимое между тегами 'foreach' и 'endforeach' для каждого элемента из списка 'params'.
    Внутри цикла доступна зарезервированная переменная $item, которая принимает значение текущего элемента списка.
    Шаблон: {% foreach cargo_9 %} элемент: $item {% endforeach %}
    Баланс: {'cargo_9': ['item1', 'item2', 'item3']}

    for -- Обрабатывает команду 'for' в шаблоне. Команда 'for' позволяет повторять содержимое между тегами 'for' и 'endfor' заданное количество раз.
    Количество повторений определяется значением ключа 'params' в словаре 'balance'.
    Внутри цикла доступна зарезервированная переменная $i, которая принимает значение текущего индекса итерации.
    Шаблон: {% for cargo_9 %} индекс: $i {% endfor %}
    Баланс: {'cargo_9': 3}

    КОММЕНТАРИИ:
    {# Я комментарий в теле шаблона #}
    """

    # Default key command handlers - single source of truth
    DEFAULT_KEY_COMMAND_HANDLERS = {
        'dummy$': lambda x, command: x,
        'float$': lambda x, command: float(x),
        'int$': lambda x, command: int(x),
        'json$': lambda x, command: json.dumps(x),
        'string$': key_command_string,
        'extract$': key_command_extract,
        'wrap$': key_command_wrap,
        'list$': key_command_list,
        'none$': key_command_none,
        'null$': key_command_none,
        r'get_' + RE_PARAM_VALUE + r'$': key_command_get_by_index,
        r'extract_' + RE_PARAM_VALUE + r'$': key_command_get_by_index
    }

    # Default template command handlers - single source of truth
    DEFAULT_TEMPLATE_COMMAND_HANDLERS = {
        'if': template_command_if,
        'comment': template_command_comment,
        'foreach': template_command_foreach,
        'for': template_command_for
    }

    """
    Метаданные для управления рекурсивной обработкой команд шаблона
    pre_process: выполнять рекурсивную обработку содержимого ДО вызова обработчика
    post_process: выполнять рекурсивную обработку содержимого ПОСЛЕ вызова обработчика
    
    Подробное объяснение логики для каждой команды:
    
    1. if (pre_process: False, post_process: True)
       Логика: Ленивая оптимизация. Содержимое обрабатывается только если условие истинно.
       - pre_process=False: Не тратим ресурсы на обработку, если блок будет удален.
       - post_process=True: Если условие истинно, рекурсивно обрабатываем вложенные команды.
       Пример: {% if show_details %} {% foreach items %} $item {% endforeach %} {% endif %}
       Если show_details=False, foreach вообще не будет обрабатываться.
    
    2. comment (pre_process: False, post_process: False)
       Логика: Полное игнорирование содержимого для максимальной производительности.
       - pre_process=False: Нет смысла анализировать содержимое комментария.
       - post_process=False: Обработчик возвращает пустую строку, обрабатывать нечего.
       Пример: {% comment %} {% foreach items %} $item {% endforeach %} {% endcomment %}
       Всё содержимое удаляется без анализа.
    
    3. foreach (pre_process: False, post_process: False)
       Логика: Избежание ошибок и переполнения стека при больших списках.
       - pre_process=False: Переменная $item еще не заменена, обработка вызовет KeyError.
       - post_process=False: Развернутый блок может быть огромным, глубокая рекурсия опасна.
                          Вложенные команды будут найдены на следующей итерации внешнего while.
       Пример: {% foreach items %} {% if $item.visible %} $item.name {% endif %} {% endforeach %}
       Сначала foreach развернет блок, затем внешний цикл найдет и обработает if.
    
    4. for (pre_process: False, post_process: False)
       Логика: Аналогично foreach - избежание ошибок с переменной $i и переполнения стека.
       - pre_process=False: Переменная $i еще не заменена.
       - post_process=False: Безопасная итеративная обработка вместо глубокой рекурсии.
    """
    
    DEFAULT_TEMPLATE_COMMAND_METADATA = {
        # Настройки по умолчанию для всех новых команд, если не указаны метаданные явно.
        # Используется в register_template_command() и add_template_command() когда metadata=None.
        # Логика: pre_process=False (не обрабатываем содержимое до handler),
        #         post_process=True (обрабатываем результат после handler).
        # Это поведение по умолчанию подходит для большинства команд, которые
        # трансформируют содержимое, но не удаляют его полностью.
        '_default': {'pre_process': False, 'post_process': True},
        
        'if': {'pre_process': False, 'post_process': True},
        'comment': {'pre_process': False, 'post_process': False},
        'foreach': {'pre_process': False, 'post_process': False},
        'for': {'pre_process': False, 'post_process': False}
    }

    def __init__(self, path='', body='', pattern=None, strip=True, jsonify=False):
        self.path = path
        self.variable_pattern = pattern or RE_VARIABLE_PATTERN
        self.strip = strip
        self.jsonify = jsonify
        self.key_command_letter = DEFAULT_COMMAND_LETTER  # символ отделяющий команду от ключа
        # Используем константы класса как базу для per-instance настройки
        self.key_command_handlers = self.DEFAULT_KEY_COMMAND_HANDLERS
        self.template_comment_pattern = RE_COMMENT_PATTERN
        self.template_command_pattern = RE_TEMPLATE_COMMAND_PATTERN
        self.template_command_handlers = self.DEFAULT_TEMPLATE_COMMAND_HANDLERS
        self.template_command_metadata = self.DEFAULT_TEMPLATE_COMMAND_METADATA
        self._body = body
        self._keys = []

    @classmethod
    def register_key_command(cls, pattern, handler):
        """
        Register a new key command handler at the class level.
        This will affect all new Template instances.

        :param pattern: Regex pattern to match the command (e.g., 'mycommand$' or r'mycmd_(\d+)$')
        :param handler: Function that takes (value, command) and returns the processed value
        :return: None
        """
        cls.DEFAULT_KEY_COMMAND_HANDLERS[pattern] = handler

    @classmethod
    def register_template_command(cls, name, handler, metadata=None):
        """
        Register a new template command handler at the class level.
        This will affect all new Template instances.

        :param name: Name of the template command (e.g., 'mycommand')
        :param handler: Function that takes (params, content, balance, key_command_handlers=None) and returns processed content
        :param metadata: Optional dict with 'pre_process' and 'post_process' keys.
                         If None, uses DEFAULT_TEMPLATE_COMMAND_METADATA['_default']
        :return: None
        """
        cls.DEFAULT_TEMPLATE_COMMAND_HANDLERS[name] = handler
        if metadata is None:
            # Use default metadata from the '_default' section
            metadata = cls.DEFAULT_TEMPLATE_COMMAND_METADATA['_default'].copy()
        cls.DEFAULT_TEMPLATE_COMMAND_METADATA[name] = metadata

    def add_key_command(self, pattern, handler):
        """
        Add a new key command handler to this specific Template instance.
        This does not affect other instances or the class defaults.

        :param pattern: Regex pattern to match the command (e.g., 'mycommand$' or r'mycmd_(\d+)$')
        :param handler: Function that takes (value, command) and returns the processed value
        :return: None
        """
        self.key_command_handlers[pattern] = handler

    def add_template_command(self, name, handler, metadata=None):
        """
        Add a new template command handler to this specific Template instance.
        This does not affect other instances or the class defaults.

        :param name: Name of the template command (e.g., 'mycommand')
        :param handler: Function that takes (params, content, balance, key_command_handlers=None) and returns processed content
        :param metadata: Optional dict with 'pre_process' and 'post_process' keys.
                         If None, uses DEFAULT_TEMPLATE_COMMAND_METADATA['_default']
        :return: None
        """
        self.template_command_handlers[name] = handler
        if metadata is None:
            # Use default metadata from the '_default' section
            metadata = self.DEFAULT_TEMPLATE_COMMAND_METADATA['_default'].copy()
        self.template_command_metadata[name] = metadata

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
        template_body = self._process_template_comments(self.body)

        # Управление строками, обработка команд управления строками (strings_command_handlers)
        template_body = self._process_template_commands(template_body, balance)
        
        # Заполнение шаблона данными
        # Заменяем ключи в шаблоне на соответствующие значения из balance
        out = self._process_key_commands(template_body, balance)
        
        # Преобразуем результат в JSON, если необходимо
        if self.jsonify:
            try:
                out = json.loads(out)
            except json.JSONDecodeError as e:
                raise ValueError(f"\nError during jsonify in {self.title}\n{str(e)}\n{out}")

        return out
    
    def save(self, balance: dict, file_name: str, path: str = ''):
        """
        Сохраняет сгенерированный конфиг в JSON.

        :param balance: Словарь с данными для подстановки в шаблон.
        :param file_name: Имя файла для сохранения конфига.
        :param path: Путь к директории для сохранения (по умолчанию текущая директория).
        :return: Сгенерированный конфиг (словарь или строка в зависимости от jsonify).
        """   
     
        config = self.render(balance)
        JSONHandler.save(config, file_name, path)

        return config

    # Алиас для метода render для обеспечения обратно совместимости
    make = render

    def _process_template_comments(self, template_body):
        """
        Удаление комментариев из шаблона.
        
        :param template_body: Содержимое файла.
        :return: Содержимое файла без комментариев.
        """
        # Регулярное выражение для поиска комментариев в шаблоне
        comment_pattern = re.compile(self.template_comment_pattern, re.DOTALL)
        
        # Удаляем все комментарии из шаблона
        template_body = comment_pattern.sub('', template_body)
        
        return template_body

    def _process_template_commands(self, template_body, balance):
        """
        Управление строками, обработка команд управления строками (strings_command_handlers)
        
        Доступные команды:
        - if [param] -- сохраняет содержимое если param == true, иначе удаляет
        - comment -- удаляет содержимое независимо от значения параметра
        - foreach [param] -- повторяет содержимое для каждого элемента из списка
        - for [param] -- повторяет содержимое заданное количество раз
        
        Архитектура: Engine-driven recursion with minimal handlers
        - Handlers are minimal and only transform content
        - Engine controls all recursion based on command metadata
        - Metadata defines pre-processing and post-processing behavior
        
        Логика работы механизма pre_process и post_process:
        ---------------------------------------------------------
        Метод работает в цикле while True, пока в тексте шаблона находятся команды.
        Для каждой найденной команды выполняется следующая последовательность:
        
        1. Извлечение метаданных (pre_process, post_process) из template_command_metadata
        2. Pre-processing (если True): Рекурсивный вызов для обработки содержимого ДО handler
           - Используется редко, когда handler должен видеть уже обработанное содержимое
        3. Вызов Handler: Трансформация содержимого (например, удаление или тиражирование)
        4. Post-processing (если True): Рекурсивный вызов для обработки результата ПОСЛЕ handler
           - Используется для "прозрачных" команд (if), которые оставляют содержимое
        5. Замена блока в шаблоне на результат
        
        Важные особенности:
        - Циклы (foreach, for) используют False/False для избежания ошибок с переменными ($item, $i)
          и переполнения стека при больших списках. Вложенные команды обрабатываются на следующей
          итерации внешнего цикла while.
        - Условия (if) используют False/True для ленивой оптимизации - не тратим ресурсы на
          обработку содержимого, которое будет удалено.
        - Комментарии (comment) используют False/False для максимальной производительности.
        
        :param template_body: Содержимое файла.
        :param balance: Словарь с данными для подстановки в шаблон.
        :return: Обработанное содержимое файла.
        """

        # Регулярное выражение для поиска строковых команд в шаблоне
        template_command_pattern = re.compile(self.template_command_pattern, re.DOTALL)
        
        # Keep processing until no more commands are found
        while True:
            # Находим все строки, содержащие команды
            matches = template_command_pattern.findall(template_body)
            if not matches:
                break
            
            # Обрабатываем каждую строку.
            for match in matches:
                full_match, command, params, content = match
                
                # Проверяем, что команда поддерживается
                if command not in self.template_command_handlers:
                    available_commands = list(self.template_command_handlers.keys())
                    raise ValueError(f"Template command '{command}' is not supported. Available only {available_commands}")
                
                # Получаем метаданные для этой команды
                metadata = self.template_command_metadata[command]
                
                # Pre-processing: рекурсивно обрабатываем содержимое ДО вызова обработчика
                if metadata.get('pre_process', False):
                    content = self._process_template_commands(content, balance)
                
                # Вызываем обработчик команды с (возможно предварительно обработанным) содержимым
                # Обработчики минимальны - они только трансформируют содержимое
                processed_content = self.template_command_handlers[command](
                    params, content, balance, self.key_command_handlers
                )
                
                # Post-processing: рекурсивно обрабатываем содержимое ПОСЛЕ вызова обработчика
                if metadata.get('post_process', True):
                    processed_content = self._process_template_commands(processed_content, balance)
                
                # Заменяем в template_body
                template_body = template_body.replace(full_match, processed_content)
        
        return template_body

    def _process_key_commands_pipeline(self, value_by_key, key_commands):
        """
        Конвеерная обработка команд для значения ключа.
        
        :param value: Значение ключа.
        :param key_commands: Список команд, которые необходимо применить к значению ключа.
        :return: Обработанное значение ключа.
        """

        # Конвеерная обработка команд
        for command in key_commands:
            # Перебираем совпадения команд в key_command_handlers регулярным выражением
            # Это позволяет передавать параметр в команде
            for cmd, handler in self.key_command_handlers.items():
                if re.match(cmd, command):
                    value_by_key = handler(value_by_key, command)
                    break
            else:
                available_commands = list(self.key_command_handlers.keys())
                raise ValueError(f"Key command '{command}' is not supported. Available only {available_commands}")
        
        # Если необходимо, отрезаем лишние кавычки от строки
        if self.strip and isinstance(value_by_key, str):
            return value_by_key
        
        # Возвращаем замененное значение
        return json.dumps(value_by_key)

    def _process_key_commands(self, template_body, balance):
        """
        Заполнение шаблона данными. Заменяет ключи в шаблоне на соответствующие значения из balance.

        :param template_body: Содержимое файла.
        :param balance: Словарь с данными для подстановки в шаблон.
        :return: Содержимое файла с замененными ключами.
        """

        # Регулярное выражение для поиска ключей в шаблоне
        def replace_keys(match):
            """
            Заменяет ключ в шаблоне на соответствующее значение из balance.

            :param match: Сопоставление ключа в шаблоне.
            :return: Замененное значение.
            """

            # Группа из ключа и списка команд которые к нему необходимо применить
            key_commands_group = match.group(1).split(DEFAULT_COMMAND_LETTER)

            # Ключ, который необходимо заменить
            key = key_commands_group[0]
            if key not in balance:
                raise KeyError(f"Key '{key}' not found in balance.")

            value_by_key = balance[key]
            key_commands = key_commands_group[1:]

            # Обрабатываем команды для значения ключа
            return self._process_key_commands_pipeline(value_by_key, key_commands)

        # Заменяем ключи в шаблоне на соответствующие значения из balance
        return re.sub(self.variable_pattern, replace_keys, template_body)
