# Changelog

## Maintenance — 2026-11-07

Close SQLite connections deterministically after both committed and rolled-back transactions, including schema failures. Fixes Windows CI cleanup failures caused by open database handles. Add four connection-lifecycle regression tests; run documentation checks with explicit UTF-8 decoding in CI and let all matrix jobs finish independently.

## 0.1.0 — 2026-11-06

Initial educational research release: offline-first CLI, strict canonical OHLCV validation, content-addressed data catalogue, NiftyHistory transition audit, daily trend and five-minute ORB reference engines, manual paper ledger, HTML dashboard and bounded evidence briefs. Includes four resource presets, portable AI workflows, and detailed installation, data, broker, VPS, metric and risk documentation.

No live routing. NiftyHistory raw data is excluded pending redistribution rights. Optional network integrations remain unverified against authenticated/live accounts.
