import json
import csv
import ast
import pickle
import bz2
from memory_profiler import profile

from . import classes

@profile
def backup_config(config, name, path=''):
    backup = {
        'documents': [x.get_raw_data() for x in config.documents],
        'settings': config.settings
        }

    save_zipped_file(f'{path}/{name}', backup)

def save_zipped_file(filename, data):
    with bz2.BZ2File(filename, 'wb') as file:
        pickle.dump(data, file)

@profile
def load_source_from_backup(filename):
    """
    ВАЖНО!
    Возвращает только список исходников (словарей) всех страниц из бекапа.
    Это НЕ обьект конфига!
    """
    with bz2.BZ2File(filename, 'rb') as file:
        data = pickle.load(file)

    return data

@profile
def save_config_documents(config, path=''):
    """
    config -- обьект GameConfig or
    Сохраняет все страницы всех документов в отдельные файлы по указанному пути
    """
    if isinstance(config, classes.GameConfig):
        for document in config:
            for page in document:
                _save_page(page, path)

    elif isinstance(config, classes.Spreadsheet):
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

def str_to_num(s, to_num=True):
    """
    Пытается перевести строку в число, предварительно определив что это было, int или float
    Переводит true\false в "правильный" формат для JSON
    """

    if s.lower() in ("true", "false"):
        s = s.capitalize()

    if not to_num:
        return s

    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s

def define_split_points(string, sep, br):
    """
    Отпределение позиции всех разделяющих строку символов.
    Игнорирует разделители внутри блоков выделенных скобками br.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    br - тип скобок выделяющих подблоки. Пример: br = '{}'

    Генератор. Возвращает индексы разделяющих символов.
    """

    br = {br[0]: 1, br[-1]: -1}
    count = 0

    for i, letter in enumerate(string):
        if letter in br:
            count += br[letter]

        elif letter == sep and count == 0:
            yield i

    yield len(string)

def split_string_by_sep(string, sep, br):
    """
    Разделение строки на массив подстрок по символу разделителю.
    Не разделяет блоки выделенные скобками.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    br - тип скобок выделяющих подблоки. Пример: br = '{}'

    Генератор. Возвращает подстроки.
    """

    prev = 0
    for i in define_split_points(string, sep, br):
        yield string[prev:i].strip(sep).strip()
        prev = i

def parse_block(string, br, to_num, no_list):
    """
    Используется внутри функции базовой функции config_to_json.
    Парсит блок (фрагмент исходной строки для разбора) разделенный только запятыми.

    string - исходная строка для разбора.

    br - тип скобок выделяющих подблоки. '{}' по умолчанию.

    to_num - нужно ли пытаться преобразовывать значения в числа.
    True (по учаолчанию) пытается преобразовать.

    no_list - нужно ли вытаскивать словари из списков единичной длины.
    False (по умолчанию) вытаскивает из списков все обьекты КРОМЕ словарей.
    True - вынимает из список ВСЕ типы обьектов, включая словари.

    Возвращает список с элементами конфига, обычно это словари.
    """

    out_dict = {}
    out = []
    br_left = br[0]

    for line in split_string_by_sep(string, ',', br):
        if line.startswith(br_left):
            substring = config_to_json(line[1:-1], br, to_num, no_list) or []
            if isinstance(substring, list) and len(substring) == 1:
                substring = substring[0]

            out.append(substring)

        elif '=' in line:
            key, substring = split_string_by_sep(line, '=', br)
            if substring.startswith(br_left):
                substring = config_to_json(substring[1:-1], br, to_num, no_list) or []

            else:
                substring = str_to_num(substring, to_num)

            out_dict[key] = substring

        else:
            out.append(str_to_num(line, to_num))

    if out_dict:
        out.append(out_dict)

    if len(out) == 1:
        return out[0]

    return out


def config_to_json(string, br='{}', to_num=True, no_list=False, is_text=False):
    """
    Парсит строку конфига и складывает результат в список словарей.
    Исходный формат крайне упрощенная и менее формальная версия JSON.
    Внутри каждого блока может быть призвольное количество подблоков выделенных
    скобками br.

    string - исходная строка для разбора.

    br - тип скобок выделяющих подблоки. '{}' по умолчанию.

    to_num - нужно ли пытаться преобразовывать значения в числа.
    True (по учаолчанию) пытается преобразовать.

    no_list - нужно ли вытаскивать словари из списков единичной длины.
    False (по умолчанию) вытаскивает из списков все обьекты КРОМЕ словарей.
    True - вынимает из список ВСЕ типы обьектов, включая словари.

    Пример: '{i = 4, p = 100, n = name}, {t = 4, e = 100, n = {{m = 4, r = 100}, n = name}}, c = 4'
    Пример: 'value1, value2, value3'

    Возможно использование дополнительного разделителя '|' на блоки, в таком случае строка:
    'itemsCount = {count = 3, weight = 65 | count = 4, weight = 35}' будет идентична записи:
    'itemsCount = {{count = 3, weight = 65}, {count = 4, weight = 35}}'
    """

    if is_text:
        return string

    string = str(string)
    out = []

    for line in split_string_by_sep(string, '|', br):
        out.append(parse_block(line, br, to_num, no_list))

    if len(out) == 1 and (type(out[0]) not in (dict, ) or no_list):
        return out[0]

    return out

if __name__ == '__main__':
    # https://habr.com/post/309242/

    string = [
        'one = two, item = {itemsCount = 4.5, price = 100.123456, name = {name1 = my_name, second = other}}, six = {name1 = my_name, second = other}, test = {itemsCount = 4, price = 100, name = {{itemsCount = 4, price = 100}, name = {count = 4, total = 10}}}, count = 4, total = 10',
        '9.1, 6.0, 6 | 7 = 7, zero = 0, one, two = {three}, tree = 3 | a, b, f',
        '{9.1, 6.0, 6}, {7 = 7, zero = 0, one, two = {2, dva}, tree = 3}, {a, b, f}',
        'five = {three = 3, two = 2}',
        'life',
        '{life = TRUE}',
        '8',
        '8 = 8',
        '20:00',
        'connection = {hostname = my.server.host, port = 22, username = user}, command = {stop = sfs2x-service stop, start = sfs2x-service start}, path = /opt/SFS_dev/SFS2X/, health_status_url = https://my.server.host:8444/healthcheck/get',
        'allow = {124588016, -283746251}, superuser = {124588016, 211631602, 106874883, 231976253}',
        'name = {{itemsCount = 4, price = 100}, name = {count = 4, total = FALSE}}',
        'id = act00040, trigger = {and = {eq = {08.04.2019, now} | more = {50, hands} | or = {more = {10, consecutiveDays} | more = {100, gold}}}} | id = act00050, trigger = {and = {more = {50, hands}}}',
        'id = act00040, trigger = {and = {eq = {now = 10.04.2019} | more = {hands = 50} | or = {more = {consecutiveDays = 50} | more = {gold = 100}}}} | id = act00050, trigger = {and = {more = {hands = 50}}}',
        '{life = {}}',
        ]

    string_txt = [
        '<color=#6aefff>New round</color> has | begun',
        '{0} made a <color=#B451E9>bet</color> {1}',
        ]

    for line in string:
        print(json.dumps(config_to_json(line), indent=4))

    for line in string_txt:
        print(json.dumps(config_to_json(line, is_text=True)))
