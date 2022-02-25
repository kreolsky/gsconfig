import os
import gsconfig


os.chdir(os.path.dirname(os.path.abspath(__file__)))

gspread_id = '1zQ4J6uExfqSINeCwYyyqcpDMstT_xjN55-EnMvv6W5M'
config = gsconfig.GameConfigLite(gspread_id)

print(type(config))
print(type(config.spreadsheet))

# Все страницы конфига
for page in config:
    print(page.title, page.name, page.format, type(page))

# Только актуальные к экспорту страницы
for page in config.pages():
    print(page.title)

# Забрать содержимое конкретной страницы
page = config["characters.json"]
print(type(page))
print(page.get())
print(page.get(mode='raw'))
print(page.get(format='csv'))

# Сохранить все страницы конфига
# config.save('_json')
