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

- Complete standard cash-equity sessions only: 75 five-minute bars opening 09:15 through 15:25 IST.
- First three bars define the opening-range high.
- After the range, a completed close above that high schedules entry at the next bar open.
- At most one entered trade per symbol/session; no new signal at or after 15:00.
- Percentage stop and R target match the daily engine; this is not an opening-range-midpoint stop.
- Any remaining position closes at the final bar's close as an explicitly labelled proxy.
- Holidays, special sessions, auctions, missing bars and exchange interruptions require additional calendar support and are rejected when the standard grid is incomplete.

## Accounting and fills

Capital is split into fixed equal-cash sleeves by symbol. Each sleeve sizes whole shares using available cash and planned risk including estimated costs. Unused cash is not automatically reassigned. Planned stop risk is not guaranteed; gaps can exceed it.

Buy fills include positive slippage and sell fills negative slippage. Fees use an aggregate user-defined bps rate on each side. A stop gapped through fills at the opening price with adverse slippage. If a bar touches both stop and target, stop is assumed first. Targets receive no optimistic gap improvement. No leverage, shorting, partial fills, depth, capacity, broker rejects or derivatives are modelled.

```bash
indian-trader research workspace/my-daily.csv --strategy trend --lookback 20 --capital 100000 --risk-pct 0.5 --stop-pct 2 --target-r 2 --fee-bps 10 --slippage-bps 5
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

Walk-forward orchestration is a roadmap item. For manual chronological splits, preserve warm-up history without scoring it; do not independently truncate inputs and accidentally change indicator state. The current engine has no warm-up scoring mask, so implement and test one before claiming a formal walk-forward study.

## Learning exercises

- Run the demo at zero costs and at higher costs. Explain why win rate alone misses the difference.
- Compare two nearby SMA values. Ask whether apparent improvement is stable or sample noise.
- Inspect the largest losing trades. Separate a signal error, gap, data error and ordinary variation.
- Explain why 10,000 bootstrapped paths from 60 sessions do not create 10,000 independent observations.
- Review current-constituent selection versus dated membership. Identify missing former members before adding indicators.

Ask the coach for one experiment at a time. It must be willing to recommend no change, more data, or rejecting the strategy.
