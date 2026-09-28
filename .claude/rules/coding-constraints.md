---
alwaysApply: true
---

# Coding Constraints

* Standard library + `gspread` only. A new runtime dependency goes into `setup.py`
  `install_requires` in the same commit — or it does not go in. (`oauth2client` is
  imported lazily in `GoogleOauth` for the service-account path and is NOT declared; do
  not add a second undeclared import.)
* No over-engineering, no redundant abstractions. Simplest tool for the job.
* No nested conditional chains. Lookup dicts (the `extractors`, key-command and
  template-command registries are the pattern) and early returns.
* Fail loud on bad input: a cell that cannot be parsed raises with the cell text in the
  message (the `Extractor` does this); a silent fallback to a raw string is a bug, not a
  feature, unless `is_raw` / `raw_pattern` asked for it.
* Semantic naming. All NEW code, comments and docstrings in English (`documentation.md`).
* **Public API is what `gsconfig/__init__.py` re-exports** plus the documented params,
  commands and methods in `docs/09-api-reference.md`. Renaming or removing any of it is
  breaking; keep a backward-compat alias (`AVAILABLE_VESRIONS` is the precedent) and say so
  in the release note.
* **Deletion test** — before keeping an abstraction, imagine deleting it. Complexity
  vanishes ⇒ inline it. Complexity reappears across N callers ⇒ it earns its keep. The
  unit under test is the whole module or registry that owns the dispatch, not one arm.
* **A layer between this library and an external surface is kept by naming its
  consumer.** Surfaces: the Google Sheets API (gspread), the spreadsheet authors (the
  intermediate format), `.template` files, the game that reads the JSON, the user's
  Python code (public API). Name a `file:line` where something downstream gets from the
  layer what the surface below does not supply. Not named ⇒ it goes. A named consumer
  counts only if it is itself reachable from a root: a public name, a documented param or
  command, a golden case, an example notebook the docs point to. An unreachable chain ends
  in a QUESTION to the user, never in an agent's deletion (`/liveness-audit`).
* **A dead layer goes in the session that FOUND it** — same commit as the change that
  proved it dead, unless the deletion tail makes the diff unreadable.
* **One adapter is a hypothetical seam; two are a real one.**
* **Consolidating duplicate code** (the parser-version / skip-letters setters repeat across
  `Page`, `Document`, `GameConfig`): if the sites diverge in behaviour, STOP and ask which
  to keep. Never assume the divergence is accidental.
* **Surgical changes only**: don't "improve" adjacent code, comments or formatting. Remove
  what YOUR change made unused; leave pre-existing dead code unless asked.
* **Size limits**: file > 500 lines → propose a split (soft). Function > 50 lines → split
  (hard) — `func-length-gate.py`, zero-net-growth against `.claude/baselines/func-length.json`.

## Removing or moving an existing symbol

* Grep the bare name across `gsconfig/`, `tests/`, `examples/` (notebooks included),
  `docs/`, `docs_ru/`, `README.md`, `google apps script/`.
* A class attribute that users may set or patch (`Template.DEFAULT_KEY_COMMAND_HANDLERS`,
  `register_key_command`) is public by use even when undocumented.

## Read the entry file — don't infer a contract from one symbol

Before building ON or NEXT TO an existing mechanism (the block parser, the schema
detection, the template-command recursion metadata), READ its `SYSTEM:` entry file —
docstring plus markers. Do NOT reconstruct its contract from one regex or one param.

**Adding a case for a NAME to a dispatch site obliges a repo-wide grep of that name first**
— a key command, a template command, a page format, a parser version, a v2 short command
(`[]`, `()`, `{}`). An existing arm for the same name means the case is ALREADY OWNED.

## Anti-mirage validation

After generating or modifying >20 lines, verify: every `import` references a real module;
every call matches a real signature; every param the code reads exists in
`ConfigJSONConverter.default_params` or is documented; new syntax runs on Python >= the
floor in `setup.py` `python_requires` (or the floor is raised on purpose). If unsure an API
exists — gspread especially — grep or check the installed version before using it.
