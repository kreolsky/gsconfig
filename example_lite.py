import os
import gsconfig


os.chdir(os.path.dirname(os.path.abspath(__file__)))

gspread_id = '1cxzI4JJY-n4K5PJ4cd6TuNV4e5spt3q6W2X2Cj_gCrE'
config = gsconfig.GameConfigLite(gspread_id)

print(type(config))
print(type(config.spreadsheet))

# Все страницы конфига
# for page in config:
#     print(page.title, page.name, page.format, type(page))

# Только актуальные к экспорту страницы
# for page in config.pages():
#     print(page.title, page.name, page.format, type(page))

# Забрать содержимое конкретной страницы
page = config["characters.json"]
print(type(page))
print(page.get())
print(page.get(mode='raw'))
print(page.get(format='csv', mode='raw'))

# Сохранить все страницы конфига
# config.save('_json')
