import json
import csv
import ast
import pickle
import bz2

from . import classes

def backup_config(config, name, path=''):
    backup = {
        'documents': [x.get_raw_data() for x in config.documents],
        'settings': config.settings
        }

    save_zipped_file(f'{path}/{name}', backup)

def save_zipped_file(filename, data):
    with bz2.BZ2File(filename, 'wb') as file:
        pickle.dump(data, file)

def load_from_backup(filename):
    """
    ВАЖНО!
    Возвращает только список исходников (словарей) всех страниц из бекапа.
    Это НЕ обьект конфига!
    """
    with bz2.BZ2File(filename, 'rb') as file:
        data = pickle.load(file)

    return data

def save_config(config, path=''):
    """
    config -- обьект GameConfig or
    Сохраняет все страницы всех документов в отдельные файлы по указанному пути
    """
    if isinstance(config, classes.GameConfig):
        for document in config:
            for page in document:
                _save_page(page, path)

    elif isinstance(config, classes.Spreadsheet) or isinstance(config, classes.GameConfigLite):
        for page in config:
            _save_page(page, path)

    else:
        raise classes.GSConfigError('Object must be of GameConfig or Spreadsheet type!')

def _save_page(page, path=''):
    """
    page -- обьект Worksheet
    Сохраняет страницу по указанному пути
    """
    if not isinstance(page, classes.Worksheet):
        raise classes.GSConfigError('Object must be of Worksheet type!')

    return save_page_function[page.type](page.get_page_data(), page.title, path)

def save_as_csv(data, title, path):
    with open(path + title, 'w', encoding='utf-8') as file:
        for line in data:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(line)

def save_as_json(data, title, path):
    title = ''.join(title.split(".")[:-1]) + '.json'

    with open(path + title, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent = 2, ensure_ascii = False)

save_page_function = {'json': save_as_json, 'csv': save_as_csv, 'localization': save_as_json}

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
