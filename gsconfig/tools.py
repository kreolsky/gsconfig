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
    Понимает два формата:
        1. Документ в две колонки key \ value
        2. Свободный формат. Первая строка ключи, все остальные строки - значения

    Проверка форматов по очереди, если в первой строке нет ОБОИХ ключей key \ value,
    то считает сободным форматом.

    key - заголовок столбца ключей для формата в 2 колонки
    value - заголовок столбца данных

    **params - все параметры доступные для парсера parser.jsonify
    """

    key = params.get('key', 'key')
    value = params.get('value', 'value')
    key_skip_letters = params.get('key_skip_letters', [])

    headers = page_data[0]  # Заголовки
    data = page_data[1:]  # Данные

    # Парсер конфигов из гуглодоки в JSON
    parser = gsparser.ConfigJSONConverter(params)

    # Документ из двух колонок
    # Ключи в столбце key и значения в столбце value
    if key in headers and value in headers:
        key_index = headers.index(key)
        value_index = headers.index(value)

        out = {
            line[key_index]: parser.jsonify(line[value_index])
            for line in data if len(line[0]) > 0
        }

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
    
    if not isinstance(type(data), dict):
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


# Блок парсера конфигов!
# Перевод из промежуточного формата конфигов в JSON
def define_split_points(string, sep, **params):
    """
    Define the positions of all separator characters in the string.
    Ignores separators inside blocks enclosed by brackets.

    Args:
        string (str): The original string to be parsed.
        sep (str): The separator. Example: sep = '|'
        params (dict): Additional parameters, including:
            - br_block (str): Brackets for highlighting sub-blocks. Example: br_block = '{}'
            - br_list (str): Brackets for highlighting lists. Example: br_list = '[]'
            - raw_pattern (str): Raw pattern to avoid parsing. Example: raw_pattern = '!'

    Yields:
        int: Indices of separator characters.
    """

    br_block = params.get('br_block')
    br_list = params.get('br_list')
    raw_pattern = params.get('raw_pattern')

    # Brackets are grouped by types.
    # All opening brackets increase the counter, closing brackets decrease it
    br = {
        br_block[0]: 1,
        br_block[1]: -1,
        br_list[0]: 1,
        br_list[1]: -1
    }

    is_not_raw_block = True
    count = 0

    for i, letter in enumerate(string):
        if letter == raw_pattern:
            is_not_raw_block = not is_not_raw_block

        elif (delta := br.get(letter)) is not None:
            count += delta

        elif letter == sep and count == 0 and is_not_raw_block:
            yield i

    yield len(string)

def split_string_by_sep(string, sep, **params):
    """
    Разделение строки на массив подстрок по символу разделителю.
    Не разделяет блоки выделенные скобками.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    br - тип скобок выделяющих подблоки. Пример: br = '{}'

    Генератор. Возвращает подстроки.
    """

    prev = 0
    for i in define_split_points(string, sep, **params):
        yield string[prev:i].strip(sep).strip()
        prev = i

def parse_string(s, to_num=True):
    """
    Пытается перевести строку в число, предварительно определив что это было, int или float
    Переводит true\false в "правильный" формат для JSON
    """

    string_mapping = {
        'none': None,
        'nan': None,
        'null': None,
        'true': True,
        'false': False
    }

    if s.lower() in string_mapping:
        return string_mapping[s.lower()]

    if not to_num:
        return s

    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s
