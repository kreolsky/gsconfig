import json
import csv
import os
import ast

from . import gsconfig
from . import gsparser

def parser_dummy(page_data, **params):
    return page_data

def parser_json(page_data, **params):
    """
    Парсит данные из гуглодоки в формат JSON. См. parser.jsonify
    
    Понимает несколько схем компановки данных. Проверка по очереди:
    1. Указана схема данных (заголовки столбца ключей и данных). См. описание scheme ниже
    2. ДВЕ колонки. В первой строке есть ОБА ключа 'key' и 'value'
    3. Свободный формат, первая строка - ключи, все последуюшие - данные

    Схема в две колонки упрощенная версия формата со схемой. Результатом будет словарь 
    с парами ключ = значение. В случае указания схемы, данные будут дополнительно 
    завернуты в словари с названием столбца данных.
    
    Параметры только для формата в ДВЕ колонки. 
    Можно задать кастомные значения названия полей ключей и данных
        key - заголовок столбца ключей
        value - заголовок столбца данных

    **params - все параметры доступные для парсера parser.jsonify
    """

    key = params.get('key', 'key')
    value = params.get('value', 'value')
    scheme = params.get('scheme')
    key_skip_letters = params.get('key_skip_letters', [])

    headers = page_data[0]  # Заголовки
    data = page_data[1:]  # Данные

    # Парсер конфигов из гуглодоки в JSON
    parser = gsparser.ConfigJSONConverter(params)

    # Документ из произвольного числа колонок
    # Указана схема (scheme) хранения данных
    if scheme:
        key = scheme.get('key', 'key')
        key_index = headers.index(key)
        value_indexes = [headers.index(x) for x in scheme['data']]
        # Первый столбец проходит как дефолтный, 
        # из него брать данные если в других столбцах пусто
        default_value_index = value_indexes[0]

        out = {}
        for value_index in value_indexes:
            bufer = {}
            for line in data:
                # Пропуск пустых строк
                if not line[key_index]:
                    continue

                line_data = line[value_index]
                # Если данные пустые, то брать из дефолтного столбца
                if not line_data:
                    line_data = line[default_value_index]
                
                bufer[line[key_index]] = parser.jsonify(line_data)
            out[headers[value_index]] = bufer

        return out

    # Документ из двух колонок
    # Ключи в столбце 'key' и значения в столбце 'value'
    if key in headers and value in headers:
        key_index = headers.index(key)
        value_index = headers.index(value)

        out = {}
        for line in data:
            # Пропуск пустых строк
            if not line[key_index]:
                continue

            out[line[key_index]] = parser.jsonify(line[value_index])

        return out

    # Обычный документ, данные расположены строками
    # Первая строка с заголовками, остальные строки с данными
    out = []
    for values in data:
        bufer = [
            f'{key} = {{{str(value)}}}' for key, value in zip(headers, values)
            if not any([key.startswith(x) for x in key_skip_letters]) and len(key) > 0
        ]
        bufer = parser.jsonify(', '.join(bufer))
        out.append(bufer)

    # Оставлено для совместимость с первой версией
    # Если в результате только один словарь, он не заворачивается
    if len(out) == 1:
        return out[0]

    return out

def save_page(page, path=''):
    """
    Сохраняет страницу по указанному пути
    page - обьект Page
    path - путь сохранения обьекта
    """

    if not isinstance(page, gsconfig.Page):
        raise gsconfig.GSConfigError('Object must be of Page type!')

    save_func = save_page_functions.get(page.format, save_csv)
    return save_func(page.get(), page.name, path)

def save_csv(data, title, path=''):
    if not title.endswith('.csv'):
        title = f'{title}.csv'

    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        for line in data:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(line)

def save_json(data, title, path=''):
    if not title.endswith('.json'):
        title = f'{title}.json'
    
    if isinstance(data, str):
        data = json.loads(data)

    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def save_raw(data, title, path=''):
    with open(os.path.join(path, title), 'w') as file:
        file.write(data)

save_page_functions = {
    'json': save_json,
}

def dict_to_str(source, tab='', count=0):
    output = ''

    if not isinstance(source, dict):
        return source

    for key, value in source.items():
        end = ''
        if isinstance(value, dict):
            count += 1
            value = dict_to_str(value, ' ' * 4, count)
            end = '\n'
            count -= 1

        output += f'{tab * count}{str(key)}: {end}{str(value)}\n'

    return output[:-1]


"""
Template command handlers
"""

def command_extract(array):
    """
    extract -- Вытаскивает элемент из списка (list or tuple) если это список единичной длины.

    Пример: По умолчанию парсер не разворачивает словари и они приходят вида [{'a': 1, 'b': 2}],
    если обязательно нужен словарь, то extract развернёт полученный список до {'a': 1, 'b': 2}
    """
    if len(array) == 1 and type(array) in (list, tuple):
        return array[0]
    return array

def command_wrap(array):
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

def command_string(arg):
    """
    string -- Дополнительно заворачивает строку в кавычки. Все прочие типы данных оставляет как есть. Используется
    когда заранее неизвестно будет ли там значение и выбор между null и строкой.
    Например, в новостях мультиивентов поле "sns": {news_sns!string}.

    Пример: Получена строка 'one,two,three', тогда она будет завернута в кавычки и станет '"one,two,three"'.
    """

    if type(arg) is str:
        return f'"{arg}"'
    return arg