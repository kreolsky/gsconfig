import ast


def get_all_brackets(**params):
    """
    Возвращает все используемые в конверторе типы скобок.
    params - параметры с настройками класса конвертора
    """

    brackets = {}
    for key, value in params.items():
        # Все скобки лежат в параметрах начинающихся с br_
        if key.startswith('br_'):
            brackets[value[0]] = 1
            brackets[value[-1]] = -1
    return brackets

def get_all_separators(**params):
    """
    Возвращает все возможные разделители блоков.
    params - параметры с настройками класса конвертора
    """

    separators = [' ', params['sep_block'], params['sep_base']]
    return separators

def strip_all_separators(string, separators):
    """
    Отрезает от строки все символы разделителей
    """

    for sep in separators:
        string = string.strip(sep)
    return string.strip()

def define_split_points(string, sep, **params):
    """
    Определяет точки в которых необходимо разрезать строку.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    params - параметры с настройками класса конвертора
    
    Генератор. Возвращает порядковые номера символов.
    """

    raw_pattern = params.get('raw_pattern')
    br = get_all_brackets(**params)

    is_not_raw_block = True
    br_level = 0

    for i, letter in enumerate(string):
        if letter == raw_pattern:
            is_not_raw_block = not is_not_raw_block

        elif (delta := br.get(letter)) is not None:
            br_level += delta

        elif letter == sep and br_level == 0 and is_not_raw_block:
            yield i

    yield len(string)

def split_string_by_sep(string, sep, **params):
    """
    Разделение строки на массив подстрок по символу разделителю. 
    Не разделяет блоки выделенные скобками.

    string - исходная строка для разбора
    sep - разделитель. Пример: sep = '|'
    params - параметры с настройками класса конвертора

    Генератор. Возвращает подстроки.
    """

    prev = 0
    for i in define_split_points(string, sep, **params):
        yield string[prev:i].strip(sep).strip()
        prev = i

def block_splitter(string, **params):
    """
    Разрезает строку по блокам. Конец блока определяется по:
     - спец. символу окончания блока 
     - изолироваванный самостоятельный блок выделенный {}

    string - исходная строка для разбора
    params - параметры с настройками класса конвертора
    """

    raw_pattern = params.get('raw_pattern')
    br = get_all_brackets(**params)
    separators = get_all_separators(**params)

    is_not_raw_block = True
    is_isolated_block = True
    br_level = 0  # Глубина вложенности
    block_start = 0  # Начало блока

    for i, char in enumerate(string):
        if char == raw_pattern:
            is_not_raw_block = not is_not_raw_block
        
        # Считаем глубину вложенности по скобкам
        elif (delta := br.get(char)) is not None:
            br_level += delta

        # Когда перед блоком что-то есть, то он не самостоятельный и отрезать его ничего не нужно
        elif char not in separators and br_level == 0:
            is_isolated_block = False

        # Нашли символ конец блока (sep_block) и он не внутри других блоков
        end_block_by_sep = char == params['sep_block'] and br_level == 0
        # Блок закончился и он был самостоятельный
        end_isolated_block = is_isolated_block and br_level == 0
        # Конец строки
        string_end = i == len(string) - 1

        # Отправляем найденный блок и разбираем строку дальше
        if (end_block_by_sep or end_isolated_block or string_end) and is_not_raw_block:
            block = strip_all_separators(string[block_start:i + 1], separators)
            # Пробелы в разбираемой строке могут создавать пустые блоки
            if not block:
                continue
            yield block
            block_start = i + 1

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


