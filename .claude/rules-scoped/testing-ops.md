# Testing ops — commands, environment, end-to-end drives

Read before running or debugging any suite. The judgement rules are in
`.claude/rules/testing.md`; this file is only the mechanics.

## Commands

```bash
python -m pytest tests/ -q                                  # everything, offline, < 1 s
python -m pytest tests/test_converter.py -q --tb=line       # golden converter cases, v1 + v2
python -m pytest tests/test_template.py -q --tb=line        # template engine
python -m pytest tests/ -k "v2-" -q                         # one parser version
```

Use an interpreter that has BOTH `pytest` and `gspread` (the package imports gspread at
top level). On this machine the conda base env has them: `~/.miniconda3/bin/python -m
pytest …`; the `wpc` env's `python3` has gspread but no pytest. `tests/conftest.py` puts the
repo root first on `sys.path`, so the tree under test is never a pip-installed copy.

`/run-tests` runs the full set and reports.

## Golden data

`examples/converter_test_cases.json` — `[{version, data: [[input, expected], …]}, …]`, one
group per parser version. `tests/test_converter.py` parametrizes over it (ids `v1-00` …),
so a new case is a new test with no code change. The same file is still read by
`examples/converter.ipynb`.

## End-to-end drive (Phase-4 acceptance)

Green tests are not acceptance. Drive the affected flow on real input, paste the output:

```bash
# converter — the exact cell strings, both versions
python3 -c "import sys; sys.path.insert(0,'.'); import gsconfig, json
for v in ('v1','v2'):
    print(v, json.dumps(gsconfig.ConfigJSONConverter({'parser_version': v}).jsonify('<cell>'), ensure_ascii=False))"

# extractor — a hand-built page per schema
python3 -c "import sys; sys.path.insert(0,'.'); from gsconfig import Extractor
page = [['key','data'], ['a','1, 2'], ['#skip','x']]
print(Extractor().get(page, 'json', schema=('key','data'), key_skip_letters={'#'}, parser_version='v1'))"

# template — render a real template (balance built from the keys it needs)
python3 -c "import sys; sys.path.insert(0,'.'); from gsconfig import Template
t = Template(path='examples/templates/MobSettings.template'); print(t.keys)"
```

A high-entanglement change renders EVERY `examples/templates/*.template` on `git stash` and
on the change, and diffs the two — the diff is the evidence.

A `sheets-access` change is driven against a live spreadsheet (`sheets.md`).
