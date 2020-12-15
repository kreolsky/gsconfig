import os
import gsconfig
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

google_oauth2_token_file_path = 'google_oauth2_token.json'
gspread_id = '18l0UwSwQswrobsfKptLtfiwvEjFCjxyV4Mn3wGIIcIY'
page_title = 'documents'

client = gsconfig.GoogleOauth(google_oauth2_token_file_path)
game_config_lite = gsconfig.GameConfigLite(client, '1jSlEF1kLLkFYM36zaJsxWeDDhgo8YGfWKFMwJ2Ad4aA')

data = game_config_lite['instant'].get_page_data()
print(json.dumps(data, indent = 2))

# for page in game_config_lite:
#     print(type(page))

# gsconfig.tools.backup_config(game_config_lite, 'dev.backup', '_backup/')
# gsconfig.tools.save_config_documents(game_config_lite, '_json/')
