# Sheets access — `gsconfig/gsconfig.py`, `google apps script/**`

Read before editing. Entry point: `SYSTEM: sheets-access`.

* **Network and credentials.** Everything here reaches Google through gspread. Auth:
  `GoogleOauth(keyfile=None)` → `gspread.oauth()` (`~/.config/gspread/credentials.json` +
  `authorized_user.json`); with a keyfile → service account via `oauth2client` (lazy,
  undeclared import). Check those paths before asking for credentials; never commit a token.
* **Read-only by default.** The library reads worksheets (`get_all_values`) and writes
  local files. Any code path that WRITES to a spreadsheet is a side effect outside the
  tree (`workflow.md` Phase 3) — never run it against a real document without an ask.
* **Caches**: `Page._cache` (worksheet values; `invalidate_cache()` resets),
  `GameConfigLite._cached_spreadsheet`, `GameConfig._cached_documents` (opened in a
  `ThreadPoolExecutor`, 5 workers). A fix to stale data is almost always one of these.
* **Skip letters**: pages whose title starts with `page_skip_letters` and keys starting
  with `key_skip_letters` (default `{'#', '.'}`) are not exported; `Document.pages` returns
  ALL pages, iteration returns only exported ones. The page format comes from the title
  suffix (`.json`, `.csv`, else `raw`).
* **Live drive**: `examples/game_config_live.ipynb` (or a 5-line script with the user's
  spreadsheet id) — the only acceptance for a change here. No spreadsheet id in the tree
  or the chat ⇒ ask for one; do not invent a mock and call it acceptance.
* **`google apps script/*.js`** runs inside Google Sheets, not in Python; it produces the
  trees the extractor reads. A change on either side of that boundary names the other.
