#!/usr/bin/env python3
"""Claude Code hook dispatcher — Bash guards, scoped-rule reminders, commit gates.

Reads the hook payload as JSON on stdin (the Claude Code hook contract: `tool_name`,
`tool_input`, `session_id`). Modes, one per settings.json entry:

  pre-bash    block destructive commands; warn on a tag push (publishes to PyPI); run
              pre-commit-gates.sh before `git commit`
  pre-edit    once per session per rule file: point at the matching .claude/rules-scoped/
  post-bash   after `git commit`: the /retro trigger reminder
  post-edit   a plan written under plans/: run plan-shape-gate.py on it

INVARIANT: a block exits 2 with the reason on stderr; everything else exits 0.
Why: Claude Code treats exit 2 as "block and show stderr to the model"; exit 1 is a
non-blocking error, so a guard that exits 1 lets the command run anyway.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

BLOCKS = [
    (re.compile(r"\brm\s+-[a-zA-Z]*(rf|fr)[a-zA-Z]*\b(?!\s+\S*(__pycache__|\.pytest_cache|build|dist)\b)"),
     "rm -rf is destructive. Use targeted removal."),
    (re.compile(r"\bgit\s+push\s+(-f|--force)\b.*\b(master|dev)\b|\bgit\s+push\b.*\+\S*(master|dev)\b"),
     "force push to master/dev."),
    (re.compile(r"\btwine\s+upload\b"),
     "manual PyPI upload — releases go through /release (tag push → CI publish)."),
]
TAG_PUSH = re.compile(r"\bgit\s+push\b.*(refs/tags/|--tags\b|\bv\d+\.\d+\.\d+\b)")
COMMIT = re.compile(r"\bgit\s+commit\b")

# path fragment → scoped rule files; first match wins.
SCOPED = [
    ("tests/", ["testing-ops.md"]),
    ("examples/converter_test_cases.json", ["converter.md", "testing-ops.md"]),
    ("gsconfig/gsparser.py", ["converter.md", "testing-ops.md"]),
    ("gsconfig/extractor.py", ["converter.md", "testing-ops.md"]),
    ("gsconfig/template/", ["template.md", "testing-ops.md"]),
    ("gsconfig/gsconfig.py", ["sheets.md"]),
    ("google apps script/", ["sheets.md"]),
    ("docs/release/", []),  # release notes: owned by /release, not the user manual
    ("docs/", ["docs.md"]),
    ("docs_ru/", ["docs.md"]),
    ("README.md", ["docs.md"]),
]


def message(text: str) -> None:
    print(json.dumps({"systemMessage": text}))


def block(reason: str) -> None:
    print(f"BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)


def pre_bash(cmd: str) -> None:
    for pattern, reason in BLOCKS:
        if pattern.search(cmd):
            block(reason)
    if TAG_PUSH.search(cmd):
        message("Pushing a v* tag publishes to PyPI (irreversible for that version). "
                "Only from /release §4, after the pre-flight and the version check.")
    if COMMIT.search(cmd):
        gates = subprocess.run(["bash", str(ROOT / ".claude/scripts/pre-commit-gates.sh")],
                               capture_output=True, text=True)
        if gates.returncode != 0:
            block("pre-commit gates fail. Fix, then commit:\n" + gates.stdout + gates.stderr)
        message("Review gate: if this change is M/L or a review-gate trigger fired (hot path, "
                "new module, user said done/push) - verify /review ran before committing; "
                "S-size quick fixes are exempt (workflow.md Phase 4).")


def pre_edit(path: str, session: str) -> None:
    rel = path.replace(str(ROOT) + "/", "")
    rules = next((r for frag, r in SCOPED if frag in rel), None)
    if not rules:
        return
    marker = Path(tempfile.gettempdir()) / f".gsconfig-rules-{session}-{'-'.join(rules)}"
    if marker.exists():
        return
    marker.touch()
    message(f"Path-scoped rules apply - READ .claude/rules-scoped/: {' '.join(rules)} "
            "(reminder fires once per session).")


def post_bash(cmd: str) -> None:
    if COMMIT.search(cmd):
        message("Commit done. Run /retro ONLY if a workflow.md Auto-lessons trigger fired this "
                "session (3+ fix iterations on one category / a released defect past a green "
                "review / a wrong hypothesis that cost real time / the user asked). A clean "
                "feature is NOT a trigger - skip.")


def post_edit(path: str) -> None:
    p = Path(path)
    if p.suffix != ".md" or "plans" not in p.parts or {"archive", "superseded"} & set(p.parts):
        return
    shape = subprocess.run([sys.executable, str(ROOT / ".claude/scripts/plan-shape-gate.py"), str(p)],
                           capture_output=True, text=True)
    if shape.returncode != 0:
        message("Plan is OFF-SHAPE - /implement will refuse it. Rewrite (do not append):\n"
                + shape.stdout.strip())


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") or {}
    cmd = tool_input.get("command", "")
    path = tool_input.get("file_path", "")
    session = payload.get("session_id", "nosession")
    handlers = {
        "pre-bash": lambda: pre_bash(cmd),
        "pre-edit": lambda: pre_edit(path, session),
        "post-bash": lambda: post_bash(cmd),
        "post-edit": lambda: post_edit(path),
    }
    if mode in handlers:
        handlers[mode]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
