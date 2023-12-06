import os
import gsconfig

os.chdir(os.path.dirname(os.path.abspath(__file__)))

gspread_id = '1yaecKybihfddy96pRGcFLnna6zEl_2gHnOC3wlBQYow'  # EG google drive
# gspread_id = '1nNvAiOlc9qdiAFcAUcRwl5F7rbNpHtjBXPfTiLHBqfA'  # My own google drive

config = gsconfig.GameConfigLite(gspread_id)
config.parser_mode = 'v2'

# print(type(config))
# print(type(config.spreadsheet))

# Все страницы конфига
# for page in config:
#     print(page.title, page.name, page.format, type(page))

# print()
# Только актуальные к экспорту страницы
# for page in config.pages():
#     print(page.title, page.name, page.format, type(page))

# print()
# Забрать содержимое конкретной (первой в списке) страницы
page = config.page1
# print(page.parser_mode)
print(config['tentacles_count.json'])
# print(config['#items'])
# print(page.get())
# print(page.get(mode='raw'))
# print(page.get(format='csv'))

# Сохранить все страницы конфига
config.save('_json')
