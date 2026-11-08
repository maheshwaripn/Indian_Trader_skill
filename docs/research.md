# Strategy ideas, evidence and learning

## Turn an idea into explicit rules

Copy `examples/strategy.json` into your private workspace. Fill hypothesis, universe, timeframe, entry, exit, sizing, portfolio limits, costs, data and validation. Run:

```bash
indian-trader coach workspace/my-strategy.json
```

The command checks completeness, not profitability or semantic correctness. Ask an assistant to read `skills/strategy-review/SKILL.md` for substantive critique. It should explain each gap and offer: learn the concept, adopt a stated assumption, choose an alternative, or defer the experiment. A user can accept a research limitation, but the report must continue to disclose it.

## Implemented daily reference strategy

- Long-only, one daily bar per symbol/date.
- Entry: previous close at/below its trailing SMA and current close above its trailing SMA.
- Calculate both SMAs using only closes available at each signal time.
- Buy at the next supplied bar open with adverse slippage.
- Stop is a fixed percentage below the slipped entry; target is a multiple of that initial price risk.
- Exit on a close below SMA at the next open, or on a stop/target during a bar.
- At the sample end, close-price liquidation is a research proxy, not a promised executable order.

## Implemented ORB reference strategy

- Standard cash-equity sessions: 75 five-minute bars opening 09:15 through 15:25 IST.
- First three bars define the opening-range high.
- After the range, a completed close above that high schedules entry at the next bar open.
- At most one entered trade per symbol/session; no new signal at or after 15:00.
- Percentage stop and R target match the daily engine; this is not an opening-range-midpoint stop.
- Any remaining position closes at the session's last bar close, an explicitly labelled proxy.
- Days without the full standard grid (missing bars, holidays, special or Muhurat sessions) get no new entries and are listed in `skipped_sessions`. `--strict-sessions` restores the v0.1 behaviour of rejecting the whole file.

## Products, lots and membership

- `--product delivery` (trend default), `intraday` (ORB default) or `futures`. Futures need `--lots FILE` (CSV `symbol,effective_date,lot`), trade whole lots only, check margin (`--margin-pct`, default 20% of notional) and treat prices as one continuous contract with no roll cost or basis.
- When one lot or one share exceeds the risk budget the entry is skipped and counted in `rejections`; it is never rounded up.
- `--universe FILE --index Nifty500` allows entries only on dates when the symbol was in the latest earlier membership snapshot. Conflicting histories are refused unless `--allow-unverified`.
- Moves that look like unadjusted splits or bonuses stop the run unless `--allow-suspect-jumps`; use adjusted prices instead.

## Accounting and fills

Capital is split into fixed equal-cash sleeves by symbol. Each sleeve sizes whole shares using available cash and planned risk including estimated costs. Unused cash is not automatically reassigned. Planned stop risk is not guaranteed; gaps can exceed it.

Buy fills include positive slippage and sell fills negative slippage. Fees use the dated Indian cost model by default (see [costs](costs.md)), or a flat bps rate with `--costs bps --fee-bps N`. A stop gapped through fills at the opening price with adverse slippage. If a bar touches both stop and target, stop is assumed first. Targets receive no optimistic gap improvement. No leverage, shorting, partial fills, depth, capacity, broker rejects or derivatives are modelled.

```bash
indian-trader research workspace/my-daily.csv --strategy trend --lookback 20 --capital 100000 --risk-pct 0.5 --stop-pct 2 --target-r 2 --broker flat20 --slippage-bps 5
```

The parameters are adjustable research assumptions, not recommendations. A high target/stop ratio does not ensure positive expectancy. `E = p(win) × average win − p(loss) × average loss` must use actual realised outcomes and costs, with breakeven trades treated consistently.

## A disciplined experiment

1. Write the economic hypothesis and what would disprove it.
2. Freeze baseline rules and an untouched chronological test period.
3. Audit data, universe selection and execution timing.
4. Change one factor or a small preregistered set of factors.
5. Record every trial, including failures. Do not report only the best.
6. Compare net return, drawdown, expectancy, turnover, trade count and exposure.
7. Inspect period/sector dependence and adverse cost scenarios.
8. Evaluate the selected approach on untouched data. If you revise after viewing it, it is no longer untouched.
9. Paper-test operational behaviour before considering any live pilot.

## Evidence protocol (implemented)

Write the rules, windows and checks first. Then:

```bash
# 1. choose settings on the development window only; every setting is reported
indian-trader sweep data.csv --grid '{"lookback":[10,20,40],"stop_pct":[1,2,3]}' --dev 2018-01-01 2021-12-31
# 2. run validation once with the chosen setting; keep the final window closed
indian-trader evaluate data.csv --lookback 20 --stop-pct 2 --dev 2018-01-01 2021-12-31 --val 2022-01-01 2023-12-31 --final 2024-01-01 2025-12-31
```

`sweep` ranks by plateau score (mean expectancy in R of a setting and its one-step neighbours) and adds a reality check: a sign-flip test of the best t-statistic across all settings, in 5-day blocks. `evaluate` reports development and validation separately: metrics, 1x/2x/3x cost stress, equal-cash buy-and-hold over the same window, random entries with the same exits at the rule's own entry rate (30 seeds), and a bootstrap interval of mean R resampled by trading day. Its checks: at least 30 trades, expectancy above zero, bootstrap interval above zero, beats 90% of random runs, still positive at 2x costs, beats buy-and-hold. The verdict is `PASSES_PREDECLARED_CHECKS_NOT_PROOF` or `DOES_NOT_PASS`.

Windows use IST dates. Indicators warm up on earlier bars; trades and equity are scored only inside the window. `research --start/--end` does the same for single runs, and `research --entry random --seed N` runs one null.

## Learning exercises

- Run the demo at zero costs and at higher costs. Explain why win rate alone misses the difference.
- Compare two nearby SMA values. Ask whether apparent improvement is stable or sample noise.
- Inspect the largest losing trades. Separate a signal error, gap, data error and ordinary variation.
- Explain why 10,000 bootstrapped paths from 60 sessions do not create 10,000 independent observations.
- Review current-constituent selection versus dated membership. Identify missing former members before adding indicators.

Ask the coach for one experiment at a time. It must be willing to recommend no change, more data, or rejecting the strategy.
