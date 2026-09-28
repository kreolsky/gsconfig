# Integration protocol (Phase 1 — L, or any feature touching 3+ systems)

Before implementing:

1. Read `CLAUDE.md` — identify the affected systems.
2. Find them in `SYSTEMS.md`, then `grep -rn "SYSTEM:" gsconfig/` and READ each entry file.
3. `grep -rnE "(ARCH|INVARIANT|WHY|DEBT):" gsconfig/` in the affected areas.
4. Name, in one line each, what the change looks like at: **sheets-access** (Page/Document
   params), **extractor** (schemas, formats), **converter** (grammar, v1 vs v2),
   **template** (syntax, commands), **public API** (`__init__.py`, docs 09), **docs**
   (`docs` + `docs_ru`) — or why a layer is N/A.
5. Is it additive for existing sheets/templates? If not — stop, it is a breaking change.

Output the filled list. Skip reasons are part of the output, not an omission.
