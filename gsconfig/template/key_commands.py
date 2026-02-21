"""
Key command handlers
"""

import re
from .constants import (
    RE_KEY_COMMAND_WITH_PARAM,
)


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
