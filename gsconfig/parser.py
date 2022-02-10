import json
import csv
import ast

# Блок парсера конфигов!
# Перевод из промежуточного формата конфигов в JSON

def define_split_points(string: str, sep, br, raw_pattern):
    """
    Отпределение позиции всех разделяющих строку символов.
    Игнорирует разделители внутри блоков выделенных скобками br.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    br - тип скобок выделяющих подблоки. Пример: br = '{}'

    Генератор. Возвращает индексы разделяющих символов.
    """

    br = {br[0]: 1, br[-1]: -1}
    is_not_raw_block = True
    count = 0

    for i, letter in enumerate(string):
        if letter is raw_pattern:
            is_not_raw_block = not is_not_raw_block

        if letter in br:
            count += br[letter]

        elif letter == sep and count == 0 and is_not_raw_block:
            yield i

    yield len(string)

def split_string_by_sep(string: str, sep, br, raw_pattern):
    """
    Разделение строки на массив подстрок по символу разделителю.
    Не разделяет блоки выделенные скобками.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    br - тип скобок выделяющих подблоки. Пример: br = '{}'

    Генератор. Возвращает подстроки.
    """

    prev = 0
    for i in define_split_points(string, sep, br, raw_pattern):
        yield string[prev:i].strip(sep).strip()
        prev = i

def parse_string(s, to_num=True):
    """
    Пытается перевести строку в число, предварительно определив что это было, int или float
    Переводит true\false в "правильный" формат для JSON
    """

    if s.lower() in ('none', 'nan', 'null'):
        return None

    if s.lower() in ('true', 'false'):
        return s.capitalize()

    if not to_num:
        return s

    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s

def parse_block(string, br, dict_sep, block_sep, to_num, unwrap_list, raw_pattern, is_dict_parse=False):
    """
    Используется внутри функции базовой функции config_to_json.
    Парсит блок (фрагмент исходной строки для разбора) разделенный запятыми.

    string - исходная строка для разбора.

    br - тип скобок выделяющих подблоки. '{}' по умолчанию.
    dict_sep - разделитель ключ\значение элементов словаря. '=' по умолчанию.
    block_sep - разделитель блоков. Синтаксический сахар.

    to_num - нужно ли пытаться преобразовывать значения в числа.
    True (по учаолчанию) пытается преобразовать.

    unwrap_list - нужно ли вытаскивать словари из списков единичной длины.
    False (по умолчанию) вытаскивает из списков все обьекты КРОМЕ словарей.
    True - вынимает из список ВСЕ типы обьектов, включая словари.

    Возвращает список с элементами конфига, обычно это словари.
    """

    out = []
    out_dict = {}

    for line in split_string_by_sep(string, ',', br, raw_pattern):

        # Проверка нужно ли вообще парсить строку
        if line.startswith(raw_pattern):
            out.append(line[1:-1])

        # Проверка наличия блока. Блок всегда начинается с открывающей скобки блока
        elif line.startswith(br[0]):
            # Внутренний блок всегда разворачиваем из лишних списков. Кроме случая когда пришли из разбора словаря.
            # Иначе лезут паразитные вложения.
            unwrap_list = unwrap_list if is_dict_parse else True
            substring = config_to_json(line[1:-1], br, dict_sep, block_sep, to_num, unwrap_list, raw_pattern) or []
            out.append(substring)

        # Проверка на словарь
        elif dict_sep in line:
            key, substring = split_string_by_sep(line, dict_sep, br, raw_pattern)
            out_dict[key] = parse_block(substring, br, dict_sep, block_sep, to_num, unwrap_list, raw_pattern, True)

        # Остались только строки
        else:
            out.append(parse_string(line, to_num))

    if out_dict:
        out.append(out_dict)

    if len(out) == 1:
        return out[0]

    return out


def config_to_json(string, br='{}', dict_sep='=', block_sep='|', to_num=True, unwrap_list=False, raw_pattern='"', is_raw=False):
    """
    Парсит строку конфига и складывает результат в список словарей.
    Исходный формат крайне упрощенная и менее формальная версия JSON.
    Внутри каждого блока может быть призвольное количество подблоков выделенных
    скобками br.

    string - исходная строка для разбора.

    br - тип скобок выделяющих подблоки. '{}' по умолчанию.
    dict_sep - разделитель ключ\значение элементов словаря. '=' по умолчанию.
    block_sep - разделитель блоков. Синтаксический сахар

    to_num - нужно ли пытаться преобразовывать значения в числа.
    True (по учаолчанию) пытается преобразовать.

    unwrap_list - нужно ли вытаскивать словари из списков единичной длины.
    False (по умолчанию) вытаскивает из списков все обьекты КРОМЕ словарей.
    True - вынимает из список ВСЕ типы обьектов, включая словари.

    raw_pattern - символ маркирующий строку которую не нужно разбирать, по умолчанию двойная кавычка '"'
    Строки начинающиеся с символа raw_pattern не парсятся и сохраняются как есть.

    is_raw - указание надо ли парсить строку или нет. False по умаолчанию.
    False (по умолчанию) - парсит строку по всем правилам, с учётом raw_pattern.
    True - не парсит, возвращает как есть.

    Пример: '{i = 4, p = 100, n = name}, {t = 4, e = 100, n = {{m = 4, r = 100}, n = name}}, c = 4'
    Пример: 'value1, value2, value3'

    Возможно использование дополнительного разделителя на блоки (block_sep='|'), в таком случае строка:
    'itemsCount = {count = 3, weight = 65 | count = 4, weight = 35}' будет идентична записи:
    'itemsCount = {{count = 3, weight = 65}, {count = 4, weight = 35}}'
    """

    string = str(string)

    if is_raw:
        return string

    out = []
    for line in split_string_by_sep(string, block_sep, br, raw_pattern):
        out.append(parse_block(line, br, dict_sep, block_sep, to_num, unwrap_list, raw_pattern))

    if len(out) == 1 and (type(out[0]) not in (dict, ) or unwrap_list):
        return out[0]

    return out

