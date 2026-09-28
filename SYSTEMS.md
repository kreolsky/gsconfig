# SYSTEMS — subsystem catalog

GENERATED — do not edit; run `.claude/scripts/systems-index.py --write`.

Discovery: find your system (or an alias) here, then `grep -rn "SYSTEM: <name>"`
and read the entry file(s). Aliases are hand-maintained in
`.claude/systems-aliases.json`.

| System | Description | Entry file(s) | Aliases |
|--------|-------------|---------------|---------|
| converter | intermediate format to JSON (ConfigJSONConverter, parser v1/v2) | `gsconfig/gsparser.py:1` | парсер, промежуточный формат, jsonify, конвертор, parser_version, v1, v2 |
| extractor | page format dispatch (json/csv/raw) and data schemas (simple, complex, free) | `gsconfig/extractor.py:1` | схема, schema, формат страницы, json/csv/raw, извлечение данных |
| file-io | save pages as json/csv/raw, load json | `gsconfig/tools.py:1` | сохранение, save_page, tools, csv |
| json-output | game-config-friendly JSON dumps (inline numeric lists) | `gsconfig/json_handler.py:1` | сохранение json, форматирование json, dumps, JSONHandler |
| key-commands | `!command` value transforms applied to template variables | `gsconfig/template/key_commands.py:1` | команды ключей, !float, !int, !list, extract, wrap, get_N |
| package-api | public exports and __version__ (read by setup.py) | `gsconfig/__init__.py:1` | публичный api, экспорт, версия, __version__ |
| sheets-access | GoogleOauth, Page/Document wrappers over gspread, GameConfigLite/GameConfig | `gsconfig/gsconfig.py:1` | гуглодока, таблица, страница, документ, gspread, авторизация, oauth, page, document, gameconfig |
| template-commands | if/comment/foreach/for blocks and $item/$i | `gsconfig/template/template_commands.py:1` | if, foreach, for, comment, $item, $i, циклы шаблона |
| template-engine | Template load, variable substitution, command dispatch, render | `gsconfig/template/classes.py:1` | шаблон, template, рендер, render, подстановка |
