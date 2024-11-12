from . import gsparser

class Extractor:
    """
    Класс для извлечения и парсинга данных из страниц гугл-таблиц.
    """

    def __init__(self):
        # Набор экстракторов
        self.extractors = {
            'json': self._extract_json,
            'csv': self._extract_dummy,  # Пример для csv, можно заменить на реальный парсер
            'raw': self._extract_dummy
            }

        # Данные из парсера, необходимы для корректной обработки команд в ключах
        self._parser_sep = ''
        self._parser_br_open = ''
        self._parser_br_close = ''

    def _filter_page_data(self, required_keys, page_data):
        """
        Фильтрует данные, оставляет только запрошенные столбцы и удаляет пустые строки.

        :param required_keys: список ключей (заголовков), которые нужно оставить
        :param page_data: двумерный массив (список списков)
        :return: отфильтрованный двумерный массив
        """

        # Создаем словарь индексов всех ключей для оптимизации
        # Заголовки всегда идут первой строкой (требование формата!)
        header_to_index = {header: idx for idx, header in enumerate(page_data[0])}
        indices = [header_to_index[h] for h in required_keys]

        # Фильтрация данных по указанным индексам столбцов и удаление пустых строк
        headers, *data = [
            [row[idx] for idx in indices] 
            for row in page_data
            if any(row[idx].strip() != '' for idx in indices)
            ]
        
        return headers, data

    def _prepare_to_parser(self, key, value):
        """
        Собрает строку для парсера. Необходимо для корректно йобработки команд в ключах
        Ключ должен попасть под пасер на общих словиях, тогда он будет корректно обработан

        :param key: ключ
        :param value: значение
        :return: Строка готовая для корректного разбора парсером
        """
        # TODO: Сюда хорошо бы вставить проверку и запорачивать корректно. 
        # Заворачивать нужно только в том случае, если удалось разделить строку по sep_block, sep_base или sep_dict
        # Учитывая блоки используя parser.split_string_by_sep
        return f'{key} {self._parser_sep} {self._parser_br_open}{value}{self._parser_br_close}'

    def _parse_complex_schema(self, page_data, parser, schema):
        """
        Парсит данные по обычной схеме, где есть несколько столбцов с данными.
        
        gsconfig.set_schema()       

        :param page_data: двумерный массив (список списков)
        :param parser: объект парсера
        :param schema: словарь схемы данных
        :return: отфильтрованный и преобразованный словарь
        """
        
        # Определяем необходимые ключи и фильтруем данные
        required_keys = [schema['key']] + list(schema['data'])
        headers, data = self._filter_page_data(required_keys, page_data)

        # Определяем индексы ключей и данных
        key_index = headers.index(schema['key'])
        data_indices = [headers.index(x) for x in schema['data']]

        # Ключ по умолчанию. Если не задан, то будет использоваться первый из списка data
        # Столбец из которго будут браться данные когда они не заданы в других столбцах
        default_key = schema.get('default', schema['data'][0])
        default_data_index = headers.index(default_key)

        # Парсим данные по схеме
        out = {}
        for data_index in data_indices:
            buffer = {}
            for line in data:
                line_data = line[data_index] or line[default_data_index]
                line_to_parse = self._prepare_to_parser(line[key_index], line_data)
                buffer.update(parser.jsonify(line_to_parse))
            
            out[headers[data_index]] = buffer

        return out
    
    def _parse_simple_schema(self, page_data, parser, schema):
        """
        Парсит данные по простой схеме, где только один столбец с данными.
        Для разбора используется как частный случай self._parse_complex_schema
        
        См. gsconfig.set_schema()

        :param page_data: двумерный массив (список списков)
        :param parser: объект парсера
        :param schema: словарь схемы данных
        :return: отфильтрованный и преобразованный словарь
        """
        schema = {
            'key': schema[0],
            'data': [schema[-1]]
            }

        return self._parse_complex_schema(page_data, parser, schema)[schema['data'][0]]

    def _parse_free_format(self, page_data, parser, key_skip_letters):
        """
        Парсит данные в свободном формате, где первая строка - ключи, все последующие - данные.

        :param page_data: двумерный массив (список списков)
        :param parser: объект парсера
        :param key_skip_letters: символы для пропуска ключей
        :return: отфильтрованный и преобразованный список
        """
        
        # Определяем заголовки и фильтруем данные
        headers_raw = page_data[0]
        required_keys = [
            key for key in headers_raw
            if not any(key.startswith(x) for x in key_skip_letters)
            and len(key) > 0
            ]
        headers, data = self._filter_page_data(required_keys, page_data)

        # Парсим данные в свободном формате
        out = []
        for line in data:
            buffer = {}
            for key, value in zip(headers, line):
                line_to_parse = self._prepare_to_parser(key, value)
                buffer.update(parser.jsonify(line_to_parse))

            out.append(buffer)

        # Развернуть лишнюю вложенность когда только один элемент
        if len(out) == 1:
            return out[0]

        return out

    def _extract_json(self, page_data, **params):
        """
        Парсит данные из гуглодоки в формат JSON. См. parser.jsonify

        Когда формат не указан - возвращает сырые данные как двумерный массив.
        Понимает несколько схем компановки данных. Проверка по очереди:
        1. Используется схема данных. См. Page.schema и Page.set_schema()
        2. Свободный формат, первая строка - ключи, все последующие - данные соответствующие этим ключам

        **params - все параметры доступные для парсера parser.jsonify
        """
        
        # Получаем параметры
        schema = params.get('schema')
        key_skip_letters = params.get('key_skip_letters', [])
        parser = gsparser.ConfigJSONConverter(params)

        # Данные по структуре из парсера
        # необходимы для корректного разбора команд ключей
        self._parser_sep = parser.params['sep_dict']  # разделитель словаря
        self._parser_br_open = parser.params['br_block'][0]  # открывающая скобка блока
        self._parser_br_close = parser.params['br_block'][-1]  # закрывающая скобка блока

        # Парсим данные по обычной схеме
        if isinstance(schema, dict):
            return self._parse_complex_schema(page_data, parser, schema)
        
        # Парсинг по простой схеме
        if isinstance(schema, tuple) and all(x in page_data[0] for x in schema):
            return self._parse_simple_schema(page_data, parser, schema)
        
        # Обработка в свободном формате когда нет схемы
        return self._parse_free_format(page_data, parser, key_skip_letters)

    def _extract_dummy(self, page_data, **params):
        """
        Возвращает неизмененные данные.
        """
        return page_data

    def get(self, page_data, format='json', **params):
        """
        Извлекает данные в указанном формате.

        :param page_data: двумерный массив (список списков)
        :param format: формат данных ('json', 'csv', 'raw')
        :param params: дополнительные параметры для парсера
        :return: отфильтрованные и преобразованные данные
        """

        if format not in self.extractors:
            raise ValueError(f'Unsupported format: {format}. Supported formats are: {list(self.extractors.keys())}')

        return self.extractors[format](page_data, **params)
