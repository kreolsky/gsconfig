import os
import gsconfig


os.chdir(os.path.dirname(os.path.abspath(__file__)))

google_oauth2_token_file_path = 'google_oauth2_token.json'
gspread_id = '1mZJtTkSzYRVcWJx93IMHOxCSwmgHVUDI8g93LziFvTs'

client = gsconfig.GoogleOauth(google_oauth2_token_file_path)
config = gsconfig.GameConfigLite(client, gspread_id)

print(type(config))
# print(config.spreadsheet.fetch_sheet_metadata(params = {"includeGridData": "true"}))

# Все страницы конфига
for page in config:
    print(page.title)

# Только актуальные к экспорту страницы
for page in config.pages():
    print(page.title)

# Забрать содержимое конкретной страницы
ws = config[".players.json"]
print(type(ws))
print(ws.get())

# Сохранить все страницы конфига
config.save('_json')
