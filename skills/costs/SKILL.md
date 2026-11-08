---
name: indian-trader-costs
description: Explain and estimate Indian trading costs (STT, exchange charges, SEBI fee, stamp duty, GST, brokerage, DP charges) for delivery, intraday, futures and options with Indian Trader Skill, and show how costs change a strategy's result.
---

Read `docs/costs.md`. Use the CLI for every number; do not compute charges in your head.

1. Ask the product (delivery, intraday, futures, options), trade dates, quantity, prices and broker. Map the broker to a preset (`flat20`, `discount`, `zero`) and say it is an approximation.
2. Run `cost-calc` and explain each line, including which statutory rates applied on that date. Note that rates changed on 2023-04-01, 2024-10-01 and 2026-04-01.
3. For a strategy, compare `research` at `--cost-stress 1`, `2` and `3`. Express costs per trade in R, not only rupees.
4. Tell the user to check the current schedule on the NSE and broker websites and their contract notes before relying on any figure.

These are estimates for research. Never present them as tax or legal advice.
