"""
Template Processing Module for Game Configuration

This module provides a flexible template engine for generating game configuration files.
It supports variable substitution, command processing, and control structures for
dynamic content generation.

Main Components:
    - Constants: Delimiters, special variables, and regex patterns for template parsing
    - Key Command Handlers: Functions that transform values (e.g., !float, !int, !string)
    - Template Command Handlers: Control structures (if, for, foreach, comment)
    - Template Class: Main class for loading, processing, and rendering templates

Usage Example:
    >>> from gsconfig.template import Template
    >>> template = Template(path='config.tpl')
    >>> balance = {'player_name': 'Hero', 'health': 100}
    >>> result = template.render(balance)
    >>> print(result)

Key Features:
    - Variable substitution with command chaining: {% variable!command1!command2 %}
    - Template control structures: if, for, foreach, comment
    - Special loop variables: $item (current element), $i (current index)
    - Extensible command system for custom transformations
    - Support for both string and JSON output formats
"""

import os
import json
import re

from .json_handler import JSONHandler


# --- Constants ---

# Command delimiters and special characters

DEFAULT_COMMAND_LETTER = '!'
"""
Default character used to separate a variable name from its commands.

This character is used to delimit commands in template variables. When a variable
needs to be processed through one or more commands, they are appended to the
variable name using this character.

Example:
    Template: {% player_score!float!int %}
    Here, '!' separates the variable 'player_score' from commands 'float' and 'int'

Usage:
    Can be customized when creating a Template instance, though '!' is the standard
    convention throughout the codebase.
"""

VARIABLE_START = '{%'
"""
Opening delimiter for template variables and commands.

This marker indicates the beginning of a template variable or control structure.
All variables and template commands must be enclosed between VARIABLE_START and
VARIABLE_END delimiters.

Example:
    {% player_name %}
    {% if condition %} content {% endif %}
"""

VARIABLE_END = '%}'
"""
Closing delimiter for template variables and commands.

This marker indicates the end of a template variable or control structure.
It must properly close all VARIABLE_START delimiters.

Example:
    {% player_name %}  - Variable substitution
    {% foreach items %} {{ $item }} {% endforeach %}  - Loop structure
"""

COMMENT_START = '{#'
"""
Opening delimiter for template comments.

This marker indicates the beginning of a comment in the template. Comments are
completely removed during template processing and do not appear in the final output.

Example:
    {# This is a comment that will be removed #}
    {% player_name %}  {# Player's display name #}
"""

COMMENT_END = '#}'
"""
Closing delimiter for template comments.

This marker indicates the end of a comment in the template. All text between
COMMENT_START and COMMENT_END is removed during processing.

Example:
    {# This comment spans multiple lines
       and will be completely removed #}
    {% player_name %}
"""

# Special variables for loops

VAR_ITEM = '$item'
"""
Special variable representing the current item in a foreach loop.

This variable is automatically set to the current element being processed in
a foreach loop. It can be used with commands for transformation.

Example:
    Template: {% foreach items %} value: {% $item!string %}, {% endforeach %}
    Balance: {'items': ['apple', 'banana', 'cherry']}
    Output: value: "apple", value: "banana", value: "cherry"

Note:
    This variable is only valid within the scope of a foreach loop.
"""

VAR_INDEX = '$i'
"""
Special variable representing the current index in a for loop.

This variable is automatically set to the current iteration index (0-based) in
a for loop. It can be used with commands for transformation.

Example:
    Template: {% for count %} iteration: {% $i!int %} {% endfor %}
    Balance: {'count': 3}
    Output: iteration: 0 iteration: 1 iteration: 2

Note:
    This variable is only valid within the scope of a for loop.
"""

# Regex components

RE_COMMAND_NAME = r'[a-zA-Z0-9_]+'
"""
Regular expression pattern for matching valid command names.

This pattern matches one or more alphanumeric characters or underscores, which
constitutes a valid command name in the template system.

Matches:
    - 'float' - Valid command name
    - 'my_command' - Valid command name
    - 'cmd123' - Valid command name

Does not match:
    - 'my-command' - Hyphens are not allowed
    - 'my command' - Spaces are not allowed

Usage:
    Used as a building block in more complex regex patterns for command parsing.
"""

