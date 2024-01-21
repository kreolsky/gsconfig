import ast

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

def block_splitter(text, **params):

    br_block = params.get('br_block')
    br_list = params.get('br_list')
    raw_pattern = params.get('raw_pattern')

    br = {
        br_block[0]: 1,
        br_block[1]: -1,
        br_list[0]: 1,
        br_list[1]: -1
    }

    is_not_raw_block = True

    depth = 0
    start = 0
    characters = 0

    for i, char in enumerate(text):
        if (delta := br.get(char)) is not None:
            depth += delta
        elif depth == 0:
            characters += 1

        if (char == "|" and depth == 0) or (characters == 0 and depth == 0) or i == len(text) - 1:
            block = text[start:i + 1].strip().strip(params['sep_block']).strip(params['sep_base']).strip()
            if not block:
                continue
            yield block
            start = i + 1

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
        'always_unwrap': False,
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

    ### always_unwrap
    Нужно ли вытаскивать словари из списков единичной длины.

    False (по умолчанию) - вытаскивает из списков все объекты КРОМЕ словарей.

    True - вынимает из список ВСЕ типы объектов, включая словари. **ВАЖНО!** Настройка игнорирует команды mode = v2, если список можно развернуть, то он обязательно будет развернут!

    Строка: ```'one!list = two, item = {count = 4.5, price = 100, name!list = {name1 = name}}'```

    Результат:
    ```
    {
        "one": "two",
        "item": {
            "count": 4.5,
            "price": 100,
            "name": {
                "name1": "my_name"
            }
        }
    }
    ```
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
            'always_unwrap': False,
            'parser_version': 'v1',
            'is_raw': False
        }
        self.params = {**self.default_params, **(params or {})}
        self.parser = BlockParser(self.params)

    def jsonify(self, string: str, is_raw: bool = None) -> dict:
        """
        Метод переводящий строку конфига в JSON
        - string -- исходная строка для конвертации
        - is_raw -- в случае True строка не будет конвертироваться и возвращается как есть. Когда is_raw не задано, берем значение из настроект обьекта
        """

        # Берем из настроек обьекта если не указано
        if is_raw is None:
            is_raw = self.params['is_raw']

        # Вернуть сырые строки как есть
        if is_raw:
            return string

        # Иногда на вход могут прилететь цифры (int, float, ...)
        string = str(string).strip()

        out = []

        # Оределяем блоки и уже блоки передаем в разработку. 
        # Блок начинается либо со скобки определяющей блок br_block тогда блоки отделяются sep_base
        # Либо наличием символа блока sep_block
        # separator = self.params['sep_block']
        # if string.startswith(self.params['br_block'][0]):
        #     separator = self.params['sep_base']

        for i, block in enumerate(block_splitter(string, **self.params)):
            out.append(self.parser.parse_block(block, self))

        return out[0] if len(out) == 1 else out