class BlockParser:
    def __init__(self, params):
        self.params = params
        self.command_handlers = {
            'list': lambda x: [x] if type(x) not in (list, tuple, ) else x,
            'dlist': lambda x: [x] if type(x) in (dict, ) else x,
            'flist': lambda x: [x]
        }
        # Синтаксический сахар для ключей конфига, альтернативный способ указать команду для парсера.
        # Ключ this_is_the_key[] будет идентичен this_is_the_key!dlist
        # Использование '[]' для всех ключей v2 будет эквивалентно использованию converter v1, 
        # Позволяет более гибко искючать словари которые не нуждаются в заворачивании 
        self.short_commands = {
            '[]': 'dlist',  
            '()': 'list',
            '(!)': 'flist'
        }

    def parse_dict(self, line, converter):
        """
        line - фрагмент строки для разбора
        out_dict - итоговый словарь
        converter - обьект ConfigJSONConverter
        """

        # По умолчанием ключ идет без дополнительных команд
        command = None

        key, substring = split_string_by_sep(line, self.params['sep_dict'], **self.params)
        result = converter.jsonify(substring)

        # Обработка команд. Только для v2
        if self.params.get('parser_version') == 'v2':
            # Команда всегда указана через 'sep_func'
            if self.params['sep_func'] in key:
                key, command = key.split(self.params['sep_func'])
            # Обработка коротких команд. Проверям каждый ключ на наличие коротких команд
            # Если найдена, определяем команду и отрезаем от ключа короткую команду
            for item in self.short_commands.keys():
                if key.endswith(item):
                    command = self.short_commands[item]
                    key = key.rstrip(item)
                    break

        # Для v1 словари всегда завернуты в список!
        elif self.params.get('parser_version') == 'v1':
            command = 'dlist'

        if command:
            result = self.command_handlers[command](result)
        
        return {key: result}

    def parse_string(self, line):
        return parse_string(line, self.params['to_num'])

    def parse_block(self, string, converter):
        """
        string - строки для разбора
        converter - обьект ConfigJSONConverter
        """

        out = []
        out_dict = {}

        condition_mapping = {
            lambda line: line.startswith(self.params['raw_pattern']): lambda x: x[1:-1],
            lambda line: line.startswith(self.params['br_block'][0]): lambda x: converter.jsonify(x[1:-1]),
            lambda line: self.params['sep_dict'] in line: lambda x: self.parse_dict(x, converter),
        }

        for line in split_string_by_sep(string, self.params['sep_base'], **self.params):
            for condition, action in condition_mapping.items():
                if condition(line):
                    r = action(line)
                    if isinstance(r, dict):
                        out_dict.update(r)
                    else:
                        out.append(r)
                    break
            else:
                out.append(self.parse_string(line))
        
        if out_dict:
            out.append(out_dict)
        
        return out[0] if len(out) == 1 else out

