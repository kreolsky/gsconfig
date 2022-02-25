import json
import csv
import ast
import pickle
import bz2
import os

from . import classes

def save_page(page, path=''):
    """
    Сохраняет страницу по указанному пути
    page - обьект Page
    path - путь сохранения обьекта
    """
    if not isinstance(page, classes.Page):
        raise classes.GSConfigError('Object must be of Page type!')

    return save_page_function[page.format](page.get(), page.title, path)

def save_csv(data, title, path):
    if not title.endswith('.csv'):
        title = f'{title}.csv'

    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        for line in data:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(line)

def save_json(data, title, path):
    if not title.endswith('.json'):
        title = f'{title}.json'

    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        json.dump(data, file, indent = 2, ensure_ascii = False)

save_page_function = {
    'json': save_json,
    'csv': save_csv,
    'raw': save_json
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