RE_PARAM_VALUE = r'\d+'
"""
Regular expression pattern for matching numeric parameter values.

This pattern matches one or more digits, used for extracting numeric parameters
from commands that require them (e.g., get_0, get_1, get_2).

Matches:
    - '0' - Single digit
    - '123' - Multiple digits

Does not match:
    - '-1' - Negative numbers
    - '1.5' - Decimal numbers
    - 'abc' - Non-numeric values

Usage:
    Used in commands like get_N where N is a numeric index.
"""

# Compiled or raw regex patterns

RE_VARIABLE_PATTERN = r'\{%\s*([a-zA-Z0-9_!]+)\s*%\}'
"""
Regular expression pattern for matching template variables.

This pattern matches template variables enclosed in {% %} delimiters, capturing
the variable name and any commands. The captured group includes the variable name
and optional commands separated by the command letter.

Matches:
    - {% player_name %} - Simple variable
    - {% score!float %} - Variable with command
    - {% data!get_0!string %} - Variable with multiple commands

Captured Group:
    Group 1: The variable name and commands (e.g., 'player_name', 'score!float')

Usage:
    Used to find all variables in a template that need to be replaced with values
    from the balance dictionary.

Example:
    >>> import re
    >>> pattern = re.compile(RE_VARIABLE_PATTERN)
    >>> template = "Name: {% player_name %}, Score: {% score!float %}"
    >>> matches = pattern.findall(template)
    >>> matches
    ['player_name', 'score!float']
"""

RE_COMMENT_PATTERN = r'\{\#\s*(.*?)\s*\#\}\n{0,1}'
"""
Regular expression pattern for matching template comments.

This pattern matches comments enclosed in {# #} delimiters, optionally followed
by a newline character. The captured group contains the comment content.

Matches:
    - {# This is a comment #} - Simple comment
    - {# Multi-line\ncomment #} - Multi-line comment (with DOTALL flag)
    - {# Comment #}\n - Comment with trailing newline

Captured Group:
    Group 1: The comment content without delimiters

Usage:
    Used to remove all comments from the template before processing.

Example:
    >>> import re
    >>> pattern = re.compile(RE_COMMENT_PATTERN, re.DOTALL)
    >>> template = "Name: {% player %} {# Player name #}"
    >>> result = pattern.sub('', template)
    >>> result
    'Name: {% player %} '
"""

RE_TEMPLATE_COMMAND_PATTERN = r'(\{%\s*([\w_]+)\s+([\w_]*)\s*%\}(.*?)\{%\s*end\2\s*%\}\n{0,1})'
"""
Regular expression pattern for matching template control structure commands.

This pattern matches template commands with opening and closing tags, capturing
the command name, parameters, and content. It supports nested command structures.

Matches:
    - {% if condition %} content {% endif %} - Conditional block
    - {% foreach items %} {{ $item }} {% endforeach %} - Loop block
    - {% for count %} iteration {{ $i }} {% endfor %} - Counted loop

Captured Groups:
    Group 1: Full match including opening and closing tags
    Group 2: Command name (e.g., 'if', 'foreach', 'for')
    Group 3: Parameters (e.g., 'condition', 'items', 'count')
    Group 4: Content between opening and closing tags

Usage:
    Used to process template control structures before variable substitution.

Example:
    >>> import re
    >>> pattern = re.compile(RE_TEMPLATE_COMMAND_PATTERN, re.DOTALL)
    >>> template = "{% if show %}Hello{% endif %}"
    >>> matches = pattern.findall(template)
    >>> matches[0][1]  # Command name
    'if'
    >>> matches[0][2]  # Parameters
    'show'
    >>> matches[0][3]  # Content
    'Hello'
"""

RE_KEY_COMMAND_WITH_PARAM = r'_(\d+)'
"""
Regular expression pattern for matching key commands with numeric parameters.

This pattern matches commands that include a numeric parameter, such as get_N
or extract_N, where N is a number.

Matches:
    - '_0' - Parameter value 0
    - '_123' - Parameter value 123

Captured Group:
    Group 1: The numeric parameter value

Usage:
    Used to extract the parameter from commands like get_0, get_1, etc.

Example:
    >>> import re
    >>> pattern = re.compile(RE_KEY_COMMAND_WITH_PARAM)
    >>> command = 'get_2'
    >>> match = pattern.search(command)
    >>> match.group(1)
    '2'
"""

