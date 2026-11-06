---
name: indian-trader-report-review
description: Generate and explain Indian Trader research dashboards, performance metrics, trade outcomes and evidence limitations using compact local reports.
---

Read `docs/dashboard.md`. Open `brief.json` before the full result.

1. Verify the result label, period, parameters, input hash and code version.
2. Generate the HTML report using `indian-trader dashboard RESULT --output PATH` when needed.
3. Explain return, drawdown, expectancy, trade count, win rate, costs and profit factor in plain language. State what each helps decide and what it cannot show.
4. Review worst trades and concentration of results. Obtain detailed records only for the question at hand.
5. Identify absent benchmark, adjustments, point-in-time filtering or out-of-sample evidence. Do not compute institutional metrics from insufficient inputs or label unavailable values zero.
6. Distinguish synthetic, historical and manual paper evidence. A successful program run is not a successful trading strategy.
7. Recommend one next check and one learning exercise. Provide the exact report path; do not expose private files publicly.

The current HTML is a research dashboard, not a live portfolio service. Do not invent broker connections, automated paper fills, Sharpe, VaR, or regulatory approval.
