# Contributing

Create a focused branch and explain the problem, behaviour change and validation. Run `python -m unittest discover -s tests -v`, `indian-trader demo` and `python scripts/check_docs.py` before submitting a pull request.

Add meaningful tests for timing, accounting, costs, gaps, identity mapping and failure recovery. Do not add tests that merely repeat formulas without independent expected outcomes. Use synthetic fixtures or documented redistributable data. Do not upload third-party market history without permission.

Keep implemented features distinct from planned features. Every provider adapter needs source documentation, entitlements, timeout/rate-limit policy and failure tests. Every new strategy needs exact signal/fill timing, costs, bias assumptions and a simple baseline. Do not submit selected backtest profits as proof of correctness.

Keep AI instructions short and reference detailed guides only when needed. Update command docs when the CLI changes. Do not add broad auto-approval settings, live keys, or default live execution.
