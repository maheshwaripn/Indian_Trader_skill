---
name: indian-trader-research-protocol
description: Run an evidence-gated strategy test with Indian Trader Skill: written rules before results, development and validation windows, an untouched final window, random-entry and buy-and-hold comparisons, cost stress, parameter sweeps with plateau scores and a reality check.
---

Read `docs/research.md` (sections "Evidence protocol" onwards). Treat every idea as a hypothesis; a negative result is a valid outcome.

1. Before any result, write the rules, universe, windows (development, validation, final), costs, settings to try and the checks that would reject the idea into the user's private strategy file. Do not change them after seeing validation; record any change as a new version.
2. Confirm data: `validate`, `calendar-check`, and resolve `suspect_corporate_actions` (use adjusted prices or explain each). Use `--universe` with dated membership when the idea selects from an index.
3. Choose settings with `sweep` on the development window only. Report every setting tried, the plateau-ranked choice and the reality-check p. A p above 0.10 means the best result is consistent with luck.
4. Run `evaluate` once with the chosen setting. Read the verdict and each check: trades, expectancy in R, bootstrap interval, share of random-entry runs beaten, 2x costs, buy-and-hold.
5. Keep the final window closed (`--final` without `--open-final`) until everything is fixed and the user asks to open it, once.
6. Report facts, assumptions and limits; quote numbers from the output files only. Never call a pass proof of future profit, and never suggest live trading from these results alone.
