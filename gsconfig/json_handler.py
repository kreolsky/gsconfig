
import os
import json

class JSONHandler:
    """
    Класс для работы с JSON-данными, обеспечивающий их загрузку, сохранение и форматирование.
    Поддерживает пользовательское форматирование JSON, включая возможность представления числовых списков в виде одной длинной строки.
    Форматирование специфичное для игровых конфигов, для более удобного просмотра глазами
    """

    @staticmethod
    def dumps(data, indent=4, inline=True, ensure_ascii=False, dict_items=5):
        """
        Преобразует JSON-данные в строку с возможностью форматирования числовых списков в одну строку.
        Метод позволяет гибко форматировать JSON-данные, особенно полезно для улучшения читаемости
        при отображении структур с числовыми массивами.

        Args:
            data (dict или list): JSON-данные для преобразования.
            indent (int, optional): Количество пробелов для отступа при форматировании вложенных структур. Defaults to 4.
            inline (bool, optional): Если True, числовые списки будут отображаться в одну строку для экономии места. Defaults to True.
            ensure_ascii (bool, optional): Если False, символы UTF будут сохранены как есть, иначе будут экранированы. Defaults to False.
            dict_items (int): Максимальное количество элементов в словаре, при котором он будет отображаться в одну строку.
                              Если элементов больше, словарь будет форматироваться с отступами. Defaults to 5.

        Returns:
            str: JSON-данные, отформатированные в виде строки с учетом заданных параметров форматирования.

        Example:
            >>> print(JSONHandler.dump(numeric_data))
            {
                "numbers": [1, 2, 3]
            }

            >>> print(JSONHandler.dump(nested_data))
            {
                "nested": {
                    "a": 1,
                    "b": [2, 3, 4],
                    "c": {
                        "d": 5
                    }
                }
            }
        """
        def serialize(obj, current_indent):
            """
            Рекурсивная функция для сериализации объектов в JSON-строку с учетом форматирования.
            
            Args:
                obj: Объект для сериализации (может быть dict, list, или примитивным типом)
                current_indent (int): Текущий уровень отступа для форматирования
            
            Returns:
                str: Сериализованный объект в формате JSON
            """
            # Создаем строку отступа на основе текущего уровня вложенности
            spacing = ' ' * current_indent
            if isinstance(obj, dict):
                # Проверяем, нужно ли отображать словарь в одну строку
                # Если количество элементов меньше или равно dict_items и все значения не являются сложными типами (dict или list)
                if (len(obj) <= dict_items and all(not isinstance(v, (dict, list)) for v in obj.values())):
                    # Формируем элементы словаря в одну строку
                    items = [f'"{ k }": {json.dumps(v, ensure_ascii=ensure_ascii)}'
                            for k, v in obj.items()]
                    return '{ ' + ', '.join(items) + ' }'
                
                # Обычное форматирование словаря с отступами
                items = []
                for key, value in obj.items():
                    # Рекурсивно сериализуем значение с увеличенным отступом
                    serialized_value = serialize(value, current_indent + indent)
                    items.append(f'{spacing}{" " * indent}"{key}": {serialized_value}')

                # Если есть элементы, формируем словарь с отступами
                if items:
                    return '{\n' + ',\n'.join(items) + f'\n{spacing}}}'
                else:
                    return '{}'

            elif isinstance(obj, list):
                # Проверяем, содержат ли все элементы списка только числа (int или float)
                if inline and all(isinstance(item, (int, float, str)) for item in obj):
                    # Если все элементы числовые, сериализуем их в одну строку для экономии места
                    serialized_items = [json.dumps(item, ensure_ascii=ensure_ascii) for item in obj]
                    return '[' + ', '.join(serialized_items) + ']'
                else:
                    # Иначе форматируем как обычный список с отступами
                    items = [serialize(item, current_indent + indent) for item in obj]
                    return '[\n' + ',\n'.join(f'{spacing}{" " * indent}{item}' for item in items) + f'\n{spacing}]'

            else:
                # Для примитивных типов используем стандартную сериализацию JSON
                return json.dumps(obj, ensure_ascii=ensure_ascii)

        # Запускаем рекурсивную сериализацию с начальным отступом 0
        return serialize(data, 0)

    @staticmethod
    def save(data, file_name, path='', indent=4, inline=True, ensure_ascii=False, dict_items=5):
        """
        Сохраняет JSON-данные в файл с использованием пользовательского форматирования.
        Этот метод позволяет сохранить отформатированные JSON-данные в файл с заданным форматированием.

        Args:
            data (dict или list): JSON-данные для сохранения.
            file_name (str): Имя файла для сохранения.
            path (str, optional): Путь к директории, где будет сохранен файл. Defaults to ''.
            indent (int, optional): Количество пробелов для отступа. Defaults to 4.
            inline (bool, optional): Если True, числовые списки будут отображаться в одну строку. Defaults to True.
            ensure_ascii (bool, optional): Если False, символы UTF будут сохранены как есть. Defaults to False.
            dict_items (int): Максимальное количество элементов в словаре для отображения в одну строку. Defaults to 5.
        """
        # Формирование полного пути к файлу, объединяя путь и имя файла
        file_path = os.path.join(path, file_name)

        # Форматирование JSON-данных с использованием метода dumps
        formatted_json = JSONHandler.dumps(data, indent, inline, ensure_ascii, dict_items)
        
        # Сохранение отформатированного JSON в файл с кодировкой UTF-8
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(formatted_json)

    @staticmethod
    def load(file_name, path=''):
        """
        Загружает JSON-данные из файла.
        Метод читает JSON-файл и возвращает его содержимое в виде Python-объекта (словаря или списка).

        Args:
            file_name (str): Имя файла для загрузки.
            path (str): Путь к директории, где находится файл.

        Returns:
            dict или list: Загруженные JSON-данные в виде Python-объекта.
        """
        # Формирование полного пути к файлу, объединяя путь и имя файла
        file_path = os.path.join(path, file_name)

        # Загрузка JSON-данных из файла с кодировкой UTF-8
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
