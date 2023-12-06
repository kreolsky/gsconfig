import os
import gsconfig
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# # Кастомный паттерн распознавания переменных в шаблоне
# pattern = r'\{%\s*([a-z0-9_!]+)\s*%\}'
# template_body = """
# - Как звучит радость?
# - Вот так: "{% variable %}"
# - Сколько коров?
# - Вот столько: {% cow!int %} (int) или {% cow %} (source) 
# - И еще давай словарик
# - Вот словарик: {% dict %}
# - И пустота: {% empty %}
# """
# template = gsconfig.Template(body=template_body, pattern=pattern)

# Дефолтный паттерн
template_path = 'example_template.template'
template = gsconfig.Template(path=template_path)

# Словарь с переменными для замены
data = {
    'variable': 'Woohooo!',
    'substring': 'subSTRing',
    'cow': 10.9,
    'dict': {'key': 'value', 'list': ['one', 'two', ['three', 'four', 'five']]},
    'empty': ''
}

r = json.loads(template.make(data))
# r = template.make(data)
print(r)

