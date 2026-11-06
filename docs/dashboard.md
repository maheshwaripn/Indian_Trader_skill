# Read and use the dashboard

Run `indian-trader demo`, or generate a research run and open its `dashboard.html`. To rebuild from saved results:

```bash
indian-trader dashboard workspace/demo-result.json --output workspace/dashboard.html
```

The report works offline. It includes metric cards with expandable explanations, an equity line, searchable trades, provenance and limitations. HTML escapes untrusted report strings. Do not publish account data or serve your repository root to the internet.

## Reading order

1. **Result label:** synthetic demo, historical simulation or manual paper ledger are different evidence types. The current HTML renderer displays research results; paper accounting is available as CLI JSON.
2. **Provenance:** inspect the dataset hash, version, parameters, period and data quality. A structurally valid file may still have missing sessions or bad adjustments.
3. **Costs:** fees are explicit and slippage is embedded in fills. Replace illustrative assumptions before interpreting profitability.
4. **Equity and drawdown:** inspect loss depth and persistence. The chart is bar-indexed, not evenly spaced calendar time, and may downsample display points; the JSON retains all points.
5. **Trades:** filter by symbol or reason. Review worst outcomes and whether a few trades dominate results.
6. **Evidence gaps:** read warnings before drawing conclusions.

## Metric reference

| Metric | How calculated | Why it helps / common trap |
|---|---|---|
| Net return | Ending equity / initial capital − 1 | Compare equal periods; it is not annualised |
| Maximum drawdown | Minimum equity/prior peak − 1 | Measures observed peak-to-trough loss; bar-close marks miss intrabar stress |
| Win rate | Positive-P&L trades / completed trades | Must be combined with payoff sizes and costs |
| Expectancy INR | Sum of net trade P&L / trade count | Useful for economics; position sizes affect comparability |
| Profit factor | Positive net P&L / absolute negative net P&L | Undefined if no losses; small samples can exaggerate it |
| Fees | Sum of modelled entry and exit fees | Does not certify statutory tax accuracy |
| Ending equity | Cash plus marked holdings | Check reconciliation to starting capital plus P&L |

Example: 40% winners averaging INR 300 and 60% losers averaging INR 100 yield INR 60 average gross P&L per trade before additional costs. A 70% win rate can still lose if losses are sufficiently large.

## Institutional reporting roadmap

The initial dashboard is a reproducible research report, not a full institutional risk platform. Planned views include benchmark-relative returns, exposure and correlation, rolling risk, trade attribution, data-bank health, paper/live reconciliation and system health. Missing capabilities must say “not available”; do not manufacture Sharpe, VaR or benchmark values.

Before adding Sharpe, specify return interval, annualisation, risk-free assumption and serial dependence. Before adding VaR/expected shortfall, disclose model, sample, confidence and tail limitations. Before adding benchmark comparisons, align dates, dividends, currency and fees.

For private VPS access, use the SSH tunnel in [VPS guide](vps.md). The static dashboard itself has no authentication server or live trading controls.