RE_COMMAND_IN_VARIABLE = r'!([a-zA-Z0-9_]+)'
"""
Regular expression pattern for matching commands within a variable expression.

This pattern matches individual commands that are chained to a variable name,
separated by the command letter (!).

Matches:
    - '!float' - Command to convert to float
    - '!string' - Command to wrap in quotes
    - '!get_0' - Command to get element at index 0

Captured Group:
    Group 1: The command name (without the ! prefix)

Usage:
    Used to extract all commands from a variable expression for sequential processing.

Example:
    >>> import re
    >>> pattern = re.compile(RE_COMMAND_IN_VARIABLE)
    >>> variable = 'data!get_0!string'
    >>> commands = pattern.findall(variable)
    >>> commands
    ['get_0', 'string']
"""


# Helper to generate regex for special variables with commands
def get_special_var_with_commands_regex(var_name):
    """
    Generates a regex pattern to match a special variable with one or more commands.
    Example: {% $item!cmd1!cmd2 %}
    """
    return r'\{%\s*' + re.escape(var_name) + r'(!' + RE_COMMAND_NAME + r')+\s*%\}'


"""
Key command handlers
"""

def key_command_extract(array, command):
    """
    extract -- Вытаскивает элемент из списка (list or tuple) если это список единичной длины.

    Пример: По умолчанию парсер v1 не разворачивает словари и они приходят вида [{'a': 1, 'b': 2}],
    если обязательно нужен словарь, то extract развернёт полученный список до {'a': 1, 'b': 2}
    
    ПРИМЕЧАНИЕ: Актуально только для v1. Парсер v2 всегда разворачивает словари по умолчанию
    """
    if len(array) == 1 and isinstance(array, (list, tuple)):
        return array[0]
    return array

def key_command_wrap(array, command):
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

def key_command_list(item, command):
    """
    List -- Если обьект не список, то заворачивает его в список.
    """
    if type(item) not in (list, tuple):
        return [item]
    return item

def key_command_string(string, command):
    """
    string -- Дополнительно заворачивает строку в кавычки. Все прочие типы данных оставляет как есть. Используется
    когда заранее неизвестно будет ли там значение и выбор между null и строкой.
    Например, в новостях мультиивентов поле "sns": {news_sns!string}.

    Пример: Получена строка 'one,two,three', тогда она будет завернута в кавычки и станет '"one,two,three"'.
    """
    if isinstance(string, str):
        return f'"{string}"'
    return string

def key_command_none(element, command):
    """
    Возвращает None если пустой элемент. Иначе входящий элемент без изменения.
    """

    if str(element) == "":
        return None

    return element

def key_command_get_by_index(array, command):
    r"""
    get_(\d+) -- Возвращает элемент из списка по указанному индексу.

    Пример: Получен список [1, 2, 3], команда 'get_1' вернет 2 (элемент под индексом 1)

    :param array: Список, из которого нужно получить элемент.
    :param command: Команда вида 'get_N', где N - индекс элемента.
    :return: Элемент из списка по указанному индексу.
    :raises TypeError: Если array не является списком или кортежем.
    :raises IndexError: Если индекс выходит за пределы списка.
    :raises ValueError: Если команда имеет неверный формат.
    """
    if not isinstance(array, (list, tuple)):
        raise TypeError(f"Переданный объект {array} должен быть списком или кортежем.")

    try:
        idx = int(re.search(RE_KEY_COMMAND_WITH_PARAM, command).group(1))
        if idx >= len(array):
            raise IndexError(f"Индекс {idx} выходит за пределы списка {array}. Всего элементов: {len(array)}")
        return array[idx]
    except AttributeError:
        raise ValueError(f"Неверный формат команды '{command}'. Ожидается формат 'get_N', где N - индекс элемента.")

"""
Template command handlers
"""

def apply_key_commands_to_value(value, commands, key_command_handlers):
    """
    Universal function to apply key commands to a value.
    
    This function applies a list of commands to a value using the provided
    key_command_handlers dictionary.
    
    :param value: The value to process.
    :param commands: List of command strings to apply.
    :param key_command_handlers: Dictionary of key command handlers.
    :return: Processed value after applying all commands.
    """
    if not key_command_handlers:
        return value
    
    result = value
    for command in commands:
        # Find the matching handler for this command
        for cmd_pattern, handler in key_command_handlers.items():
            if re.match(cmd_pattern, command):
                result = handler(result, command)
                break
    return result

