import json
import csv
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from . import gsconfig
from . import gsparser

def get_google_client(json_keyfile):
    """
    Коннект к гуглотабличкам. См подробности в офф доке gspread

    https://github.com/burnash/gspread
    http://gspread.readthedocs.io/en/latest/
    """

    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)

    return gspread.authorize(credentials)


def save_page(page, path=''):
    """
    Сохраняет страницу по указанному пути
    page - обьект Page
    path - путь сохранения обьекта
    """

    if not isinstance(page, gsconfig.Page):
        raise gsconfig.GSConfigError('Object must be of Page type!')

    save_func = save_page_functions.get(page.format, save_raw)
    return save_func(page.get(), page.name, path)

def check_folder_exists(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def convert_to_dict(data):
    if isinstance(data, str):
        return json.loads(data)
    else:
        return data

def add_extension(filename, extension):
    if not filename.lower().endswith(f'.{extension}'):
        return f'{filename}.{extension}'
    else:
        return filename

def save_csv(data, title, path=''):
    title = add_extension(title, 'csv')

    check_folder_exists(path)
    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        for line in data:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(line)

def save_json(data, title, path=''):
    title = add_extension(title, 'json')
    data = convert_to_dict(data)
    
    check_folder_exists(path)
    with open(os.path.join(path, title), 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def save_raw(data, title, path=''):
    check_folder_exists(path)
    with open(os.path.join(path, title), 'w') as file:
        file.write(data)

save_page_functions = {
    'json': save_json,
    'raw': save_raw,
    'csv': save_csv
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
