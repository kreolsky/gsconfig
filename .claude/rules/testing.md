# Testing

* Write tests before business logic when feasible (the TDD cycle is in `workflow.md`).
* Never modify an existing test — or a golden case in `examples/converter_test_cases.json`
  — to make failing code pass. A golden case that is genuinely wrong is a product decision:
  stop and ask; if approved, it is a breaking change (`workflow.md` → Hard rules).
* Commands and environment → `.claude/rules-scoped/testing-ops.md`.

## After a run: propose, don't ask

Close a run that ends in observations with a SHORT plan — what gets fixed, in what order —
and start it. **A bug found by a run is fixed, always**, unless the fix changes what an
existing cell or template produces; those stop with a recommendation.
**Say what was NOT proven**: a parser version you did not run, a schema you did not
build a page for, a live-sheet path you could not reach.

## Reports are user scenarios, not a changelog of the code

State what a game designer or a library user can now do, or no longer gets wrong.

* **Wrong**: "`split_string_by_sep` now tracks bracket depth, `_prepare_to_parser` wraps."
* **Right**: "A cell like `a = {x = 1, y = 2} | b = 3` now splits into two blocks instead of
  cutting inside the braces; a key with `!list` on a complex-schema page is wrapped again."

## A green test is not evidence — bind the contract, not your own assumption

* **Assert over the DERIVED source, not a literal.** Walk the real registry
  (`ConfigJSONConverter.AVAILABLE_VERSIONS`, `Template.DEFAULT_KEY_COMMAND_HANDLERS`,
  `Extractor().extractors`) so the next member is covered automatically.
* **Compare JSON through `json.dumps`**, not `==` on Python objects: `1 == 1.0` and dict
  order are exactly what the game sees differently.
* **Every parser test runs under BOTH `v1` and `v2`** unless it is about the difference.
* **Test the input that must be REFUSED** — an unknown parser version, an unknown format,
  an unbalanced bracket — not only the one that passes.
* **A test with no failing branch is not a test.**
* **A test that must change when the implementation changes is testing PAST the
  interface.** The interface is `jsonify`, `Extractor.get`, `Template.render`, the public
  classes — not `BlockParser` internals or regex constants.
