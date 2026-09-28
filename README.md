# gsconfig

Python library for game configs in Google Sheets: turns a compact cell syntax into JSON and
renders config files from templates. Built on [gspread](https://docs.gspread.org/en/latest/).

[English docs](docs/README.md) | [Документация на русском](docs_ru/README.md)

Game designers keep balance data in spreadsheets — with their own formulas and layout — and
gsconfig exports it as JSON the game reads, without anyone typing JSON by hand.

## Install

```bash
pip install git+https://github.com/kreolsky/gsconfig@v0.16.1
```

The library is **not on PyPI** — the `gsconfig` package there is an unrelated project.
Releases are git tags; see [docs/release/](docs/release/).

Requires Python 3.8+, `gspread`, and Google credentials (OAuth or a service account —
see [Authentication](docs/01-quick-start.md#authentication)).

## Example

```python
import gsconfig

client = gsconfig.GoogleOauth().client                      # OAuth; or GoogleOauth('keyfile.json')
config = gsconfig.GameConfigLite('<spreadsheet id>', client)

mobs = config['mobs.json'].get()                            # the page "mobs.json" as dict/list
```

Cells use a short syntax instead of JSON:

| Cell | JSON |
|------|------|
| `hp = 10, speed = 2.5` | `{"hp": 10, "speed": 2.5}` |
| `fire, ice, poison` | `["fire", "ice", "poison"]` |
| `drops = ["gold", "gem"]` | `{"drops": ["gold", "gem"]}` |
| `{type = sword, dmg = 7} \| {type = bow, dmg = 4}` | `[{"type": "sword", "dmg": 7}, {"type": "bow", "dmg": 4}]` |

The same data can be rendered into any text config through templates:
`hp: {% hp %}` → `hp: 10`, plus `if` / `foreach` / `for` blocks — see
[Working with Templates](docs/05-working-with-templates.md).

## Documentation

1. [Quick Start](docs/01-quick-start.md)
2. [Core Abstractions](docs/02-core-abstractions.md)
3. [Intermediate Format and Conversion](docs/03-intermediate-format.md)
4. [Data Extraction and Schemas](docs/04-data-extraction.md)
5. [Working with Templates](docs/05-working-with-templates.md)
6. [Best Practices](docs/06-best-practices.md)
7. [Custom Extensions](docs/07-custom-extensions.md)
8. [Recipes and Examples](docs/08-recipes-and-examples.md)
9. [API Reference](docs/09-api-reference.md)

## License

[MIT](LICENSE)
