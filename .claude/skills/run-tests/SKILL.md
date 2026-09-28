---
name: run-tests
description: >
  Run the full gsconfig test suite (golden converter cases v1/v2 + template engine) and
  report. Прогони тесты, запусти тесты, проверь тесты, проверь конвертор, тесты конвертора,
  сценарии конвертора, run tests, run pytest, test the converter, converter test scenarios,
  verify converter correctness. Do NOT use for: a single targeted test while
  debugging (run pytest directly), or a live Google Sheets drive.
---

# run-tests — full gsconfig suite

Commands and environment live in `.claude/rules-scoped/testing-ops.md` — read it; this skill
only sequences them.

## 1. Pick the interpreter

It needs `pytest` AND `gspread`:

```bash
for py in python3 python ~/.miniconda3/bin/python; do
  $py -c "import pytest, gspread" 2>/dev/null && { echo "$py"; break; }
done
```

None found → say so and stop; do not `pip install` into an environment without asking.

## 2. Run

```bash
<py> -m pytest tests/ -q --tb=short
```

Offline, under a second. `tests/conftest.py` pins the local tree, so a pip-installed
`gsconfig` cannot mask a failure.

## 3. Report

```
N passed, M failed in T s   (interpreter: <py>)
```

On failures: the `FAILED …` lines only. For a converter case, show the input string, the
version, got vs expected (`json.dumps`) — the parametrize id (`v2-17`) is the index into
that version's `data` list in `examples/converter_test_cases.json`; `<py> -m pytest
tests/test_converter.py -k "v2-17" -vv` prints the full diff. Per version, also report the
error count (`v1: 0 errors, v2: 2 errors`) — the shape the old notebook check used.

Then per `.claude/rules/testing.md` → *propose, don't ask*: a short fix plan, started
without waiting — unless the fix changes what an EXISTING input produces (stop with a
recommendation). Never edit a golden case to make the run green.
