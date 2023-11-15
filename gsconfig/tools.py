import json
import csv
import os
import gsparser

from . import classes

def parser_dummy(page_data, **params):
    return page_data

def parser_json(page_data, **params):
    """
    Парсит данные со страницы гуглодоки в формат JSON. См. parser.config_to_json
    Понимает два формата:
        1. Документ в две колонки key \ value
        2. Свободный формат. Первая строка ключи, все остальные строки - значения

    Проверка форматов по очереди, если в первой строке нет ОБОИХ ключей key \ value,
    то считает сободным форматом.

    key - заголовок столбца с ключами для формата в 2 колонки
    value - заголовок столбца с данными
    **params - все параметры доступные для парсера parser.config_to_json
    """

    key = params.get('key', 'key')
    value = params.get('value', 'value')
    key_skip_letters = params.get('key_skip_letters', [])

    headers = page_data[0]
    data = page_data[1:]

    # Если документ из двух колонок.
    # Ключами в столбце key и значением в столбце value
    if key in headers and value in headers:
        key_index = headers.index(key)
        value_index = headers.index(value)

        out = {
            line[key_index]: gsparser.jsonify(line[value_index], **params)
            for line in data if len(line[0]) > 0
        }

        return out

    # Первая строка с заголовками, остальные строки с данными
    out = []
    for values in data:
        bufer = [
            f'{key} = {{{str(value)}}}' for key, value in zip(headers, values)
            if not any([key.startswith(x) for x in key_skip_letters]) and len(key) > 0
        ]
        bufer = gsparser.jsonify(', '.join(bufer), **params)
        out.append(bufer)

    # Оставлено как совместимость с первой версией
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

    if not isinstance(page, classes.Page):
        raise classes.GSConfigError('Object must be of Page type!')

    save_func = save_page_functions.get(page.format, save_csv)
    return save_func(page.get(), page.name, path)

def save_csv(data, title, path):
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
