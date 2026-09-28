# Template engine — `gsconfig/template/**`

Read before editing. Entry points: `SYSTEM: template-engine`, `key-commands`,
`template-commands`.

* **Template syntax is a public contract** — `{% var!cmd!cmd %}`, `{% if/for/foreach/comment %}`
  blocks, `{# … #}` comments, `$item` / `$i`. Existing `.template` files outside the repo
  render through it; a change to what an existing template renders is breaking.
  Before/after render of every `examples/templates/*.template` is the evidence.
* **Regexes live in `constants.py`** and are the grammar. A regex edit is a hot-path edit
  (`workflow.md` Review gate): add a `tests/test_template.py` case for the construct.
* **Registries are the extension point**: `DEFAULT_KEY_COMMAND_HANDLERS` (regex → handler),
  `DEFAULT_TEMPLATE_COMMAND_HANDLERS` + `DEFAULT_TEMPLATE_COMMAND_METADATA`
  (`pre_process`/`post_process`). `register_*` mutates the class, `add_*` the instance —
  keep both working; users call them (`docs/07-*` + `docs_ru/07-*`).
* **Recursion metadata is load-bearing**: `foreach`/`for` expand BEFORE nested commands
  are processed (their `$item`/`$i` must be substituted first). A new block command
  declares its metadata explicitly — the `_default` is `post_process=True`.
* **`strip=True` (default)** means strings arrive unquoted and the template carries the
  quotes; `!string` quotes explicitly. `jsonify=True` returns a parsed dict.
* `_process_template_commands` is a grandfathered > 50-line function
  (`.claude/baselines/func-length.json`); split it rather than grow it.
