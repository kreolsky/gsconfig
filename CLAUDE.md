# GSConfig — Project Bible

Python library (`gsconfig`, installed from git — not on PyPI) for game configs kept in Google Sheets: reads worksheets
through gspread, converts a compact spreadsheet syntax (the *intermediate format*) to JSON,
and renders config files from templates.

**Development rules, coding standards, and lessons: see `RULES.md`.**

## Tech Stack

* **Language**: Python 3.8+ (`setup.py` `python_requires`; the floor is set by the walrus in
  `gsconfig/gsparser.py`)
* **Runtime dependency**: `gspread` (declared); `oauth2client` (lazy, service-account path
  only, NOT declared)
* **Testing**: pytest, offline — `tests/` (commands: `.claude/rules-scoped/testing-ops.md`)
* **Packaging**: `setup.py` + `__version__` in `gsconfig/__init__.py`; not published to
  PyPI (the name `gsconfig` there is another project). Install:
  `pip install git+https://github.com/kreolsky/gsconfig@vX.Y.Z`. CI
  (`.github/workflows/tests.yml`) runs `tests/` on push to `dev`/`master`
* **Branches**: work on `dev`; `master` = released

## Core Systems

**Data path**: Google Sheet → `Page` (gspread worksheet, values cached) → `Extractor`
(format from the page-title suffix `.json` / `.csv` / raw; schema detection) →
`ConfigJSONConverter.jsonify` per cell → dict/list → `JSONHandler` / `tools` save, or →
`Template.render(balance)` → config file text.

**Sheets access** (`gsconfig/gsconfig.py`): `GoogleOauth` (gspread OAuth or service-account
keyfile) → `GameConfigLite` (one spreadsheet) / `GameConfig` (several, opened in parallel) →
`Document` → `Page`. Pages/keys starting with `page_skip_letters` / `key_skip_letters`
(default `{'#', '.'}`) are not exported. Params: `parser_version` (`v1` default, `v2`).

**Extractor** (`gsconfig/extractor.py`): three layouts, tried in order — complex schema
(dict: `key`, `data: [...]`, `default`), simple schema (tuple `('key', 'data')`, the
default, when both columns exist), free format (row 1 = keys, each row = one object).

**Converter** (`gsconfig/gsparser.py`): the intermediate-format grammar — separators
`|` block, `,` item, `=` key/value, `!` key command; `{}` sub-blocks, `[]` Python literals,
`"` raw strings. `v1` wraps every dict in a list; `v2` unwraps length-1 lists and honours key
commands (`list`, `flist`, `dlist`, `wrap`, `string`, `json`, `int`, `float`) and short forms
`[]`/`()`/`{}`. All params and defaults: `ConfigJSONConverter` docstring.

**Template engine** (`gsconfig/template/`): `{% key!cmd %}` substitution with key commands
(`float`, `int`, `json`, `string`, `list`, `extract`, `wrap`, `none`, `get_N`), block commands
`if` / `comment` / `foreach` (`$item`) / `for` (`$i`), `{# #}` comments. Extensible through
`register_*` (class) and `add_*` (instance). Recursion order per command:
`DEFAULT_TEMPLATE_COMMAND_METADATA`.

**Google Apps Script** (`google apps script/*.js`): runs inside Sheets and builds the
config trees the library reads; not Python, not tested here.

## Compatibility contract

Spreadsheets and `.template` files that the repo never sees depend on the grammar, the
template syntax, the defaults and the public names in `gsconfig/__init__.py`. A change to
what an existing input produces is **breaking** (`workflow.md` → Hard rules). The golden
cases in `examples/converter_test_cases.json` (run by `tests/test_converter.py`) are the
executable part of that contract.

## Architecture Discovery

Start at **`SYSTEMS.md`** — the generated subsystem catalog (name · description · entry file
· aliases, incl. Russian task nouns). Regenerate with
`python3 .claude/scripts/systems-index.py --write`; `pre-commit-gates.sh` blocks on drift.

Markers (`.claude/rules/documentation.md`): `# ARCH:` cross-cutting decisions,
`# INVARIANT:` constraints (each with a `Why:`), `# WHY:` local choices, `# DEBT:` the
deferred-work ledger, `# SYSTEM:` subsystem entry points (line 1 of the entry file).

* `grep -rn "SYSTEM:" gsconfig/` — subsystem entry points
* `grep -rnE "(ARCH|INVARIANT|DEBT):" gsconfig/` — decisions, constraints, debt

## Docs

User manual in two mirrored trees: `docs/` and `docs_ru/` (same numbering). Examples:
`examples/*.ipynb`, `examples/templates/`. Legacy Russian docstrings in `gsconfig/` are
grandfathered; new comments are English (`cyrillic-src-gate.py`).

## Design Principles

* **Compatibility first**: new syntax is additive or opt-in (param, command, parser version).
* **Registries over branches**: formats, key commands, template commands are dispatch
  tables; extend them, don't add `if` chains.
* **Fail loud**: an unparseable cell raises with its text; no silent raw fallback.
* **Thin over gspread**: no Sheets logic that gspread already provides.
