"""
Template command handlers
"""

import re
from .constants import (
    RE_COMMAND_IN_VARIABLE,
    VAR_ITEM,
    VAR_INDEX,
    get_special_var_with_commands_regex,
    remove_trailing_comma
)


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
