# Point-in-time NIFTY membership

## Source and semantics

The repository owner's CSV came from https://niftyhistory.in/. The website describes dated inclusions and exclusions. The owner confirms these represent additions/removals from NIFTY 500. This clarifies event intent, but does not establish whether the `symbols` snapshots use historical or subsequently normalised ticker identities.

The source website and archive were reviewed on 2026-11-06. They state “All rights reserved”; a public redistribution licence was not established. We therefore provide source attribution, an importer and audit findings, **not the downloaded CSV**. Download your own permitted copy. Do not place source data under the software MIT licence. If the source grants written redistribution permission, preserve it before adding a public fixture.

## Audit of the owner-supplied file

- Filename: `nifty500_1991-01-01_to_2026-12-31.csv`.
- SHA-256: `570e3305c981d068736e2e4a1506f28f928dddfb36ef6d1f48d0e9ad52ccec55`.
- 137 rows; actual effective dates 1998-01-08 through 2026-09-30.
- 500–501 unique symbols per snapshot; 49 snapshots contain 501.
- 114 of 136 transitions do not equal `(previous snapshot − exclusions) ∪ inclusions`.
- Publication timestamps and stable security identifiers are absent.

These are internal-consistency findings, not a claim that every flagged row is incorrect. Replacements, ticker aliases, temporary constituents or the source's snapshot semantics may explain some differences. Do not manufacture corrections.

## Run your own audit

```bash
indian-trader universe-audit path/to/download.csv --output workspace/universe-audit.json
indian-trader universe-asof path/to/download.csv --date 2020-06-01
```

Conflicting event/snapshot history blocks lookup by default. For clearly labelled exploratory work only:

```bash
indian-trader universe-asof path/to/download.csv --date 2020-06-01 --allow-unverified
```

This selects the latest snapshot effective on or before the date. It does not reconstruct an authoritative event ledger, check publication-time availability, or validate economic identity. Dates earlier than the first snapshot fail. Dates after the last snapshot carry `stale_possible=true`. No future membership is backfilled into earlier dates.

## Reconciliation workflow

1. Preserve the source unchanged and record its hash.
2. Compare each event against the prior snapshot; inspect mismatches.
3. Obtain official index notices or other authorised source evidence for disputed dates.
4. Maintain an alias table with stable instrument ID, source symbol, effective interval, evidence URL and verification status.
5. Distinguish a corporate rename from a replacement, merger, demerger or new security.
6. Apply documented transformations into a separate derived dataset; never edit raw history.
7. Re-run transition checks and manually examine a stratified sample of old/new dates.
8. Add publication timestamps if reconstructing what a trader could know before an effective date.

Recommended future record: `index_id,instrument_id,effective_from,effective_to,announced_at,source_url,retrieved_at,verification_status`. Interval end should be exclusive. Never assume an unknown announcement timestamp equals the effective date.

## Remaining survivorship risks

Membership alone does not supply delisted prices, terminal losses, suspended trading, corporate actions or historical liquidity. A backtest that silently drops missing former constituents remains biased. Report expected members, available members, excluded members and exclusion reasons for each period.

The current research engine does **not** apply this file automatically. Build and validate a dated research universe before supplying price extracts. Until integration and source reconciliation are complete, do not describe a result as survivorship-bias-free.
