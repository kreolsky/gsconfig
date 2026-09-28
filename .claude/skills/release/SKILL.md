---
name: release
description: Bump the version, tag vX.Y.Z, fast-forward dev into master and publish gsconfig to PyPI. Релиз, выпусти версию, опубликуй в PyPI, мерж dev в master, новая версия, bump version, release, publish.
---

# Release — `__version__` bump, tag `vX.Y.Z`, fast-forward `dev` → `master`

A release = version bump + release note on `dev` + annotated tag `vX.Y.Z` on that SHA +
fast-forward of `origin/master`. **Pushing the tag publishes to PyPI**
(`.github/workflows/publish-to-pypi.yml`), and PyPI never accepts the same version twice —
the tag push is the point of no return.

**Invoking this skill IS the operator's go-ahead for the tag and both pushes.** The
operator is asked exactly one thing, the version level (§2). The only other halts: a `STOP`
from the pre-flight, a red suite, a `WARN` whose decision cannot be made from the tree.

## 1. Pre-flight

```bash
git push origin dev                                  # the audit reads origin/dev
python3 .claude/scripts/release-audit.py --fetch     # STOP => exit 1, blocks the release
<py> -m pytest tests/ -q                             # interpreter per run-tests §1
```

Read-only checks: fast-forward possible, local `HEAD == origin/dev`, commit types since
the last tag + recommended level, `__version__` vs the last tag, public names dropped from
`gsconfig/__init__.py`, `setup.py` changes, the newest note. Each `WARN` gets a line in the
note. A non-ff `master` → halt and ask; never `--force`.

## 2. Version (ask the operator)

`vMAJOR.MINOR.PATCH`; the tree carries it once, `__version__` in `gsconfig/__init__.py`
(`setup.py` reads it). Recommendation by **presence** since the last tag: `BREAKING
CHANGE` / `type!:` or a dropped public name → major; any `feat` → minor; else patch. Major
= an existing spreadsheet, template or user script produces something different or breaks.
While the version is `0.x`, a breaking change bumps MINOR — say so in the note.

Ask with `AskUserQuestion`, recommended level FIRST, each option with its evidence. Do not
tag yet.

## 3. Version bump + release note (one commit on `dev`)

- `__version__ = 'X.Y.Z'` in `gsconfig/__init__.py`.
- `docs/release/release-YYYY-MM-DD-vX.Y.Z.md`, **English only** (`cyrillic-src-gate.py`
  blocks Cyrillic in `docs/release/`); H1 `# Release vX.Y.Z — YYYY-MM-DD`; shaped like the
  newest existing note.
  - One-paragraph summary: commit count since the previous tag + the headline theme.
  - Changes by theme, written as what a game designer or library user can now do
    (`.claude/rules/testing.md` → *Reports are user scenarios*), never a raw log.
  - `# Upgrade actions` (mandatory): changed params/defaults, changed parse or render
    output for existing input, new/removed public names, dependency or Python-floor changes.
  - `# Known limitations` when by-design caveats ship.

`.claude/scripts/pre-commit-gates.sh` (unpiped), then commit
`chore(release): vX.Y.Z` and `git push origin dev`.

## 4. Tag and fast-forward

Push both by the SHA of the audited `origin/dev`, never by a local branch name.

```bash
git fetch origin
REL=$(git rev-parse origin/dev)
test -z "$(git log origin/dev..origin/master --oneline)"   # still a fast-forward
VER=vX.Y.Z                                                 # the level chosen in §2
git show "$REL:gsconfig/__init__.py" | grep -q "__version__ = '${VER#v}'"   # tag == package version
git tag -a "$VER" "$REL" -m "Release $VER — $(date +%F)

See docs/release/release-$(date +%F)-$VER.md"
git push origin "$REL:refs/heads/master"
git push origin "refs/tags/$VER"                           # triggers the PyPI publish
git rev-parse "$VER^{}" origin/master                      # both lines are $REL
```

## 5. Output

Version (and any overridden recommendation), note path, commit count, the new
`origin/master` SHA, and the publish run: `gh run list --workflow publish-to-pypi.yml -L 1`.
A failed publish is reported with its log — the tag stays; the fix ships as the next patch.
