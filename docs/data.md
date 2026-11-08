# Choose a source and maintain your data bank

## Choose by purpose, not just price

| Source | Good starting use | Constraints |
|---|---|---|
| Existing CSV/Parquet | Reuse your own research history | Validate schema, timestamps, provenance and adjustments |
| Yahoo Finance | Exploratory daily research | Unofficial access, rate limits, symbol changes and missing delisted instruments |
| NSE bhavcopy | Exchange daily cash-market records | End-of-day only; formats change; observe download and reuse terms |
| Dhan/Zerodha | Entitled historical or live feeds | Authentication, subscriptions, rate limits, historical retention and account rules |
| Licensed vendor | Special history or coverage | Cost, permitted storage and redistribution restrictions |

The source chosen in `init` is a preference, not an automatic subscription or credential setup. Read the broker-specific guides before connecting. Do not scrape around access restrictions. Provider failures should produce missing-data status, not fabricated prices.

## Canonical schema

CSV and Parquet use exactly these required fields:

```csv
timestamp,symbol,open,high,low,close,volume
2024-01-02T09:15:00+05:30,DEMO_A,100,103,99,102,10000
```

`timestamp` is the **bar opening time** with an explicit offset. A daily cash-equity bar is stamped at 09:15 IST; a five-minute bar at 09:15 represents [09:15,09:20). Signals become available after the bar closes. Use only completed bars. `symbol` is a research identifier: maintain a separate dated instrument mapping rather than assuming `.NS` is a universal exchange ID. Prices must be finite and positive; volume nonnegative. Rows must increase within each symbol and duplicates are rejected. The engine normalises timestamps to UTC.

Dataset metadata should separately record interval, price adjustment, source, exchange, segment, acquisition time, session calendar, instrument mapping version and licence. Structural validation cannot infer these from seven columns. Mixing adjusted and raw series invalidates research even if validation passes.

## Import and audit

```bash
indian-trader validate my-prices.csv
indian-trader ingest my-prices.csv --name equities_daily --source "provider-name; daily; raw; personal-use"
indian-trader catalogue
indian-trader verify-bank
```

The importer copies a raw file into a SHA-256-addressed folder and adds an SQLite catalogue row. Re-importing identical content under the same name is idempotent. Changed content becomes a new version. The catalogue records acquisition time, structural coverage and the declared adjustment state. Snapshot paths are stored relative to the bank, so a workspace can be moved or copied and still verify; catalogues from v0.1 with absolute paths are still read. It does not automatically bless a correction.

## Daily maintenance procedure

1. Fetch a new complete period into a staging file, never directly over an old raw snapshot.
2. Validate it. Inspect gaps, timezone, zero volume, unexpected symbol changes, and corporate actions.
3. Compare overlapping dates with the previous version. If values disagree, retain both and investigate adjustment/source changes.
4. Import the new file with the same dataset name; a changed hash creates a new snapshot.
5. Record which snapshot your research used. `research` stores the input hash in its result.
6. Run `verify-bank`, back up the workspace, and periodically restore to a test directory.

The tool does not automatically repair gaps, fetch corporate actions or reconcile duplicate sources. These operations need an explicit reviewed transformation. No “last writer wins” merge is permitted by default.

## Yahoo daily example

```bash
python -m pip install -e ".[yahoo]"
indian-trader fetch-yahoo --symbol RELIANCE.NS --start 2024-01-01 --end 2025-01-01 --output workspace/reliance.csv
indian-trader validate workspace/reliance.csv
```

The end date is exclusive. Current-day bars are excluded. Output uses raw prices (`auto_adjust=False`); splits and other corporate actions must be handled before interpreting returns. This adapter is for daily Indian-equity exploration, not a live execution feed. Do not silently substitute it for a broker's live quotes. The optional integration was not network-tested for this release.

## NSE bhavcopy

Download your permitted daily archive from the official NSE reports area: https://www.nseindia.com/all-reports. Extract the CSV locally. The converter reads both the **legacy** layout (`SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TOTTRDQTY,TIMESTAMP`) and the **UDiFF** layout used since July 2024 (`BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv`: `TradDt, TckrSymb, SctySrs, OpnPric, HghPric, LwPric, ClsPric, TtlTradgVol`). It keeps one series (default `EQ`), and for UDiFF only stock rows (`FinInstrmTp` = `STK`). Several daily files can be merged in one call; rows are sorted by symbol and date.

```bash
indian-trader convert-bhavcopy BhavCopy_NSE_CM_0_0_0_2026110*_F_0000.csv --output workspace/nse-days.csv
```

Other layouts are rejected rather than guessed. Bhavcopy prices are **raw**: splits and bonuses are not adjusted (see below).

## Corporate actions and calendars

`validate` and `ingest` list `suspect_corporate_actions`: overnight moves where previous close / next open is near a common split or bonus ratio (2, 3, 4, 5, 10, 1.5, 4/3, 2.5) and the move is at least 25%. `research` stops on these unless `--allow-suspect-jumps`. Treat the list as evidence to check, not proof: a crash can match and an odd ratio can be missed. Record the adjustment state when ingesting: `ingest FILE --name N --source S --adjustment raw|adjusted|unknown`.

`calendar-check FILE` compares daily bars with the bundled NSE calendar (2026: holidays, the Budget Sunday session and the Muhurat session) and lists missing sessions and bars on closed days. Add more years with `--calendar FILE` in the same JSON shape as `src/indian_trader/data/nse_calendar_2026.json`. Dates outside every loaded calendar are not judged.

## Parquet

Install the optional extra and pass a single canonical file to the same commands. A large partitioned lake should be queried into a bounded research extract first. v0.1 does not recursively load an entire directory. Record the query and all source hashes. Prefer partition pruning and column selection over loading full history into memory.

## Identity and survivorship

Keep exchange and segment identifiers separate from Yahoo or broker IDs. Map symbol changes with effective dates; never merge different economic securities solely because a name resembles another. Preserve removed and delisted names with availability status. See [point-in-time](point-in-time.md).
