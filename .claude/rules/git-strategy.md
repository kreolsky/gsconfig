---
alwaysApply: true
---

# Git Strategy

* **Branch First (large only)**: S and M go straight to `dev`. Create a feature branch from
  `dev` only for L: work whose plan's `## Order` carries 2+ commits (`workflow.md`). Never
  work directly on `master`.
* **A feature branch may be red between commits**; only its tip, before the merge, must be
  green.
* **Base branch**: `dev`. `master` is what was released. (`develop`, `deprecated`, `lite`
  are legacy branches — never a base, never deleted without an explicit ask.)
* **Pre-merge audit**: `/merge` (`merge-audit.py`), then explicit confirmation.
* **Release**: only via `/release`, only when the user asks. It tags `vX.Y.Z` and
  fast-forwards `master` (`git push origin <sha>:refs/heads/master`). The tag push is what
  publishes to PyPI (`.github/workflows/publish-to-pypi.yml`) — a tag is irreversible in
  practice, since PyPI never accepts the same version twice. Never create a local merge
  commit on `master`.
* **Clean up**: delete feature branches after merge into `dev`, on an explicit yes.
* **Foreign working-tree changes stay untouched.** Never revert, stash, `git checkout --`,
  reformat or commit edits that are not yours (`.kilo/`, notebooks with fresh outputs,
  `dist/`, `build/`). If one blocks you, say so and ask.
* **The commit carries the plan it was written from** — the `plans/` file is staged in the
  SAME commit as the code (on an L, with the first commit of `## Order`).
* **Commit messages are English-only — subject AND body**, including when the chat is in
  Russian. Conventional-commit form: `feat(converter): …`, `fix(template): …`,
  `docs(ru): …`, `chore(harness): …`. `type!:` or a `BREAKING CHANGE` body marks a change
  to what existing sheets/templates produce (`/release` reads it).
