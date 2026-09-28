#!/usr/bin/env python3
"""Cyrillic gate — no NEW untranslated prose in gsconfig/, none at all in release notes.

New and changed code comments and docstrings are written in English. The library predates
that rule and carries Russian docstrings throughout, so `gsconfig/` is zero-net-growth
per file against `.claude/baselines/cyrillic.json`: a file may shrink its Cyrillic line
count (translating on touch), never grow it. Release notes (`docs/release/`) are strict —
any Cyrillic line fails. User docs in `docs_ru/` are Russian by design and never scanned.

Usage:
  cyrillic-src-gate.py            # exit 1 on growth in gsconfig/ or any hit in docs/release/
  cyrillic-src-gate.py --update   # rewrite the gsconfig/ baseline with the current counts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from marker_checks import iter_files  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
CODE_DIR = ROOT / "gsconfig"
STRICT_DIR = ROOT / "docs" / "release"
BASELINE = ROOT / ".claude" / "baselines" / "cyrillic.json"


def _cyrillic_lines(path: Path) -> list[int]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    return [n for n, line in enumerate(lines, 1) if any("Ѐ" <= ch <= "ӿ" for ch in line)]


def count_code() -> dict[str, int]:
    counts = {}
    for path in iter_files(CODE_DIR, (".py",)):
        n = len(_cyrillic_lines(path))
        if n:
            counts[str(path.relative_to(ROOT))] = n
    return counts


def main() -> int:
    counts = count_code()
    if "--update" in sys.argv:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"cyrillic-gate: baseline updated → {sum(counts.values())} lines in {len(counts)} files")
        return 0

    rc = 0
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
    grown = {f: (n, baseline.get(f, 0)) for f, n in counts.items() if n > baseline.get(f, 0)}
    if grown:
        rc = 1
        print("Cyrillic GREW in gsconfig/ — write new comments/docstrings in English:")
        for f, (now, base) in sorted(grown.items()):
            print(f"  {f}: {base} → {now}")
    strict = [f"{p.relative_to(ROOT)}:{n}" for p in iter_files(STRICT_DIR, (".md",))
              for n in _cyrillic_lines(p)]
    if strict:
        rc = 1
        print("Cyrillic in docs/release/ — release notes are English-only:")
        for hit in strict:
            print(f"  {hit}")
    if rc == 0:
        print(f"OK — no Cyrillic growth ({sum(counts.values())} grandfathered lines).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
