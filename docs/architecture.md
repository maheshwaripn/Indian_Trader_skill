# Architecture, scope and roadmap

## v0.1 architecture

Portable AI instructions call a single Python CLI. `core.py` validates and normalises inputs; `bank.py` stores content-addressed raw snapshots with SQLite metadata; `universe.py` audits membership; `research.py` runs explicit reference strategies; `paper.py` records manual simulated fills; `report.py` produces HTML and compact evidence. Optional provider utilities are separated in `providers.py`.

Every research run stores version, data hash, parameters, creation time, mode, elapsed time and zero AI calls. The core never reads AI or broker credentials. It does not use a broker SDK or submit orders. The dashboard is a report, not an order control surface.

## Current limitations

- Equal-cash sleeves rather than a full dynamic portfolio engine.
- No automatic PIT membership integration or symbol-master reconciliation.
- No adjusted-price/corporate-action engine, exchange-calendar validation or delisted-data recovery.
- No parameter-search or formal walk-forward runner.
- No live broker adapter, automatic paper fill simulation or background data ingestion service.
- Profiles enforce rows/brief limits only; no OS memory scheduler or AI API budget governor.
- Broker/network integrations and every AI surface are not end-to-end tested.
- HTML metrics are a research foundation, not a complete institutional risk dashboard.

## Planned releases and acceptance gates

| Release | Scope | Gate |
|---|---|---|
| 0.1 | Local core, reference engines, manual paper accounting, reports and detailed guides | Offline correctness tests and reproducible demo |
| 0.2 | Reconciled PIT data, instrument mappings, calendar/adjustments, provider adapters | Dated fixtures, provenance, entitlement-aware live read-only tests |
| 0.3 | Portfolio engine, benchmark reporting, walk-forward experiments, data-health dashboard | Leakage, accounting, stress and out-of-sample protocol tests |
| 0.4 | Managed VPS scheduling, incremental updates, budgeted AI integration | Resume/retry/locking/budget and privacy tests |
| Separate execution extension | Dhan then Zerodha, followed by other brokers | Simulation, reconciliation, current requirements and explicit user activation |

The repository should remain usable as a Python package without any AI provider. Documentation-only capabilities must never be presented as implemented commands. New skills should call established code rather than generating their own untested arithmetic.

## Change control

Record what changed, why, evidence, expected impact, new risks and validation. Version strategy rules independently when semantics change. Keep old run results immutable. Fail a run on invalid required inputs rather than producing partial results labelled complete.
