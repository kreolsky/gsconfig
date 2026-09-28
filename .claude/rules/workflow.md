---
alwaysApply: true
---

# Workflow (mandatory)

Single source of truth for: phase sequence, sizing, TDD cycle, review gate, self-review,
error recovery, debugging intake, auto-lessons. Other files point here — do not restate.

## Phases — required sequence

Skipping a phase = hard-rule violation.

**Two axes, and they answer different questions.** Commits decide how much PROCESS;
entanglement decides how much PROOF. **Neither counts files.**

| Size | Criteria — commits | Branch | Phases |
|------|--------------------|--------|--------|
| **S** Quick Fix | ONE commit, low entanglement | no — straight to `dev` | 0 → plan → 3 → 5 |
| **M** Feature | ONE commit, medium or high entanglement — it moves a contract | no — straight to `dev` | 0 → plan → 3 → 4 → 5 |
| **L** Epic | the plan's `## Order` carries 2+ commits | yes, from `dev` | 0 → 1 → 2 → 3 → 4 → 5 |

| Entanglement | Tests | Model |
|--------------|-------|-------|
| **low** (e≤2) → S | the test files covering what this diff can break, `--tb=line` | Haiku |
| **medium** (3–6) → M | full `tests/` | Sonnet |
| **high** (≥7) → M | full `tests/` **+ an end-to-end render** of every `examples/templates/*.template` before and after, diffed | **Opus** |
| any, but **L** | the above once at the last step — not per commit; see below | per e |

**Inside an L branch a commit is a step, not a release.** The branch owes the proof ONCE,
at its last step, over `git diff dev...HEAD`: the entanglement-table run, `/review`, the
end-to-end drive. An intermediate commit MAY leave the feature broken as long as
`## Progress` names what is broken and which step catches up; it owes only
`pre-commit-gates.sh` and the targeted tests of its own step.

Entanglement is computed from production `+` lines only (`gsconfig/`), so it cannot be
inflated by the tests, plans and docs this workflow itself mandates. Scope must still
enumerate the affected file paths.

**Size is not file count.** It is answered by two questions, in this order:

1. *Does this need more than one commit?* If yes — it needs a plan whose `## Order` says
   so, and that is the ONLY thing that earns a branch.
2. *How much must be held at once to not break it?* Entanglement — a boundary crossing on
   the data path (sheet → `Page` → `Extractor` → `ConfigJSONConverter` → JSON →
   `Template` → file), an `INVARIANT:` on the path, the **intermediate-format grammar**
   (what a spreadsheet cell parses to), the **template syntax** (what a `.template` renders
   to), the parser `v1`/`v2` split, the public API re-exported by `gsconfig/__init__.py`.
   Low → **S**; medium and high → **M**; and it sets the test regime and the model.

- **Phase 0 — Scope.** State S/M/L and the entanglement signals.
  **Discovery gate (also fires in plan/discussion mode, before any design):** look the
  task's nouns up in `SYSTEMS.md` (generated catalog: name · desc · entry file · aliases
  incl. Russian), then `grep -rn "SYSTEM:" gsconfig/` filtered to the matched names, then
  READ the entry file of each match. Any "new module / new param / new command / new
  format" proposal MUST cite the grep that proves it does not already exist.
- **Plan — after Scope, before any edit.** M/L and hot-path S get the plan FILE; every
  other S gets the three-line chat form. Both are under `## Plans` below.
- **Phase 1 — Integration checklist** (L only): `.claude/rules-scoped/integration.md`.
- **Phase 2 — TDD as a GATE** (L only). Failing tests BEFORE implementation. S and M still
  write tests — what L adds is the red run as a gate.
- **Phase 3 — Implement.** A running plan does not wait on a human: ambiguities, conflicts
  and plan defects are RULED ON, logged as `Ruling: <what> — <why> — <cost if wrong>`, and
  execution continues. Four things still stop it: an irreversible or destructive operation,
  a change to output that existing spreadsheets/templates already rely on (see Hard rules),
  a side effect outside this tree (merge, push, tag, a write to a Google
  Sheet), and a plan where every path forward is a guess. Run tests after each logical
  step; commands in `.claude/rules-scoped/testing-ops.md`. Add markers
  (`documentation.md`); regenerate `SYSTEMS.md` if a `SYSTEM:` marker changed.
