---
name: indian-trader-setup
description: Set up and explore Indian Trader Skill on a local computer or VPS, choose resource and data options, and run the offline demo with an authorised terminal.
---

Read `START_HERE.md` from the repository root. If this skill was copied elsewhere, locate the checkout before running commands. Do not assume a chat sandbox is the user's machine.

1. Establish target OS, authorised terminal access and whether the user wants local or VPS operation. If no access exists, explain the manual route.
2. Read `docs/install.md` and the relevant section of `docs/ai-setup.md`. Inspect Python/version and existing installation before proposing changes.
3. Run `indian-trader doctor`. Explain `local`, `assisted`, `lab`, `vps`; current profiles enforce rows/brief limits, not whole-system quotas.
4. Offer source choices: existing CSV/Parquet, Yahoo, NSE, Dhan or Zerodha. Explain capabilities and costs without inventing current prices.
5. Use `init --interactive` for a person at a terminal. In automation use explicit `--mode` before `init --source`; never hang on an interactive prompt.
6. Run the offline demo. Explain its synthetic label and open the local dashboard if authorised.
7. Report exact paths, outcome and remaining limitations. Offer one learning action.

Never install all optional dependencies by default. Never silently configure live accounts, send orders or request secrets in chat. Read deeper guides only when needed.