if __name__ == '__main__':
    # https://habr.com/post/309242/

    string = [
        'one = two, item = {itemsCount = 4.5, price = 100.123456, name = {name1 = my_name, second = other}}, six = {name3 = my_thirs_name, second = other}, test = {itemsCount = 4, price = 100, name = {{itemsCount = 4, price = 100}, name = {count = 4, total = 10}}}, count = 4, total = 10',
        '9.1, 6.0, 6 | 7 = 7, zero = 0, one, two = {three}, tree = 3 | a, b, f',
        '{9.1, 6.0, 6}, {7 = 7, zero = 0, one, two = {2, dva}, tree = 3}, {a, b, f}',
        'five = {three = 3, two = 2}',
        'life',
        '{life = {TRUE}}',
        '8',
        9999,
        '8 = 8',
        '20:00',
        'connection = {hostname = my.server.host, port = 22, username = user}, command = {stop = sfs2x-service stop, start = sfs2x-service start}, path = /opt/SFS_dev/SFS2X/, health_status_url = https://my.server.host:8444/healthcheck/get',
        'allow = {124588016, -283746251}, superuser = {124588016, 211631602, 106874883, 231976253}',
        'name = {{itemsCount = 4, price = 100}, name = {count = 4, total = FALSE}}',
        'id = act00040, trigger = {and = {eq = {08.04.2019, now} | more = {50, hands} | or = {more = {10, consecutiveDays} | more = {100, gold}}}} | id = act00050, trigger = {and = {more = {50, hands}}}',
        'id = act00040, trigger = {and = {eq = {now = 10.04.2019} | more = {hands = 50} | or = {more = {consecutiveDays = 50} | more = {gold = 100}}}} | id = act00050, trigger = {and = {more = {hands = 50}}}',
        '{life = {}}',
        'a = nan',
        'popup_icon = {left = -1, top = -28}, widget_icon = {{pen, 0, 0, 0}, {sample, 8, 8, 8}, top = 10}, mobile_banner = {title_position = {left = "0x90532022", "oppa", "work!", right = 10, top = 11}}, popup_scheme = "0xFF000000,0xFF000000,0xFF000000,0x30c77263,0xFFf56b45,0xFF152645,0xFFe48f72,0xFF3d407a,0xFF000000"',
        '"payload.cash_delta_ratio", ">=", 10"o"0 | payload.bankroll_delta, ">=", 50000',
        '"<color=#6aefff>{New, new2 = 5} round</color> has | begun"',
        'minSmallBlind = 0, maxSmallBlind = 3, chipsIdList = ChipsSet_01, chipsPrefix = Chips_1_, chipsAmountList = {1, 5, 10, 10, 10, 25, 25, 50, 50, 50} | minSmallBlind = 3, maxSmallBlind = 12.5, chipsIdList = ChipsSet_02, chipsPrefix = Chips_2_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 12.5, maxSmallBlind = 60, chipsIdList = ChipsSet_03, chipsPrefix = Chips_3_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 60, maxSmallBlind = 300, chipsIdList = ChipsSet_04, chipsPrefix = Chips_4_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 300, maxSmallBlind = 1250, chipsIdList = ChipsSet_05, chipsPrefix = Chips_5_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 1250, maxSmallBlind = 6000, chipsIdList = ChipsSet_06, chipsPrefix = Chips_6_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 6000, maxSmallBlind = 30000, chipsIdList = ChipsSet_07, chipsPrefix = Chips_7_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 30000, maxSmallBlind = 125000, chipsIdList = ChipsSet_08, chipsPrefix = Chips_8_, chipsAmountList = {1, 5, 10, 5, 10, 10, 25, 50, 50, 50} | minSmallBlind = 125000, maxSmallBlind = 350000, chipsIdList = ChipsSet_09, chipsPrefix = Chips_9_, chipsAmountList = {1, 5, 10, 1, 1, 5, 5, 10, 25, 50} | minSmallBlind = 750000, maxSmallBlind = 1000000, chipsIdList = ChipsSet_10, chipsPrefix = Chips_10_, chipsAmountList = {1, 5, 10, 5, 5, 10, 25, 50, 50, 50} | minSmallBlind = 1000000, maxSmallBlind = 999999999999, chipsIdList = ChipsSet_11, chipsPrefix = Chips_11_, chipsAmountList = {1, 5, 10, 5, 5, 5, 10, 25, 50, 50}'
        ]

    string_txt = [
        '<color=#6aefff>New round</color> has | begun',
        '{0} made a <color=#B451E9>bet</color> {1}',
        ]

    string_sep = [
        ' hand =   "{three     = 3, two = 2 | four = 5, five = 5}"',
        'hand =    {three     = 3, two             = 2 | four = 5, five = 5}',
        '"<color=#6aefff>New round</color> has | begun"',
        '"{0} made a <color=#B451E9>bet</color> {1}"',
        ]

    for line in string_sep:
        print(json.dumps(config_to_json(line, unwrap_list=False), indent=4))


    # for line in string_txt:
    #     print(json.dumps(config_to_json(line, is_raw=True)))