class ConfigJSONConverter:
    """
    # Конвертор из конфига в JSON
    Разбирает строки конфига и складывает результат в список словарей. 
    Исходный формат крайне упрощенная и менее формальная версия JSON. 
    Внутри каждого блока может быть произвольное количество подблоков выделенных скобками определения блока.

    Пример: ```string = '{i = 4, p = 100}, {t = 4, e = 100, n = {{m = 4, r = 100}, n = name}}'```

    Пример: ```string = 'value1, value2, value3'```

    Параметры умолчанию:
    ```
    params = {
        'br_list': '[]',
        'br_block': '{}',
        'sep_func': '!',
        'sep_block': '|',
        'sep_base': ',',
        'sep_dict': '=',
        'raw_pattern': '"',
        'to_num': True,
        'parser_version': 'v1',
        'is_raw': False
    }
    ```
    Создание класса ```parser = ConfigJSONConverter(params)```

    Основной метод: ```jsonify(string, is_raw=False)```, где 
    - string -- исходная строка для парсинга
    - is_raw -- если True, то строка не будет распарсена

    Пример: ```config_json = parser.jsonify(string)```

    ## Параметры:

    ### parser_version = 'v1'. По умолчанию.
    Все словари всегда будут завернуты в список!

    Строка: ```'one = two, item = {count = 4.5, price = 100, name = {name1 = name}}'```

    Результат:
    ```
    {
        "one": "two",
        "item": [
            {
                "itemsCount": 4.5,
                "price": 100,
                "name": [
                    {
                        "name1": "my_name"
                    }
                ]
            }
        ]
    }
    ```
    ### parser_version = 'v2'
    Разворачивает все списки единичной длины. Для заворачивания необходимо указать в ключе команду 'list'.

    Сама команда (все что после указателя команды) в итоговом JSON будет отрезано. См. символ sep_func

    Строка: ```'one!list = two, item = {count = 4.5, price = 100, name!list = {n = m, l = o}}'```

    Результат:
    ```
    {
        "one": [
            "two"
        ],
        "item": {
            "count": 4.5,
            "price": 100,
            "name": [
                {
                    "n": "m",
                    "l": "o"
                }
            ]
        }
    }
    ```

    #### Команды версии v2

    * list - заворачивает содержимое в список только если это не список
    * flist - всегда заворачивает в дополнительный список, даже списки!
    * dlist - заворачивает только если внутри словарь (dict)

    #### Короткие команды

    Синтаксический сахар для ключей конфига, альтернативный способ указать команду для парсера.
    * [] - dlist
    * () - list
    * (!) - flist

    Ключ this_is_the_key[] будет идентичен this_is_the_key!dlist
    Использование '[]' для всех ключей v2 будет эквивалентно использованию converter v1, 
    Позволяет более гибко искючать словари которые не нуждаются в заворачивании.

    ### br_block
    Тип скобок выделяющих подблоки. '{}' по умолчанию.

    ### br_list
    Тип скобок выделяющих списки. '[]' по умолчанию.

    **ВАЖНО!** Нельзя переопределять значение по умолчанию!

    Внутри допустима любая вложенность, но исключительно в синтаксисе python.

    Нельзя одновременно использовать упрощенный синтаксис и квадратные скобки! Строки обязательно обрамлены кавычками, словари с полным соблюдением синтаксиса!

    Строка: ```['one', ['two', 3, 4], {'one': 'the choose one!'}]```

    Результат:
    ```
    [
        "one",
        [
            "two",
            3,
            4
        ],
        {
            "one": "the choose one!"
        }
    ]
    ```
    Аналогичного результата можно достигнуть и классическим, упрощенным синтаксисом. Строка ```{one, {two, 3, 4}, {one = the choose one!}}``` даст идентичный верхнему результат. Может пригодиться для задания, например, пустых списков или простых конструкций.

    ### sep_base
    Базовый разделитель элементов. ',' - по умолчанию.

    ### sep_dict
    Разделитель ключ-значение элементов словаря. '=' - по умолчанию.

    ### sep_block
    Синтаксический сахар для разделения блоков. '|' - по умолчанию.

    Запись: ```'0, 6| 7 = 7, zr = 0, one, tw = {2 = d}, tv = {2 = dv | 3 = tr} | a, b'```,

    будет идентична: ```'{0, 6}, {7 = 7, zr = 0, one, tw = {2 = d}, tv = {{2 = dv}, {3 = tr}}}, {a, b}'```,

    ### sep_func
    Разделитель указания функций. '!' - по умолчанию.

    Например: key!list означает, что содержимое ключа key обязательно будет списком.

    См. все актуальные доступные команды перечислены в command_handlers класса BlockParser

    ### to_num
    Нужно ли пытаться преобразовывать значения в числа.

    True (по умолчанию) - пытается преобразовать.

    False - не преобразовывать. Числовые значения будут разобраны как строки.

    ### raw_pattern
    Символ маркирующий строку которую не нужно разбирать.

    '"' (двойная кавычка) - по умолчанию. Строка которую не нужно разбирать должна быть обрамлена этим символом с обеих сторон.

    Строки начинающиеся с символа raw_pattern не парсятся и сохраняются как есть.

    ### is_raw
    Указание надо ли парсить строку или нет. False по умолчанию.

    False (по умолчанию) - парсит строку по всем правилам, с учётом raw_pattern.

    True - не парсит, возвращает как есть.
    """

    # Доступные версии парсера
    AVAILABLE_VESRIONS = ('v1', 'v2')

    def __init__(self, params=None):
        self.default_params = {
            'br_list': '[]',
            'br_block': '{}',
            'sep_func': '!',
            'sep_block': '|',
            'sep_base': ',',
            'sep_dict': '=',
            'raw_pattern': '"',
            'to_num': True,
            'parser_version': 'v1',
            'is_raw': False
        }
        self.params = {**self.default_params, **(params or {})}
        self.parser = BlockParser(self.params)

    def jsonify(self, string: str, is_raw: bool = False) -> dict:
        """
        Метод переводящий строку конфига в JSON
        - string -- исходная строка для конвертации
        - is_raw -- в случае True строка не будет конвертироваться и возвращается как есть. Когда is_raw не задано, берем значение из настроект обьекта
        """

        # Вернуть сырые строки как есть без конвертации
        if is_raw or self.params['is_raw']:
            return string

        # Иногда на вход могут прилететь цифры (int, float, ...)
        string = str(string).strip()

        out = []
        # Оределяем блоки и уже блоки передаем в разборку
        # Блок либо выделен br_block тогда блоки отделяются sep_base
        # Либо определяется наличием символа блока sep_block
        for block in block_splitter(string, **self.params):
            out.append(self.parser.parse_block(block, self))
                       
        # Ничего не добавили, нечего и возвращать
        if not out:
            return ''

        # Иначе каждый блок будет завернуть в лишний список
        return out[0] if len(out) == 1 else out
