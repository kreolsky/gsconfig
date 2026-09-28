#!/usr/bin/env python3
"""Release pre-flight: the read-only checks the release skill runs before tagging.

Each check prints STOP (blocks the release), WARN (needs a line in the release note)
or ok. The version LEVEL, the note text and the push stay the operator's call — this
only gathers the evidence they are decided from, against the repo, never memory.

A release of this library = `__version__` in `gsconfig/__init__.py` (read by setup.py)
+ annotated tag `vX.Y.Z` on the same SHA + fast-forward `master`. The tag push is what
triggers the PyPI publish workflow, so a tag whose version disagrees with `__version__`
would publish a package under the wrong number — hence the version checks here.

Usage: release-audit.py [--fetch]      (--fetch runs `git fetch origin --tags` first)
Exit 1 if any check is STOP.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
NOTES = ROOT / "docs" / "release"
VERSION_FILE = "gsconfig/__init__.py"
DEPS_FILE = "setup.py"
BASE, TARGET = "origin/dev", "origin/master"
SUBJECT_TYPE = re.compile(r"^([a-z]+)(\([^)]*\))?(!)?:")
VERSION_RE = re.compile(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", re.M)
PUBLIC_RE = re.compile(r"^from \S+ import (\S+)(?: as (\S+))?$|^from \. import (\S+)$", re.M)

stops = 0


def git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout.strip()


def report(level: str, title: str, body: str = "") -> None:
    global stops
    stops += level == "stop"
    print(f"{ {'stop': 'STOP', 'warn': 'WARN', 'ok': '  ok'}[level] }  {title}")
    for line in body.splitlines():
        print(f"        {line}")


def last_tag() -> str | None:
    """Newest v-tag reachable from origin/dev; None before the first release."""
    return git("describe", "--tags", "--abbrev=0", "--match", "v*", BASE) or None


def check_fast_forward() -> None:
    extra = git("log", f"{BASE}..{TARGET}", "--oneline")
    if extra:
        return report("stop", "fast-forward impossible — origin/master has commits origin/dev lacks",
                      extra + "\nHalt and ask the operator. Never --force.")
    n = len(git("log", f"{TARGET}..{BASE}", "--oneline").splitlines())
    report("ok", f"fast-forward clean — {n} commits ahead of master "
                 f"(dev={git('rev-parse', '--short', BASE)})")


def check_local_in_sync() -> None:
    if git("rev-parse", "HEAD") != git("rev-parse", BASE):
        return report("stop", "local HEAD is not origin/dev — push dev (or pull) before releasing")
    report("ok", "local HEAD == origin/dev")


def check_commit_types(since: str | None) -> None:
    rev = f"{since}..{BASE}" if since else BASE
    counts: dict[str, int] = {}
    breaking = False
    for sha in git("rev-list", "--no-merges", rev).splitlines():
        subject, _, body = git("show", "-s", "--format=%s%n%b", sha).partition("\n")
        m = SUBJECT_TYPE.match(subject)
        kind = m.group(1) if m else "other"
        counts[kind] = counts.get(kind, 0) + 1
        breaking |= bool(m and m.group(3)) or "BREAKING CHANGE" in body
    level = "major" if breaking else "minor" if counts.get("feat") else "patch"
    summary = ", ".join(f"{k}×{v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
    report("ok", f"since {since or 'the first commit'}: {summary} → recommended level: {level}"
                 + (" (BREAKING CHANGE present)" if breaking else ""))


def check_version(since: str | None) -> None:
    m = VERSION_RE.search(git("show", f"{BASE}:{VERSION_FILE}"))
    current = m.group(1) if m else None
    if not current:
        return report("stop", f"no __version__ in {VERSION_FILE} on origin/dev — setup.py cannot build")
    published = since[1:] if since else None
    if published and current == published:
        return report("ok", f"__version__ = {current} == last tag — bump it in the release-note commit")
    report("warn", f"__version__ = {current} already differs from the last tag ({since or 'none'}) — "
                   "confirm it is the version being released, not a stray bump")


def exports(source: str) -> set[str]:
    """Public names re-exported by gsconfig/__init__.py."""
    return {m[1] or m[0] or m[2] for m in PUBLIC_RE.findall(source)}


def check_public_api(since: str | None) -> None:
    if not since:
        return report("ok", "first release — no public-API diff to compute")
    removed = sorted(exports(git("show", f"{since}:{VERSION_FILE}"))
                     - exports(git("show", f"{BASE}:{VERSION_FILE}")))
    if removed:
        return report("warn", "names dropped from `gsconfig` since the last tag — a major bump:",
                      "\n".join(removed))
    report("ok", "no public name dropped from `gsconfig`")


def check_deps(since: str | None) -> None:
    if not since:
        return report("ok", "first release — no dependency diff to compute")
    if git("diff", "--name-only", f"{since}..{BASE}", "--", DEPS_FILE):
        return report("warn", "setup.py changed since the last tag — name install_requires / "
                              "python_requires changes in the note")
    report("ok", "setup.py unchanged")


def check_newest_note() -> None:
    notes = sorted(NOTES.glob("release-*.md")) if NOTES.is_dir() else []
    if not notes:
        return report("warn", "no release note yet — write docs/release/release-YYYY-MM-DD-vX.Y.Z.md")
    report("ok", f"newest note: {notes[-1].name} — {notes[-1].read_text(encoding='utf-8').splitlines()[0]}")


def main() -> int:
    if "--fetch" in sys.argv:
        subprocess.run(["git", "-C", str(ROOT), "fetch", "origin", "--tags", "--quiet"], check=True)
    dirty = git("status", "--porcelain", "--untracked-files=no")
    report("warn" if dirty else "ok", "tracked working-tree changes present (not part of the release)"
           if dirty else "no tracked working-tree changes", dirty)
    since = last_tag()
    print(f"        last tag: {since or 'none (first release)'}")
    check_fast_forward()
    check_local_in_sync()
    check_commit_types(since)
    check_version(since)
    check_public_api(since)
    check_deps(since)
    check_newest_note()
    return 1 if stops else 0


if __name__ == "__main__":
    sys.exit(main())
