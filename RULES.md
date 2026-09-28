# Development Rules — Index

**Two tiers.** `.claude/rules/` is auto-injected every session — only process-wide rules
live there; keep it lean. `.claude/rules-scoped/` is NOT auto-loaded: each file is read on
demand when its path trigger fires (a PreToolUse hook reminds once per session on the first
matching edit). One concept = one file; pointers, not restatement.

## Always loaded (`.claude/rules/`)

- **`workflow.md`** — phase sequence + sizing (commits × entanglement), TDD cycle, plan
  rules, review gate + hot-path list, self-review, error recovery, debugging intake, hard
  rules (compatibility contract), auto-lessons. *(Single source of truth for the process.)*
- **`documentation.md`** — `ARCH:` / `INVARIANT:` / `WHY:` / `SYSTEM:` / `DEBT:` markers,
  code language (English for new lines), doc tiers incl. `docs`/`docs_ru` parity,
  decision pinning.
- **`coding-constraints.md`** — stdlib + gspread, public API, deletion test, layer
  consumers, surgical changes, size limits, symbol-removal audits, anti-mirage.
- **`git-strategy.md`** — S/M straight to `dev`; branch only for L; release via `/release`
  (tag + ff `master`); English-only commit messages.
- **`testing.md`** — golden cases are never edited to pass, v1 + v2 always, compare via
  `json.dumps`, reports are user scenarios.
- **`subagent-contract.md`** — return-card format for Agent-tool dispatches and `/review`.

## On demand (`.claude/rules-scoped/`) — READ BEFORE editing matching paths

| Trigger (files you are about to touch) | Read first |
|---|---|
| Running/debugging any suite, `tests/**` | `testing-ops.md` |
| `gsconfig/gsparser.py`, `gsconfig/extractor.py`, `examples/converter_test_cases.json` | `converter.md` (+ `testing-ops.md`) |
| `gsconfig/template/**` | `template.md` (+ `testing-ops.md`) |
| `gsconfig/gsconfig.py`, `google apps script/**` | `sheets.md` |
| `docs/**`, `docs_ru/**`, `README.md` | `docs.md` |
| Multi-system feature (Phase 1) | `integration.md` |

**A rule whose trigger is an activity rather than a path cannot live in this tier.** It is
always-loaded, or mechanized as a hook, or it is nothing.

## Artifacts

- **`plans/`** — every approved plan, `<epoch-ms>-<slug>.md` by `save-plan.py`; the one to
  implement is whichever the user names. Drafts overwritten in place are kept in
  `plans/superseded/` (ignored); plans untouched 90 days go to `plans/archive/YYYY-MM/`.
  `.kilo/plans/` belongs to Kilo Code and is not part of this flow.
- **`lessons/`** — written ONLY when something went wrong (`workflow.md` → Auto-lessons);
  generated `lessons/INDEX.md` (`python3 .claude/scripts/lessons-index.py --write`).
- **`SYSTEMS.md`** — generated subsystem catalog; aliases in `.claude/systems-aliases.json`.
- **`docs/release/`** — English release notes, one per tag (`/release`).
- **`DEBT:` markers** — the grepable tech-debt ledger.

## Gates (`.claude/scripts/`)

`pre-commit-gates.sh` runs them all in about a second — a PreToolUse hook runs it before
every `git commit` and blocks on red; run it **unpiped** by hand: `invariant-why`,
`systems-index`, `func-length`, `debt-ledger`, `cyrillic-src`. Each is zero-net-growth
against a committed baseline in `.claude/baselines/`; intentional growth is an `--update`
in the same commit with justification. `plan-shape-gate.py` fires on the plan write and at
`/implement` load, never on the commit. `merge-audit.py` and `release-audit.py` are
read-only pre-flights for `/merge` and `/release`. Hooks are dispatched by
`hook-guard.py` (stdin JSON; a block exits 2).

**Not gated yet — ruff.** The rule set is not pinned in the repo and `gsconfig/` carries
~48 findings (incl. two `W605` invalid escape sequences that emit `DeprecationWarning`).
Pin the rules in a `pyproject.toml`, fix or baseline, then add it to the gates.

## Skills (invoke via `/command`)

- `/grill` — interrogate a plan or design by rounds until nothing is silently assumed.
- `/implement` — orchestrate the workflow phases (scope → TDD → implement → review → commit).
- `/tdd` — TDD initialization.  `/review` — post-implementation self-review.
- `/run-tests` — full pytest suite (golden converter cases v1/v2 + templates).
- `/merge` — pre-merge audit + merge an L branch into `dev`.
- `/release` — version bump, note, tag, ff `master`.
- `/retro` — session retrospective and lesson capture.
- **Audits, three different questions** — `/intent-audit` (markers vs code) ·
  `/liveness-audit` (is this layer reachable from a root) · `/reality-audit` (prose in
  `CLAUDE.md` / `RULES.md` / skills / docs vs code).
