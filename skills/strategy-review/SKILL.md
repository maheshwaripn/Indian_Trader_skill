---
name: indian-trader-strategy-review
description: Evaluate a trading idea, identify missing strategy rules, explain their importance, and design bounded experiments using Indian Trader Skill.
---

Read `docs/research.md` in the checkout. Treat the user's idea as a hypothesis, not evidence of an edge.

1. Extract hypothesis, universe, timeframe, entry, exit, sizing, portfolio limits, costs, data and validation into a private strategy JSON. Preserve uncertainties rather than inventing rules.
2. Run `indian-trader coach PATH`. For each material gap explain why it matters and offer a concrete default, alternative or short lesson. Limit initial questions to the three most consequential unresolved choices.
3. Challenge mechanism, timing, survivorship, liquidity, fees, gaps, selection bias and regime dependence. Explain when doing nothing or collecting better data is the best next step.
4. Compare the idea to a simpler baseline. Define what evidence would reject it and how an untouched period will be used.
5. Use an existing engine only if its exact rules match. Otherwise propose a small reviewed implementation and tests; never claim prose has been backtested.
6. Run calculations locally and inspect `brief.json` first. Do not send every symbol/candle to a model.
7. Present facts, assumptions, unknowns, findings and one next experiment. Report failed/negative experiments as faithfully as positive ones.

Allow user risk preferences within supported functionality. Explain the consequence of limitations; do not suppress warnings or bypass legal/provider rules. Do not infer positive expectancy from target R, win rate, or a best-in-sample result.