def process_special_variable_with_commands(content, variable_name, value, key_command_handlers):
    """
    Universal function to process a special variable with commands in template content.

    This function finds patterns like {% $variable!command %} or {% $variable!command1!command2 %}
    and replaces them with the value after applying the commands.

    :param content: The content to process.
    :param variable_name: Name of the special variable (e.g., '$item', '$i').
    :param value: The value to use for the variable.
    :param key_command_handlers: Dictionary of key command handlers.
    :return: Processed content with the variable patterns replaced.
    """
    if not key_command_handlers:
        # If no handlers, just replace the variable with its value
        return content.replace(variable_name, str(value))

    # 1. Process variables with commands: {% $var!cmd1!cmd2 %}
    pattern = get_special_var_with_commands_regex(variable_name)
    processed_content = content
    for match in re.finditer(pattern, content):
        full_pattern = match.group(0)
        commands = re.findall(RE_COMMAND_IN_VARIABLE, full_pattern)
        processed_value = apply_key_commands_to_value(value, commands, key_command_handlers)
        processed_content = processed_content.replace(full_pattern, str(processed_value))

    # 2. Process simple variable replacements (e.g. inside other tags)
    processed_content = processed_content.replace(variable_name, str(value))

    return processed_content

def template_command_if(params, content, balance, key_command_handlers=None):
    """
    Обрабатывает команду 'if' в шаблоне.

    Команда 'if' позволяет сохранить строку между тегами 'if' и 'endif' если параметр 'params' равен True, иначе удаляет.

    :param params: Ключ, значение которого определяет условие сохранения строки.
    :param content: Содержимое, которое необходимо сохранить или удалить.
    :param balance: Словарь с данными для подстановки в шаблон.
    :param key_command_handlers: Словарь обработчиков команд для ключей (опционально).
    :return: Строка, содержащая сохраненное содержимое если условие True, иначе пустая строка.
    :raises KeyError: Если ключ 'params' не найден в словаре 'balance'.
    """
    return content.lstrip() if balance.get(params) else ''


def template_command_comment(params, content, balance, key_command_handlers=None):
    """
    Обрабатывает команду 'comment' в шаблоне.

    Команда 'comment' позволяет удалить строку между тегами 'comment' и 'endcomment' независимо от значения параметра 'params'.

    :param params: Ключ, значение которого не используется в данной команде.
    :param content: Содержимое, которое необходимо удалить.
    :param balance: Словарь с данными для подстановки в шаблон.
    :param key_command_handlers: Словарь обработчиков команд для ключей (опционально).
    :return: Пустая строка.
    """
    return ''

def remove_trailing_comma(result):
    """
    Удаляет последнюю запятую из строки, если она присутствует.
    
    :param result: Строка, из которой необходимо удалить последнюю запятую.
    :return: Строка без последней запятой.
    """
    if result.strip().endswith('},'):
        return result.strip().strip(",")
    return result

def template_command_foreach(params, content, balance, key_command_handlers=None):
    """
    Обрабатывает команду 'foreach' в шаблоне.

    Команда 'foreach' позволяет повторять содержимое между тегами 'foreach' и 'endforeach' для каждого элемента из списка 'params'.
    Внутри цикла доступна зарезервированная переменная $item, которая принимает значение текущего элемента списка.

    :param params: Ключ, значение которого определяет список элементов для итерации.
    :param content: Содержимое, которое необходимо повторить для каждого элемента списка.
    :param balance: Словарь с данными для подстановки в шаблон.
    :param key_command_handlers: Словарь обработчиков команд для ключей (опционально).
    :return: Строка, содержащая повторенное содержимое для каждого элемента списка.
    :raises KeyError: Если ключ 'params' не найден в словаре 'balance'.
    :raises TypeError: Если значение ключа 'params' не является списком.
    """
    if params not in balance:
        raise KeyError(f'Ключ "{params}" не найден в балансе')

    items = balance[params]
    if not isinstance(items, (list, tuple)):
        raise TypeError(f'Значение для "{params}" должно быть списком')

    result = ''
    for i, item in enumerate(items):
        if isinstance(item, (int, str)):
            # Для строк и целых чисел используем единую функцию обработки
            processed_content = process_special_variable_with_commands(
                content, VAR_ITEM, item, key_command_handlers
            )
        else:
            # Заменяем $item на текущее значение элемента из списка
            # Пример: {% $item!get_0!int %}
            processed_content = content.replace(VAR_ITEM, f'{params}!get_{i}')

        result += processed_content.lstrip()

    # Отрезаем последнюю запятую, если она присутствует
    # Странный костыль для JSON документа, последняя запятая обычно лишняя
    return remove_trailing_comma(result)

