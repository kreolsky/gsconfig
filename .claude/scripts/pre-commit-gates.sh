#!/usr/bin/env bash
# Local mirror of every CHEAP structural gate — the ones needing no network and no Google
# credentials. The whole block runs in a couple of seconds, so there is no reason to
# discover these failures after a push.
#
# NOT covered here on purpose (that is what `/run-tests` is for): pytest.
#
# NOT here yet: ruff. The rule set is not pinned in the repo (the result depends on the
# runner's global config) and the tree carries ~48 findings; gating it would block every
# commit touching gsconfig/. Pin the rules + baseline first, then add it here.
#
# NOT here either: plan-shape. A plan is written in one session and executed in another,
# and it is normally still uncommitted when the implementation commit lands — gating the
# commit would block FINISHED work over a draft whose job is already done. Its enforcement
# points are the two moments where a reshape is still free: the Write|Edit hook
# (settings.json) and /implement's plan load.
#
# Usage: .claude/scripts/pre-commit-gates.sh
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

FAILED=()

run_gate() {
  local name="$1"; shift
  if "$@" >/tmp/gate-out.txt 2>&1; then
    printf '  ok    %s\n' "$name"
  else
    printf '  FAIL  %s\n' "$name"
    sed 's/^/        /' /tmp/gate-out.txt
    FAILED+=("$name")
  fi
}

echo "━━━ pre-commit gates ━━━"
run_gate "invariant-why"  python3 .claude/scripts/invariant-why-gate.py
run_gate "systems-index"  python3 .claude/scripts/systems-index.py --check
run_gate "func-length"    python3 .claude/scripts/func-length-gate.py
run_gate "debt-ledger"    python3 .claude/scripts/debt-gate.py
run_gate "cyrillic-src"   python3 .claude/scripts/cyrillic-src-gate.py


if [ ${#FAILED[@]} -gt 0 ]; then
  printf '\nBLOCKED — %d gate(s) failed: %s\n' "${#FAILED[@]}" "${FAILED[*]}"
  exit 1
fi
echo "All gates green."
