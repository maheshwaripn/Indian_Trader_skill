# Changelog

## 0.2.0 — 2026-11-08

Fixes: the ORB engine skips incomplete or special sessions instead of rejecting the whole file (`--strict-sessions` keeps the old behaviour); the data bank stores relative paths so a moved workspace still verifies (v0.1 catalogues are still read); `convert-bhavcopy` reads NSE's UDiFF layout and merges several days.

Added: dated Indian cost model for delivery, intraday, futures and options with broker presets (`--costs india` is now the default; `--costs bps` keeps the flat fee) and `cost-calc`; `--cost-stress`; futures mode with dated lot sizes and margin; membership filter (`--universe`); date windows and random-entry runs in `research`; `evaluate` (development and validation, buy-and-hold, random-entry null, cost stress, bootstrap of R, pass/fail checks) and `sweep` (all settings, plateau ranking, reality check); results in R; suspected split/bonus detection that stops a run unless allowed; NSE 2026 calendar and `calendar-check`; adjustment state in the bank; paper ledger in integer paise with fill times, `--auto-fee` and `paper-mark`; faster CSV reading with PyArrow; research-protocol and costs skills; ruff in CI.

Changed results: the demo now ends at INR 99,134.20 instead of 99,656.08 because Indian charges replace the flat 10 bps.

## Maintenance — 2026-11-07

Close SQLite connections deterministically after both committed and rolled-back transactions, including schema failures. Fixes Windows CI cleanup failures caused by open database handles. Add four connection-lifecycle regression tests; run documentation checks with explicit UTF-8 decoding in CI and let all matrix jobs finish independently.

## 0.1.0 — 2026-11-06

Initial educational research release: offline-first CLI, strict canonical OHLCV validation, content-addressed data catalogue, NiftyHistory transition audit, daily trend and five-minute ORB reference engines, manual paper ledger, HTML dashboard and bounded evidence briefs. Includes four resource presets, portable AI workflows, and detailed installation, data, broker, VPS, metric and risk documentation.

No live routing. NiftyHistory raw data is excluded pending redistribution rights. Optional network integrations remain unverified against authenticated/live accounts.
