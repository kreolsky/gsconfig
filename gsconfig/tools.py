import json
import csv
import os

from . import gsconfig
from .json_handler import JSONHandler


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
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        for line in data:
            writer.writerow(line)

def save_json(data, title, path=''):
    title = add_extension(title, 'json')
    data = convert_to_dict(data)
    JSONHandler.save(data, title, path)

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
    if not isinstance(source, dict):
        return source

    parts = []
    for key, value in source.items():
        if isinstance(value, dict):
            value = dict_to_str(value, ' ' * 4, count + 1)
            parts.append(f'{tab * count}{str(key)}: \n{str(value)}\n')
        else:
            parts.append(f'{tab * count}{str(key)}: {str(value)}\n')

    return ''.join(parts)[:-1]

def load_json(filename, path=''):
    file_path = os.path.join(path, filename)

    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
        
        return json_data
    except IOError as err:
        raise IOError(f"Error reading the file: {err}") from err
    except ValueError:
        raise ValueError("The file does not contain valid JSON.") from None
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e