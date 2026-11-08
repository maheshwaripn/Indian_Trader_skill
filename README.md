# Indian Trader Skill

**Local-first Indian equity research, explainable reports, and AI-guided learning.**

Use Python for arithmetic and data processing. Use Claude, Codex/ChatGPT, Gemini or Copilot to understand evidence, challenge assumptions and plan the next experiment. No AI subscription or API key is required for the offline core.

**Educational software · v0.2 research release · no live order routing.** You own your financial decisions and risk. No returns are promised. Historical, synthetic and paper results are explicitly labelled. Read [risk and responsibility](docs/risk.md).

## About this project

Indian Trader Skill is an open-source educational toolkit for developing a more structured approach to Indian-market strategy research. It combines portable AI instructions, local Python utilities, data-management workflows and explainable reports so users can move from an informal trading idea to a documented, testable specification.

The project is designed for individual traders, learners and developers who want to understand their assumptions as well as their results. It can be used on a personal computer or VPS, with or without an AI assistant. The offline core does not require a paid model API.

### What you can use it for

- **Develop and review strategy ideas:** identify missing entry/exit rules, signal timing, sizing, costs and validation assumptions; understand why each choice matters.
- **Prepare a research data bank:** validate CSV inputs, optionally load Parquet, preserve source snapshots and track provenance instead of repeatedly downloading or changing data without a record.
- **Run reference research:** explore daily SMA-cross and five-minute opening-range-breakout examples, inspect trades and assess documented assumptions. These examples demonstrate research mechanics; they are not validated investment recommendations.
- **Understand performance:** generate offline HTML dashboards and compact evidence briefs, review trade filters and learn how to interpret metrics and their limitations.
- **Record paper activity:** maintain a manual fill ledger for positions and cash, clearly separated from historical simulations and actual broker execution.
- **Audit historical constituents:** inspect NiftyHistory membership events and retrieve as-of snapshots while keeping unresolved source conflicts visible.
- **Learn setup and operating practices:** follow guides for Python, AI assistants, data sources, VPS operation, broker connectivity prerequisites and live-trading readiness.

### Local computation and optional AI guidance

Python performs calculations and data processing; the assistant helps clarify the hypothesis, explain missing elements and suggest the next useful investigation. The shared instructions are intended for Claude, ChatGPT/Codex, Gemini and Copilot, subject to each tool's available access and capabilities.

Start an AI review with the generated `brief.json`, then inspect larger artifacts only when needed. The four modes—`local`, `assisted`, `lab` and `vps`—provide different input and brief budgets. They do not measure or cap tokens consumed by an external assistant. A browser chatbot needs an authorized connection or user-run commands to work on a local machine or VPS.

### How it relates to Indian Quant

Use **Indian Trader Skill** for guided strategy formulation, reference backtests, data preparation, report interpretation and manual paper accounting. Use **[Indian Quant](https://github.com/maheshwaripn/Indian_Quant)** for Qlib-backed factor research, baseline machine-learning comparisons and portfolio simulations. Both repositories install independently; sharing a purpose does not imply an automatic data or execution integration.

The current release is a research and learning foundation. Broker adapters, automatic paper fills, live routing and walk-forward orchestration remain future work. Historical constituent auditing is available, but reference backtests do not automatically apply membership eligibility. The capability table below distinguishes working features from planned extensions.

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

Open `workspace/demo-dashboard.html` in a browser. It is a standalone interactive report with no CDN or tracking. Its prices are **synthetic**, not NIFTY history. Expected deterministic demo: 12 trades, ending equity about INR 99,134.20 from INR 100,000 after dated Indian delivery charges and ₹20 brokerage per order (v0.1's flat 10 bps gave INR 99,656.08).

## What works today

| Capability | v0.2 status |
|---|---|
| Offline CSV validation and content-addressed data bank | Implemented, tested; bank is portable (relative paths) and records adjustment state |
| Parquet loading, faster CSV with PyArrow | Optional PyArrow extra; uses same schema |
| NiftyHistory constituent audit, as-of lookup and membership filter in back-tests | Implemented; conflicts blocked unless explicitly exploratory |
| Daily SMA-cross and 5-minute ORB research | Reference engines; ORB skips incomplete sessions; not validated alpha |
| Dated Indian costs (STT, exchange, SEBI, stamp, GST, brokerage, DP) | Implemented for delivery, intraday, futures, options; estimates, see [costs](docs/costs.md) |
| Futures mode with dated lot sizes and margin | Implemented, long only, continuous prices |
| Evidence protocol: windows, buy-and-hold, random-entry null, cost stress, bootstrap, sweep, plateau, reality check | Implemented as `evaluate` and `sweep` |
| Corporate-action check and NSE calendar check | Detects suspected unadjusted splits/bonuses; 2026 calendar bundled |
| Dashboard, evidence brief and trade filtering | Implemented; trades shown in rupees and R |
| Strategy completeness review | Implemented deterministic checklist + guided AI workflows |
| Paper accounting | Manual fill ledger in integer paise, fill times, estimated charges, unrealised P&L from a price file |
| Yahoo daily download | Optional yfinance adapter; not live-tested in release validation |
| NSE CM bhavcopy conversion | Legacy and UDiFF layouts, several days merged |
| Four resource modes | Row budgets and brief limits enforced; other budgets are guidance |
| Multiple AI assistants | Shared instructions and setup guides; no claim of end-to-end testing on every AI product |
| Dhan / Zerodha | Detailed setup and live-readiness documentation; no executable broker adapter yet |
| Adjusted-price engine, contract-level futures, auto-ingestion, automatic paper fills, live routing | Roadmap; not implemented |

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
- [Strategy research](docs/research.md): rules, products, evidence protocol, learning exercises
- [Trading costs](docs/costs.md): dated Indian charges and broker presets
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
indian-trader sweep workspace/demo.csv --grid '{"lookback":[10,20,40]}' --dev 2024-01-01 2024-03-31
indian-trader evaluate workspace/demo.csv --lookback 20 --dev 2024-01-01 2024-03-31 --val 2024-04-01 2024-06-30
indian-trader cost-calc --product futures --qty 500 --buy-price 1600 --sell-price 1610 --buy-date 2026-05-04
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

### Shared market utilities and review corrections

The dependency-free `indian_market_core` package supplies dated fees, the bounded NSE calendar and raw bhavcopy parsing for both repositories. Trader retains its public imports. See [cost assumptions and coverage](docs/costs.md) and [independent regression checks](docs/validation.md). Fee dates outside 2023-04-01 through 2026-11-08 now fail explicitly; use documented bps assumptions for other history. Incomplete paper marks yield unavailable total equity plus a known-value subtotal. Validation windows must be chronological and nonoverlapping, including a closed final window.