def template_command_for(params, content, balance, key_command_handlers=None):
    """
    Обрабатывает команду 'for' в шаблоне.

    Команда 'for' позволяет повторять содержимое между тегами 'for' и 'endfor' заданное количество раз.
    Количество повторений определяется значением ключа 'params' в словаре 'balance'.

    Внутри цикла доступна зарезервированная переменная $i, которая принимает значение текущего индекса итерации.
    Например, если значение ключа 'params' равно 3, то переменная $i будет принимать значения 0, 1 и 2.

    :param params: Ключ, значение которого определяет количество повторений.
    :param content: Содержимое, которое необходимо повторить.
    :param balance: Словарь с данными для подстановки в шаблон.
    :param key_command_handlers: Словарь обработчиков команд для ключей (опционально).
    :return: Строка, содержащая повторенное содержимое.
    :raises KeyError: Если ключ 'params' не найден в словаре 'balance'.
    :raises TypeError: Если значение ключа 'params' не является целым числом.
    """

    # Проверяем, что ключ 'params' существует в словаре 'balance'
    if params not in balance:
        raise KeyError(f'Ключ "{params}" не найден в балансе')

    # Проверяем, что значение ключа 'params' является целым числом
    value = balance[params]
    if not isinstance(value, int):
        raise TypeError(f'Значение для "{params}" должно быть целым числом')

    result = ''
    for i in range(value):
        # Используем единую функцию обработки для $i
        processed_content = process_special_variable_with_commands(
            content, VAR_INDEX, i, key_command_handlers
        )

        # Добавляем обработанное содержимое к результату
        result += processed_content.lstrip()

    # Отрезаем последнюю запятую, если она присутствует
    # Странный костыль для JSON документа, последняя запятая обычно лишняя
    return remove_trailing_comma(result)

"""
Classes
"""

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

    def __init__(self, path='', body='', pattern=None, strip=True, jsonify=False):
        self.path = path
        self.variable_pattern = pattern or RE_VARIABLE_PATTERN
        self.strip = strip
        self.jsonify = jsonify
        self.key_command_letter = DEFAULT_COMMAND_LETTER  # символ отделяющий команду от ключа
        # Create a copy of default handlers to allow per-instance customization
        self.key_command_handlers = self.DEFAULT_KEY_COMMAND_HANDLERS.copy()
        self.template_comment_pattern = RE_COMMENT_PATTERN
        self.template_command_pattern = RE_TEMPLATE_COMMAND_PATTERN
        # Create a copy of default handlers to allow per-instance customization
        self.template_command_handlers = self.DEFAULT_TEMPLATE_COMMAND_HANDLERS.copy()
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
    def register_template_command(cls, name, handler):
        """
        Register a new template command handler at the class level.
        This will affect all new Template instances.

        :param name: Name of the template command (e.g., 'mycommand')
        :param handler: Function that takes (params, content, balance, key_command_handlers=None) and returns processed content
        :return: None
        """
        cls.DEFAULT_TEMPLATE_COMMAND_HANDLERS[name] = handler

    def add_key_command(self, pattern, handler):
        """
        Add a new key command handler to this specific Template instance.
        This does not affect other instances or the class defaults.

        :param pattern: Regex pattern to match the command (e.g., 'mycommand$' or r'mycmd_(\d+)$')
        :param handler: Function that takes (value, command) and returns the processed value
        :return: None
        """
        self.key_command_handlers[pattern] = handler

    def add_template_command(self, name, handler):
        """
        Add a new template command handler to this specific Template instance.
        This does not affect other instances or the class defaults.

        :param name: Name of the template command (e.g., 'mycommand')
        :param handler: Function that takes (params, content, balance, key_command_handlers=None) and returns processed content
        :return: None
        """
        self.template_command_handlers[name] = handler

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
        keep_it [param] -- сохраняет строку если param == true, иначе удаляет
        del_it [param] -- удаляет строку если param == true, иначе сохраняет
        
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
                
                # Recursively process nested commands in content first
                processed_content = self._process_template_commands(content, balance)
                
                # Then process the current command
                # Pass key_command_handlers to all template command handlers for consistency
                processed_content = self.template_command_handlers[command](
                    params, processed_content, balance, self.key_command_handlers
                )
                
                # Replace in template_body
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


