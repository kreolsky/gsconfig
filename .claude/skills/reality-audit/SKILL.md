---
name: reality-audit
description: Verify CLAUDE.md/RULES.md/skills/lessons prose against the actual code. Аудит реальности, сверка манифеста, проверь CLAUDE.md, устарели ли правила, актуальность правил, drift правил.
---

# Reality Audit

Manual, ~monthly, or when the manifest "feels stale". Verifies prose claims that the gates
do NOT already cover — `pre-commit-gates.sh` owns `SYSTEMS.md` freshness, `INVARIANT:`+`Why:`,
the DEBT ledger, function length and Cyrillic growth in `gsconfig/`, so those are skipped here.

Verify against the code, never against this file's assumptions. Sibling audits, different
questions: `/intent-audit` checks in-code markers against the code, `/liveness-audit` walks
reachability. Neither reads prose.

## 1. `CLAUDE.md` claims

Each checkable assertion, verified by grep or read — not by memory:

- the public-API list matches `gsconfig/__init__.py` exports — **both directions**;
- the parser params and their defaults match `ConfigJSONConverter.default_params`; the
  parser versions match `AVAILABLE_VERSIONS`; the v2 command list matches
  `BlockParser.command_handlers` + `short_commands`;
- the key/template command lists match `Template.DEFAULT_*_HANDLERS`;
- page formats match `Extractor().extractors`; skip-letter defaults match
  `Document._init_common`; `python_requires` in `setup.py` vs the syntax actually used.
- the same lists in `docs/09-api-reference.md` and `docs_ru/09-*` — and that the two
  trees still mirror each other (file numbers, section headings).

Report per mismatch: `WAS (manifest): … / NOW (code): …`.

## 2. `RULES.md` routing table

Every trigger path in the on-demand table matches real paths, and every referenced
`rules-scoped/` file exists. The always-loaded list matches `ls .claude/rules/`. There is no
skills list to check — the harness injects skill names and descriptions itself, so a list
here would be an index bound inside the book it indexes.

## 3. Rules ⇄ code ⇄ skills drift

This is where the audit earns its keep, because nothing else looks here:

- every script referenced in `.claude/rules/**` and `.claude/skills/**` exists in
  `.claude/scripts/`, and every flag quoted for it is real (`--template`, `--write`,
  `--check`);
- commands quoted in `rules-scoped/testing-ops.md` and in the skills still run: service
  paths exist, interpreters named in `testing-ops.md` still have pytest + gspread;
- **a skill quoting a contract that a rule owns** — a section list, a trigger list, a
  hot-path list. A rule is the single home (`documentation.md` → *Single home for
  contracts*); a skill restating one is drift waiting to happen, and the fix is a pointer,
  not a resync;
- `python3 .claude/scripts/lessons-index.py --check` and `systems-index.py --check` pass.

## 4. `lessons/` citations

File paths and symbol names cited in a lesson's "Actionable rule" still exist. A stale
citation gets a `(moved: …)` note proposed — **never delete the lesson**.

## 5. Report — wait for approval

One WAS/NOW report plus the proposed edits, in the card form of `subagent-contract.md`.
**Never silently rewrite the manifest.** A claim contradicting the code means one of the two
is wrong, and which one is the user's call (`documentation.md` → Maintenance: a marker
contradicting behaviour → stop and ask).
