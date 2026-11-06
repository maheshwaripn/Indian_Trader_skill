# Indian Trader Skill

**Local-first Indian equity research, explainable reports, and AI-guided learning.**

Use Python for arithmetic and data processing. Use Claude, Codex/ChatGPT, Gemini or Copilot to understand evidence, challenge assumptions and plan the next experiment. No AI subscription or API key is required for the offline core.

**Educational software · v0.1 research release · no live order routing.** You own your financial decisions and risk. No returns are promised. Historical, synthetic and paper results are explicitly labelled. Read [risk and responsibility](docs/risk.md).

## Start by asking your assistant

> Use this repository: https://github.com/maheshwaripn/Indian_Trader_skill. Read START_HERE.md, inspect my authorised environment, help me choose a resource mode and data source, run the offline demonstration, explain the report, and help me turn my strategy idea into a testable specification. Keep computations local and explain any limitations.

A URL does **not** give a browser chatbot control of your machine. Use an authorised terminal agent, an approved local connection, or follow the manual commands. See [AI setup](docs/ai-setup.md).

## Five-minute offline demonstration

Requires Python 3.11+ and Git. Windows activation differs; see [installation](docs/install.md).

```bash
git clone https://github.com/maheshwaripn/Indian_Trader_skill.git
cd Indian_Trader_skill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
indian-trader doctor
indian-trader init --interactive
indian-trader demo
```

Open `workspace/demo-dashboard.html` in a browser. It is a standalone interactive report with no CDN or tracking. Its prices are **synthetic**, not NIFTY history. Expected deterministic demo: 12 trades, ending equity approximately INR 99,656.08 from INR 100,000, using the documented default costs. This loss-making example is intentional: the demonstration does not select favourable results.

## What works today

| Capability | v0.1 status |
|---|---|
| Offline CSV validation and content-addressed data bank | Implemented, tested |
| Parquet loading | Optional PyArrow extra; uses same schema |
| NiftyHistory constituent audit and as-of snapshot lookup | Implemented; conflicts blocked unless explicitly exploratory |
| Daily SMA-cross and 5-minute ORB research | Implemented reference engines; not validated alpha |
| Dashboard, evidence brief and trade filtering | Implemented; generated offline HTML |
| Strategy completeness review | Implemented deterministic checklist + guided AI workflows |
| Paper accounting | Implemented manual fill ledger; not a broker sandbox or automated fill service |
| Yahoo daily download | Optional yfinance adapter; not live-tested in release validation |
| Legacy NSE CM bhavcopy conversion | Implemented; UDiFF requires explicit mapping |
| Four resource modes | Row budgets and brief limits enforced; other budgets are guidance |
| Multiple AI assistants | Shared instructions and setup guides; no claim of end-to-end testing on every AI product |
| Dhan / Zerodha | Detailed setup and live-readiness documentation; no executable broker adapter yet |
| Walk-forward orchestration, auto-ingestion, automatic paper fills, live routing | Roadmap; not implemented |

## Four resource modes

| Mode | Use | Maximum input rows | Brief candidates | AI review guidance |
|---|---|---:|---:|---:|
| `local` | Offline/basic laptop | 100,000 | 3 | 0 |
| `assisted` | Everyday research | 500,000 | 5 | 1 |
| `lab` | Larger experiments | 2,000,000 | 10 | 3 |
| `vps` | Persistent server workflows | 2,000,000 | 5 | 2 |

Choose with `indian-trader --mode local demo` or edit `workspace/config.json`. Global flags go **before** the subcommand. All current Python operations are single-process and make zero AI calls. Profiles do not enforce OS RAM/CPU quotas or a third-party chat token ceiling. See [resource controls](docs/resources.md).

## Documentation map

- [Start here](START_HERE.md): first session and assistant workflow
- [Installation](docs/install.md): Windows, macOS, Linux, troubleshooting
- [AI setup](docs/ai-setup.md): Claude, ChatGPT/Codex, Gemini, Copilot
- [Data sources and bank](docs/data.md): CSV, Parquet, Yahoo, NSE, broker data
- [Point-in-time history](docs/point-in-time.md): constituent semantics and supplied CSV audit
- [Strategy research](docs/research.md): rules, costs, validation, learning exercises
- [Dashboard and metrics](docs/dashboard.md): how to read reports
- [Dhan](docs/dhan.md) and [Zerodha](docs/zerodha.md): setup and connectivity guides
- [Live readiness](docs/live-readiness.md): static IP, current official references, operational gates
- [VPS operations](docs/vps.md): secure access, scheduling, backups, restart recovery
- [Resource and token efficiency](docs/resources.md)
- [Command reference](docs/commands.md)
- [Architecture and roadmap](docs/architecture.md)
- [Risk and responsibility](docs/risk.md), [security](SECURITY.md), [contributing](CONTRIBUTING.md)

## Example research workflow

```bash
indian-trader validate workspace/demo.csv
indian-trader ingest workspace/demo.csv --name demo --source synthetic
indian-trader scan workspace/demo.csv
indian-trader research workspace/demo.csv --strategy trend --lookback 20
indian-trader coach examples/strategy.json
indian-trader paper-init --capital 100000
indian-trader paper-fill --id demo-001 --symbol DEMO_A --side buy --qty 10 --price 100 --fee 1
indian-trader paper-status
```

`research` prints a run folder containing `result.json`, `brief.json` and `dashboard.html`. Give the assistant `brief.json` first, not raw market history. Core research does not automatically apply constituent membership; see the point-in-time guide before using historical universes.

## Validation

See [release validation](docs/validation.md) for tested paths and unverified integrations. Run `python -m unittest discover -s tests -v` and `python scripts/check_docs.py` locally.

## Attribution and data rights

Inspired by [Jake Schincariol's day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill). This implementation is independently written; no upstream code has been copied. Original repository licence remains MIT.

[NiftyHistory](https://niftyhistory.in/) is a third-party source for constituent events. Its site states “All rights reserved”; no redistribution licence was established during review. The supplied CSV is **not redistributed**. Import your own permitted download using the documented workflow. Dataset rights are separate from this code's MIT licence.
