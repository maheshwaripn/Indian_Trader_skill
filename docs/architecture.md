# Architecture, scope and roadmap

## Architecture

Portable AI instructions call a single Python CLI. `core.py` validates and normalises inputs; `bank.py` stores content-addressed raw snapshots with SQLite metadata; `universe.py` audits membership; `research.py` runs explicit reference strategies with `costs.py` (dated Indian charges); `validation.py` adds windows, baselines, nulls, sweeps and the reality check; `calendar.py` holds the NSE calendar; `paper.py` records manual simulated fills; `report.py` produces HTML and compact evidence. Optional provider utilities are separated in `providers.py`.

Every research run stores version, data hash, parameters, creation time, mode, elapsed time and zero AI calls. The core never reads AI or broker credentials. It does not use a broker SDK or submit orders. The dashboard is a report, not an order control surface.

## Current limitations

- Equal-cash sleeves rather than a full dynamic portfolio engine; long only.
- Futures use one continuous price series per symbol: no roll costs, basis or contract-level data.
- Corporate actions are detected, not adjusted; delisted-price recovery is the user's data task.
- The bundled exchange calendar covers 2026; other years need a user calendar file.
- Membership filtering needs a reconciled, dated constituent file and exact symbol mapping.
- No live broker adapter, automatic paper fill simulation or background data ingestion service.
- Profiles enforce rows/brief limits only; large files hold every row in memory (about 1.4 KB a row measured).
- Broker/network integrations and every AI surface are not end-to-end tested.

## Planned releases and acceptance gates

| Release | Scope | Gate |
|---|---|---|
| 0.1 | Local core, reference engines, manual paper accounting, reports and detailed guides | Offline correctness tests and reproducible demo |
| 0.2 (released) | Dated Indian costs, UDiFF bhavcopy, NSE calendar, corporate-action checks, membership filter, futures lots, validation and sweep commands, portable bank, paise ledger | Offline tests for each; see validation.md |
| 0.2.x | Adjusted-price engine, contract-level futures, more calendar years, provider adapters | Dated fixtures, provenance, entitlement-aware live read-only tests |
| 0.3 | Portfolio engine, benchmark reporting, walk-forward experiments, data-health dashboard | Leakage, accounting, stress and out-of-sample protocol tests |
| 0.4 | Managed VPS scheduling, incremental updates, budgeted AI integration | Resume/retry/locking/budget and privacy tests |
| Separate execution extension | Dhan then Zerodha, followed by other brokers | Simulation, reconciliation, current requirements and explicit user activation |

The repository should remain usable as a Python package without any AI provider. Documentation-only capabilities must never be presented as implemented commands. New skills should call established code rather than generating their own untested arithmetic.

## Change control

Record what changed, why, evidence, expected impact, new risks and validation. Version strategy rules independently when semantics change. Keep old run results immutable. Fail a run on invalid required inputs rather than producing partial results labelled complete.
