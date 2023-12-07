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
            'dummy': lambda x: x,
            'list': lambda x: [x] if type(x) not in (list, tuple,) else x,
            'flist': lambda x: [x]
        }

    def parse_raw(self, line):
        return line[1:-1]

    def parse_nested_block(self, line, converter):
        return converter.jsonify(line[1:-1], _unwrap_it=True)

    def parse_dict(self, line, out_dict, converter):
        """
        line - фрагмент строки для разбора
        out_dict - итоговый словарь
        converter - обьект ConfigJSONConverter
        """

        # Всегда разворачиваем для версии v2
        # Потом проверяем какие команды необходимо применить
        unwrap_it = self.params.get('parser_version') == 'v2'
        # Пустышка по умолчанию, не делать ничего
        command = 'dummy'

        key, substring = split_string_by_sep(line, self.params['sep_dict'], **self.params)
        result = converter.jsonify(substring, _unwrap_it=unwrap_it)

        # Команда всегда указана через 'sep_func'
        if unwrap_it and self.params['sep_func'] in key:
            key, command = key.split(self.params['sep_func'])
        out_dict[key] = self.command_handlers[command](result)

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
            lambda line: line.startswith(self.params['raw_pattern']): self.parse_raw,
            lambda line: line.startswith(self.params['br_block'][0]): lambda x: self.parse_nested_block(x, converter),
            lambda line: self.params['sep_dict'] in line: lambda x: self.parse_dict(x, out_dict, converter),
        }

        for line in split_string_by_sep(string, self.params['sep_base'], **self.params):
            for condition, action in condition_mapping.items():
                if condition(line):
                    result = action(line)
                    if result is not None:
                        out.append(result)
                    break
            else:
                out.append(self.parse_string(line))

        if out_dict:
            out.append(out_dict)

        return out[0] if len(out) == 1 else out

class ConfigJSONConverter:
    """
    # Парсер из конфига в JSON
    Класс парсинга строк конфига и складывает результат в список словарей. Исходный формат крайне упрощенная и менее формальная версия JSON. Внутри каждого блока может быть произвольное количество подблоков выделенных скобками определения блока.

    Пример: ```string = '{i = 4, p = 100}, {t = 4, e = 100, n = {{m = 4, r = 100}, n = name}}'```

    Пример: ```string = 'value1, value2, value3'```

    Параметры умолчанию:
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
    Создание класса ```parser = ConfigJSONConverter(params)```

    Основной метод: ```jsonify(string, is_raw=False)```, где 
    * string - исходная строка для парсинга
    * is_raw - если True, то строка не будет распарсена

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

    Строка: ```'one!list = two, item = {сount = 4.5, price = 100, name!list = {n = m, l = o}}'```

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

    ### _unwrap_it
    **ВАЖНО!** Служебный параметр, указание нужно ли разворачивать получившуюся после парсинга структуру. Определяется автоматически.

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
    AVAILABLE_PARSER_VESRION = ('v1', 'v2')

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

    def jsonify(self, string: str, is_raw: bool = None, _unwrap_it: bool = None) -> dict:
        # Когда is_raw не задано, берем значение из настроект обьекта
        if is_raw is None:
            is_raw = self.params['is_raw']

        # Для сырых строк возвращаем без изменений
        # Необходимо когда мешанина из разных типов строк
        # Пожалуй, это плохое решение
        if is_raw:
            return string

        string = str(string)

        # Да, всегда True. Была идея что для разных версий могут быть разные условия
        if _unwrap_it is None:
            _unwrap_it = {'v1': True, 'v2': True}[self.params['parser_version']]

        out = []
        for line in split_string_by_sep(string, self.params['sep_block'], **self.params):
            out.append(self.parser.parse_block(line, self))

        """
        Проверяем что нужно разворачивать в зависимости от того, какие
        элементы структуры разбираем. Значения внутри словарей зависит от режима и версии

        v1. Всё, кроме словарей, разворачиваем по умолчанию
        v2. Всегда разворачиваем. Дополнительные действия зависят от команды в ключе
        См. parser.parse_block() для деталей
        """
        unwrap_v1 = self.params['parser_version'] == 'v1' and (type(out[0]) not in (dict, ) or _unwrap_it)
        unwrap_v2 = self.params['parser_version'] == 'v2' and _unwrap_it
        if len(out) == 1 and (self.params['always_unwrap'] or unwrap_v1 or unwrap_v2):
            return out[0]

        """
        КОСТЫЛЬ! Последствия того, что перед парсингом в gsconfig всё заворачивается
        в скобки блока и на выход попадают массивы с пустой строкой - [""]
        """
        if isinstance(out, list) and out[0] == '':
            return []

        return out
