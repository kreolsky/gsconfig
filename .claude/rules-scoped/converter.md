# Converter & extractor — `gsconfig/gsparser.py`, `gsconfig/extractor.py`

Read before editing either file. Entry points: `SYSTEM: converter`, `SYSTEM: extractor`.

* **The grammar is a public contract.** Every string a spreadsheet author can type is
  parsed by this code in sheets the repo never sees. Changing the output for an input that
  already parses is breaking (`workflow.md` → Hard rules); prove it is not by running the
  golden cases AND adding a case for the new input.
* **Both versions, always.** `v1` wraps every dict in a list; `v2` unwraps length-1 lists
  and uses key commands (`!list`, `!flist`, `!dlist`, `!wrap`, …) and the short forms
  `[]`/`()`/`{}`. A change to shared code (`split_string_by_sep`, `parse_string`,
  `BlockParser`) runs under both.
* **Separators have a precedence**: `sep_block` (`|`) → `sep_base` (`,`) → `sep_dict`
  (`=`), each split only at bracket depth 0, `raw_pattern` (`"`) strings untouched. Adding
  a separator or bracket type touches `get_all_brackets` and every split call.
* **`br_list` content is Python-literal syntax** (`ast.literal_eval`) — never mixed with
  the simplified syntax.
* **Params flow**: `Document._init_common` → `Page.get(**params)` → `Extractor._get_parser`
  (cached by `str(sorted(params.items()))` — params values may be unhashable: dict schema,
  set skip letters) → `ConfigJSONConverter({**default_params, **params})`. A new param is
  added to `default_params`, the class docstring, and `docs/{03,09}-*` + `docs_ru/{03,09}-*`.
* **Schema detection order** in `Extractor._extract_json`: dict schema → tuple schema whose
  columns are all in the header row → free format. A key cell is wrapped into
  `key = {value}` by `_prepare_to_parser` so key commands parse — keep that in mind before
  changing brace handling.
* The TODO in `_prepare_to_parser` is known debt; convert it to `DEBT:` if you touch it.