- **Phase 4 — Review** (M; L once at its last step; S only when a Review-gate trigger
  fires). Auto-invoke `/review` — do not ask. Present findings, wait for approval.
  **Acceptance is reality-facing:** green tests are necessary, not sufficient. A change to
  `gsconfig/` is additionally driven end-to-end on REAL input and the output pasted
  verbatim: a converter change → `jsonify` of the real cell strings it affects, under
  BOTH `v1` and `v2`; a template change → a render of the affected
  `examples/templates/*.template`; an extractor/schema change → `Extractor().get()` over
  a hand-built 2-D page for each schema (simple, complex, free); a `sheets-access` change
  → a live run against a real spreadsheet (`.claude/rules-scoped/sheets.md`).
  Exemption: diffs touching only tests/docs with no runtime surface — state it.
  **Acceptance is PROPORTIONAL and on S it stops early**: targeted tests plus
  `pre-commit-gates.sh` ARE the acceptance of an S.
- **Phase 5 — Commit & Retro.** Commit only when the user asks. `/retro` runs only when an
  Auto-lessons trigger fired this session. **The plan file ships in the FIRST commit of
  its implementation, at every size** (`git-strategy.md`).

## TDD cycle

1. **Understand** — restate current vs expected behaviour + the code paths. Get confirmation.
2. **Write failing tests** — run them; all must fail for the right reasons. In a
   repeatedly-regressing area prove a regression test red by reverting the fix.
3. **Review from tests** — adjust the approach based on what writing them revealed.
4. **Implement** — run new + existing tests after each step.
5. **Review vs plan** — missed edge cases, incomplete guards.
6. **Fix rounds** (2–3) — the suite after each.
7. **Impact check** — no regressions in related systems.

Never modify an existing test — or a golden case in `examples/converter_test_cases.json` —
to make failing code pass.

## Plans

**Plans are ALWAYS written in English** — the whole file, regardless of the request's
language. Only the short chat summary may be in Russian. Enforced by `plan-shape-gate.py`.

