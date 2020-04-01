import os
import gsconfig
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

google_oauth2_token_file_path = 'google_oauth2_token.json'
gspread_id = '18l0UwSwQswrobsfKptLtfiwvEjFCjxyV4Mn3wGIIcIY'
page_title = 'documents'

client = gsconfig.GoogleOauth(google_oauth2_token_file_path)


gspread = {'gspread_id': gspread_id, 'page_title': page_title}

settings = {
    'clothes': '1w03vUeO6SLUlfhkCa86hTbRGsZcynJxyFMONHUmGJp4',
    'category': '1ZVIhyfrU2hsSf3ENO0efSAis2zW8FHLa-izi8o6J1oc',
    'wardrobe': '1MwRGpqjImvDjBN2ScXFKnitmRll2CBKj3n2YSoolEaM',
    }

# backup = gsconfig.tools.load_source_from_backup('_backup/dev.backup')
game_config = gsconfig.GameConfig(client, settings = gspread, backup = {})

gsconfig.tools.backup_config(game_config, 'dev.backup', '_backup/')
gsconfig.tools.save_config_documents(game_config, '_json/')
