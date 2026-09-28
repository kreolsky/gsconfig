# User docs — `docs/**`, `docs_ru/**`, `README.md`

* `docs/NN-*.md` and `docs_ru/NN-*.md` are one document in two languages: same file
  numbers, same section order, same examples. An edit to one is mirrored in the other in
  the SAME commit; a Russian-only fix is not "done".
* Examples in the docs are executable claims: a changed example is run through the
  end-to-end drive (`testing-ops.md`) and the doc shows the real output.
* `09-api-reference` lists the public surface (`coding-constraints.md`); a public name
  added or removed there matches `gsconfig/__init__.py`.
* The root `README.md` is a short English landing page linking into both trees.
