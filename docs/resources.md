# Resource and token efficiency

## Four profiles

`local`, `assisted`, `lab` and `vps` are resource presets, not levels of trading permission or user sophistication. Select them with the global `--mode` flag or workspace configuration. Current enforced controls are maximum input rows and number of examples in an evidence brief. The implementation is single-process. Suggested AI review counts and experiment budgets describe a workflow, not an enforced external-session limit.

For true CPU/RAM quotas on a VPS, use OS service limits. For a future API runner, reserve budget before a request, include possible output usage, reconcile returned usage, cap retries and stop when the budget is exhausted. These controls cannot be guaranteed by a Markdown instruction in an unrelated browser session.

## What stays local

Data parsing, indicators, signal logic, sizing, backtesting, accounting, report rendering and dataset hashing are deterministic Python. None require AI tokens. The assistant receives a compact `brief.json`, not the full history. Run logs and large result tables stay in the workspace until specifically needed.

The current implementation does not add a local language model. Such a model would consume RAM/CPU and must earn its cost through measured quality; it is not necessary for arithmetic.

## Keep prompts economical

1. Read the root workflow and one skill. Load the linked guide only when relevant.
2. Ask one bounded question with a clear output: e.g. “identify three evidence gaps and one next test”.
3. Use `brief.json` first. Read a trade subset only when the question requires it.
4. Keep decisions in a short private research note with run IDs. Do not replay entire chats.
5. Summarise changes since the previous run rather than sending unchanged context again.
6. Avoid per-candle/per-symbol model calls, autonomous recursive critique, and unbounded agent teams.
7. Use templates for routine output. Use AI for explanation and critique.
8. Respect data privacy: a brief may contain strategy details or account sizes, so inspect it before upload.

Claude-specific progressive disclosure and cost guidance:
https://code.claude.com/docs/en/skills
https://code.claude.com/docs/en/costs

API prompt caching can reduce repeated prefix processing, but cached content still occupies context and cache writes/hits have provider-specific costs. See https://platform.claude.com/docs/en/build-with-claude/prompt-caching. No model/API-price assumption is hard-coded here.

## Measure before claiming savings

Run `python scripts/benchmark.py`. It compares local runtime and full-result versus brief payload sizes on the deterministic demo. Byte reduction is **not** a token or billing measurement. Use provider usage metadata for actual input/output/cache usage. Compare equal tasks and output quality; record model/version, prompt, retries, wall time and cost basis.

For data-feature caching in a later release, key by input hashes, code/indicator version, parameters and adjustment policy. Never reuse a feature cache across a corrected raw dataset silently. Current raw snapshot deduplication is not feature caching.
