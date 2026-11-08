# Command reference

All commands also work as `python -m indian_trader`. Global options come first:
`indian-trader --workspace workspace --mode assisted COMMAND`.

| Command | Purpose / example |
|---|---|
| `doctor` | Inspect Python, OS, CPU count, free disk, active profile |
| `init --interactive` | Choose profile/source and create a research-only workspace config |
| `demo` | Generate seeded synthetic daily prices and an offline report |
| `validate FILE` | Strict structural CSV/Parquet validation |
| `ingest FILE --name NAME --source DESCRIPTION --adjustment raw` | Store raw snapshot and catalogue entry; adjustment is raw, adjusted or unknown |
| `catalogue` | List all snapshot versions |
| `verify-bank` | Hash-check stored snapshots; nonzero exit on corruption |
| `universe-audit FILE --output PATH` | Audit NiftyHistory events against snapshots |
| `universe-asof FILE --date YYYY-MM-DD` | Lookup latest earlier/equal snapshot; blocks conflicting history |
| `scan FILE --lookback 20` | Latest supplied-bar SMA-cross screen; not a live scanner |
| `research FILE --strategy trend` | Daily reference strategy, fixed sleeves, Indian costs by default |
| `research FILE --strategy orb` | 5-minute ORB; incomplete sessions get no entries and are listed |
| `evaluate FILE --dev S E --val S E [--final S E]` | Development and validation results with cost stress, buy-and-hold, random-entry null, bootstrap and pass/fail checks |
| `sweep FILE --grid JSON --dev S E` | Every setting on the development window, plateau ranking and reality check |
| `cost-calc --product futures --qty 500 --buy-price 1600 --sell-price 1610 --buy-date 2026-05-04` | Itemised dated Indian charges |
| `calendar-check FILE` | Missing sessions and bars on closed days against the NSE calendar |
| `dashboard RESULT_JSON --output PATH` | Rebuild standalone HTML report |
| `brief RESULT_JSON` | Compact evidence for an assistant |
| `coach SPEC_JSON` | Check ten strategy specification fields |
| `fetch-yahoo --symbol SYMBOL --start DATE --end DATE --output PATH` | Optional network daily download, end exclusive |
| `convert-bhavcopy FILE... --output PATH` | NSE cash bhavcopy, legacy or UDiFF layout, one or more days merged |
| `paper-init --capital 100000` | Create a manual paper ledger; refuses overwrite |
| `paper-fill --id ID --symbol SYMBOL --side buy --qty 10 --price 100 --fee 1 [--at TIME]` | Record a user-supplied simulated fill; `--auto-fee delivery` estimates charges instead of `--fee` |
| `paper-mark PRICES_FILE` | Cash, holdings and unrealised P&L at the latest close per symbol |
| `paper-status` | Cash, holdings, cost basis and realised P&L |

Research, evaluate and sweep flags: `--capital`, `--lookback`, `--risk-pct`, `--stop-pct`, `--target-r`, `--costs india|bps`, `--fee-bps`, `--product delivery|intraday|futures`, `--broker flat20|discount|zero`, `--slippage-bps`, `--cost-stress`, `--universe FILE --index NAME`, `--lots FILE`, `--margin-pct`, `--strict-sessions`, `--allow-suspect-jumps`. `research` adds `--start`, `--end`, `--entry random --seed N`. Defaults are illustrative, not financial recommendations. `--allow-unverified` applies only to constituent conflicts.

Exit code 0 means the command completed, not that a strategy is sound. Configuration/input failures return 2. An audit can complete successfully while reporting `REQUIRES_RECONCILIATION`; inspect its status field. No command submits broker orders.

## Paper exercise

```bash
indian-trader --workspace workspace/paper-example paper-init --capital 1000
indian-trader --workspace workspace/paper-example paper-fill --id p1 --symbol DEMO --side buy --qty 2 --price 100 --fee 1
indian-trader --workspace workspace/paper-example paper-fill --id p2 --symbol DEMO --side sell --qty 2 --price 110 --fee 1
indian-trader --workspace workspace/paper-example paper-status
```

Expected cash: INR 1,018; realised P&L: INR 18; no open positions; two fills. Repeating `p1` is rejected without changing the ledger. No live market data or real account is involved.