**Approved plans land in `plans/`**, named `<epoch-ms>-<slug>.md` by `save-plan.py` (the
PostToolUse hook on ExitPlanMode). Plans untouched for 90 days are swept into
`plans/archive/YYYY-MM/`. There is no "active plan" pointer: the plan to implement is the
one the user names. (`.kilo/plans/` is the other tool's history — never written to.)

**A plan has ONE shape, and it is small.** `plan-shape-gate.py --template` prints it; it is
enforced by the Write|Edit hook and by `/implement`'s plan load. Write to 120 units
(paragraph / bullet / step, not wrapped line); the gate fires at 150 — past that, split.

**Understanding changed ⇒ delete the file and write it again; never append.** The previous
version is kept in `plans/superseded/` by `plan-snapshot.py`.

**A decision touching existing behaviour carries a `file:line` that resolves**, and planning
does not begin until the CURRENT behaviour is named with its `file:line`.

**A plan is an instruction to an executor, not a record of the thinking.** Rejected
alternatives are DELETED. **Tests are the plan** — on a known surface a test list replaces
prose.

**A plan FILE is owed by M and L, and by any S touching a hot path** (Review-gate list) —
unless the request says otherwise ("без плана", "just do it"). Every OTHER S states its
plan in THREE LINES in the chat before the first edit: intent · files · done-when.

**A plan is written FOR A COLD SESSION** — nothing in it may resolve through this chat.

## Review gate

Self-initiate `/review` — never wait to be asked, never auto-fix. Trigger when ANY holds:

- The change is **M or L**.
- New module / new parser param / new key or template command / new page format.
- **Hot-path touch regardless of diff size**: `gsconfig/gsparser.py`,
  `gsconfig/extractor.py`, `gsconfig/template/classes.py`, `gsconfig/template/constants.py`
  (the regexes), `gsconfig/__init__.py` (public API + version), `setup.py`,
  `.github/workflows/`, `examples/converter_test_cases.json`.
- User says "done", "ready", "push", "релиз", or asks for a commit — on an L branch, only
  for the LAST commit of `## Order`.

Flow: complete work → `/review` → findings + fix plan → wait for approval → only then fix.

**Decision-pinning check** during review (`documentation.md`).

## Self-review (M and L; on S only if the diff surprised you)

1. `git diff --stat` — only expected files changed.
2. Full diff — incomplete guards, duplicated literals, params-dict drift between
   `ConfigJSONConverter.default_params`, `Document._init_common` and the docs.
3. Grep old names after renames — including `docs/`, `docs_ru/`, `examples/*.ipynb`.
4. Walk a cell through the affected path: sheet row → `Page.get` → `Extractor` →
   `jsonify` → `Template.render`, under `v1` AND `v2`.
5. Tests last.

## Error recovery — escalate per failed attempt

1. **Retry** — re-read the error; check types/imports/signatures. Max 3.
2. **Instrument** — print the intermediate split/blocks, reproduce, read actual output. Max 2.
3. **Pivot** — step back; propose a simpler approach. Do NOT implement without approval.
   Past attempt 3, re-approach from a FRESH context (a subagent given the symptom and the
   file paths, not the transcript), carrying only the list of falsified hypotheses.
4. **Stop** — write up tried/observed/hypotheses to `lessons/`, ask for guidance.

## Hard rules (non-negotiable)

- **Existing sheets and templates are the contract.** Game-design spreadsheets and
  `.template` files the repo cannot see are parsed by this library. A change to what an
  EXISTING input produces — a cell string's JSON, a template's rendered text, a default
  param, a parser-version semantic — is breaking. It stops and asks, and if approved it is
  a `feat!:`/`BREAKING CHANGE` for `/release`. New syntax is additive or it is opt-in (a
  new param, a new command, a new parser version).
- **Local tree vs installed package.** `import gsconfig` in a notebook or a user's shell
  may resolve to a pip-installed copy, not this tree. Before trusting an observation, print
  `gsconfig.__file__`. Tests pin the tree via `tests/conftest.py`.
- **Credentials are never asked for first.** gspread looks in `~/.config/gspread/`
  (`credentials.json`, `authorized_user.json`) or a service-account keyfile passed to
  `GoogleOauth`. Check there; only a secret absent from all of them is worth asking for —
  name where you looked. Never commit a token (`google_oauth2_token.json` is ignored).
- **Impact assessment**: ask how a change affects the converter, the extractor schemas,
  the template engine, the public API and `docs/` (EN) + `docs_ru/` (RU) before implementing.
- **Debugging intake (meta-rule)** — on any bug report, in order:
  1. `git status` first: in-flight changes ARE the running code.
  2. Vague report ("не работает / пусто / криво парсит") → ask ONE batched question for
     the exact cell string or template snippet, the params (`parser_version`, schema,
     separators), expected vs actual output, regression-vs-never-worked.
  3. Name your #1 hypothesis AND its falsifier; drop it when an observation falsifies it.
  4. "Key missing / page skipped" = a gating condition (`key_skip_letters`,
     `page_skip_letters`, page-title format suffix, schema detection) — one grep first.
  5. Glance at `lessons/INDEX.md`.
  6. **Observe before patch**: reproduce with the exact input string before any fix.
  7. **Fix #2 in the same area normalizes the class** — if the breaking inputs have more
     than two members, the fix is a projection over them, not another `if`.
- **Subagent dispatches** (Agent tool) follow `subagent-contract.md`.
- **Cheap gates run BEFORE the commit**: `.claude/scripts/pre-commit-gates.sh`, run
  **UNPIPED** (`gates | tail -2 && git commit` ships a red gate).

## Auto-lessons

**A lesson is written only when something WENT WRONG.** Create
`lessons/YYYY-MM-DD-short-slug.md` when ANY holds: 3+ fix iterations on the same issue
category; a released defect (reached a `v*` tag past a green `/review`) — name which check
missed it; a wrong hypothesis that cost real time; the user explicitly asks for one.

NOT triggers: a new pattern, a clean feature, a workflow tweak, a first-try fix.

Structure: frontmatter (`category:`, `systems:`) · What happened · Root cause · Actionable
rule · Code example (wrong vs right). Regenerate: `python3 .claude/scripts/lessons-index.py --write`.

A lesson is a staging area; its endpoint is a rule or an in-code marker. **No edit to
`CLAUDE.md`, `RULES.md`, `.claude/rules{,-scoped}/**` or `.claude/skills/**` without an
`Observation / Rule / File` block whose Observation is verbatim output from the current
session** (`/retro` §3a). No evidence ⇒ propose the edit and stop.
