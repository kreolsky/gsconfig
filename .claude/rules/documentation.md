---
alwaysApply: true
---

# Documentation as Architecture

Code is the single source of truth. Document only what is **not inferable from the code**:
traps, not operations.

## Markers (grep-able)

* `ARCH:` — an architectural decision, ONLY when cross-cutting or on a system boundary
  (the data path sheet → extractor → converter → template, the parser-version split, the
  command registries). A LOCAL non-obvious choice is `WHY:`, not `ARCH:`.
* `INVARIANT:` — a constraint that must hold (a cell string's parse result, separator
  precedence, bracket balancing, the recursion order of template commands). Always
  followed by a `Why:` on the same line or within the next 2 lines — gated by
  `invariant-why-gate.py`. Optional severity tag: `INVARIANT(compat):` where violating it
  changes the output of existing spreadsheets or templates.
* `WHY:` — a non-obvious implementation choice (a gspread quirk, a regex trade-off, a
  format conversion).
* `DEBT: <what> — Why deferred: <reason>` — a CONSCIOUSLY deferred refactor left in place
  on purpose. On the load-bearing line; `debt-gate.py` holds the ledger at zero net
  growth. A `# TODO:` in the tree is not a `DEBT:` — convert it when you touch it.
* `SYSTEM: <name> — <desc>` — the ENTRY POINT of a named subsystem, line 1 of the entry
  file, at most one per subsystem. Cross-references use prose: `see SYSTEM: <name>`.
  Adding, renaming, removing or moving one ⇒ `python3 .claude/scripts/systems-index.py
  --write` and commit `SYSTEMS.md`. Aliases (incl. Russian task nouns) live in
  `.claude/systems-aliases.json`.

## Language

New and changed comments and docstrings in `gsconfig/` are **English**. The tree predates
this and carries Russian docstrings; `cyrillic-src-gate.py` holds each file at zero net
growth against `.claude/baselines/cyrillic.json`. A docstring you rewrite anyway is
translated in the same edit, and the baseline is lowered with `--update` in that commit.
Do NOT translate untouched docstrings as a drive-by — that is its own task.

## Doc tiers

1. **In-code markers + docstrings** — the contract, for whoever edits the code.
2. **`docs/` (EN) + `docs_ru/` (RU)** — the USER manual, a mirrored pair (same file numbering,
   same sections). A change to user-visible behaviour — a param, a command, a format rule,
   a public name — updates BOTH in the same commit. `README.md` links into them.
3. **`CLAUDE.md` / `RULES.md` / `.claude/`** — the harness; they reference markers, never
   restate them.

## No process provenance in comments

A comment states the CONTRACT, never the process that produced it: no plan slugs,
`Stage N`, `review F3`, bare dates or `plans/…` references. Historical narrative ("used to
/ was removed when") is deleted, not rewritten. Touching a file means cleaning its header
to that shape (comments only; never rewriting an `INVARIANT:`'s rule text).

## A contract that MOVES carries its existing words

Before writing a `WHY:`/`INVARIANT:` for behaviour you are RELOCATING, read the one being
replaced (`git show <commit>^:<file>`) and move it verbatim.

## Single home for contracts

A contract lives in ONE place — the marker on the load-bearing line. The long Russian
docstrings on `ConfigJSONConverter` and `Template` are the user-facing reference for params
and commands; when one of those changes, the docstring AND `docs/`+`docs_ru/` change
together — the harness never copies them.

## Docstrings

* Every module: a one-line module docstring. **Tier 1** (non-obvious behaviour, side
  effects, error conditions): full docstring. **Tier 2**: one line. **Tier 3**: none.
* Never document what the signature already says, or what stdlib does.

## Decision pinning

User-stated business logic (how a separator splits, what `v2` unwraps, which pages are
skipped, what a command does to a type) MUST be captured on the **load-bearing line**:

```python
# INVARIANT: <rule in the user's plain words>.
# Why: <the reason they gave>.
```

No asking, no batching. A bugfix in a repeatedly-regressing area MUST add or tighten an
`INVARIANT:` + `Why:` on the broken line — and a golden case in
`examples/converter_test_cases.json` (converter) or a case in `tests/` (template).

**Maintenance**: markers move with their code. A marker contradicting behaviour → stop and
ask which is wrong; never silently fix either side.
