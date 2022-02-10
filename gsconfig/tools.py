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

    return save_page_function[page.type](page.get(), page.title, path)

def save_as_csv(data, title, path):
    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        for line in data:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(line)

def save_as_json(data, title, path):
    title = ''.join(title.split(".")[:-1]) + '.json'

    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        json.dump(data, file, indent = 2, ensure_ascii = False)

save_page_function = {
    'json': save_as_json,
    'csv': save_as_csv,
    'raw': save_as_json
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
