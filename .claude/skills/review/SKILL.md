---
name: review
description: Post-implementation self-review. Ревью кода, ревью изменений, code review, проверка, самопроверка после реализации.
---

# Post-Implementation Self-Review

Phase 4. The trigger list, the self-review checklist and the decision-pinning check live in
`.claude/rules/workflow.md` and `.claude/rules/documentation.md`. **Never auto-fix** —
present findings + a fix plan, wait for approval.

## 1. Workflow compliance

```
━━━ WORKFLOW COMPLIANCE ━━━
TDD:         [PASS / VIOLATION — tests after impl, or missing for new endpoints]
Checklist:   [PASS / SKIPPED — reason / N/A]   (.claude/rules-scoped/integration.md)
Doc markers: [PASS / MISSING — list]           (ARCH on boundaries, INVARIANT+Why, module docstrings)
Acceptance:  [PASS — live-drive evidence exists / VIOLATION — no live observation / EXEMPT — no runtime surface]
Gates:       [pre-commit-gates.sh output]
```

`Acceptance` per `workflow.md` Phase 4: a diff touching `gsconfig/` needs an end-to-end
drive on real input — converter diffs show `jsonify` of the affected cell strings under BOTH
`v1` and `v2`, template diffs show the render of the affected `examples/templates/`, a
high-entanglement diff shows the before/after render diff of every template,
`sheets-access` diffs show a live-sheet run — output captured verbatim. tests/docs-only
diffs are EXEMPT and say so.

## 2. Diff review

`git diff --stat` (only the intended files) → read the full diff for incomplete guards,
duplicated literals, params drift (`ConfigJSONConverter.default_params` ⇄ class docstring ⇄
`docs/{03,09}-*` + `docs_ru/{03,09}-*`) → grep old identifiers after any rename across `gsconfig/`,
`tests/`, `examples/` (notebooks), `docs/`, `docs_ru/`.

## 3. Architecture conformance

Align with `CLAUDE.md` and `coding-constraints.md`: **backward compatibility first** —
does any EXISTING cell string or template render differently? (yes ⇒ breaking; flag it,
it needs an explicit ruling and a `feat!:`). Both parser versions handled. Extension via
the registries, not a new `if`. Public API unchanged, or aliased and noted. Bad input
raises with the offending text. New dependency declared in `setup.py`. `docs/` and
`docs_ru/` updated together for any user-visible change. New comments in English.

## 4. Decision-pinning check

Per `documentation.md`: a bugfix in a repeatedly-regressing area must add or tighten an
`INVARIANT:` / `ARCH:` / `WHY:` with a `Why:`. Flag any new `INVARIANT:` lacking a `Why:`,
and any marker contradicting the user's latest stated rule. A new marker that met no pin
trigger is flagged as noise to drop, not kept as harmless.

## 5. Tests & gates

New or changed logic has tests in `tests/`. Run the breadth the entanglement table demands,
then `.claude/scripts/pre-commit-gates.sh` **unpiped**.

## 6. Receiving findings — verify before implementing

Applies to findings from ANY source that is not this session's own diff read: `/code-review`,
`ultra`, a subagent reviewer, the user relaying someone else's report. A finding is a
hypothesis about this codebase, not an instruction.

- **Check it against the code before touching anything**: does the claimed path exist, is the
  current shape deliberate (`INVARIANT:` / `WHY:` / `DEBT:` on the line), does the suggestion
  break a caller. A finding that survives none of these is answered with technical reasoning,
  not implemented.
- **Unclear on ANY item ⇒ implement NONE of them yet.** Items in one review interact; doing
  the understood four and asking about the fifth bakes in an ordering nobody chose.
- **Push back in the same card.** Rejecting a finding is a normal outcome and belongs in
  **Residual** with its reason — silently dropping it reads as agreement.

## 7. Summary — card form (`subagent-contract.md`)

**What moved** · **Evidence** (checks actually run, output verbatim) · **Residual**
(findings + fix plan, awaiting approval) · **Outside scope**. Wait for approval.

## 8. On an L branch — record the tip that was reviewed

Only after the findings are approved and any fix has landed, and only on a feature branch:

```bash
git rev-parse HEAD > "$(git rev-parse --git-dir)/review-ok"
```

`merge-audit.py` compares that SHA to the branch tip, so a commit added afterwards
invalidates the review instead of riding in under it. Never write it ahead of approval —
the file is the claim that this exact tip was reviewed.
