# Set up Python plus your AI assistant

The Python engine is the same for every assistant. The portable instructions are in `skills/`. Provider-specific entry files point to the shared workflow. These are repository assets, not automatically installed plugins in every chat product.

## Choose the environment

| Environment | Workflow |
|---|---|
| Terminal agent on laptop | Install Python toolkit; launch the agent from the repository directory |
| Agent on VPS | SSH to the VPS; install there; launch the agent in that checkout |
| Editor assistant | Open repository in the editor; give terminal access according to your permissions |
| Browser chat | Upload a compact brief and ask for interpretation, or use a separately authorised connection |

A chat subscription is not automatically an API entitlement. Check the provider's current account terms. This release calls no AI API and stores no AI credentials.

## Claude Code

1. Follow the official installer for your OS: https://code.claude.com/docs/en/overview.
2. Authenticate using the product's supported login flow.
3. Open a terminal in this repository and start `claude`.
4. Ask it to read `CLAUDE.md` and `START_HERE.md`, run `indian-trader doctor`, and explain the planned commands.
5. For project-local discovery, copy a selected skill folder from `skills/` to `.claude/skills/`. Its supporting guides remain in this checkout; launch from the repository root. This repository does not claim a marketplace plugin installation command.
6. Run the demo and have Claude read only the brief initially.

Claude skill documentation: https://code.claude.com/docs/en/skills.

## ChatGPT / Codex

1. Use Codex with authorised local execution for hands-on work, or ChatGPT to interpret uploaded briefs.
2. Follow the official CLI installation and login guide: https://developers.openai.com/codex/cli/ (may redirect to ChatGPT Learn).
3. Launch `codex` in this checkout and ask it to read `AGENTS.md` and `START_HERE.md`.
4. Verify that the terminal belongs to your target machine before writing files or installing dependencies.
5. Run the offline demo; open the generated dashboard locally.
6. If using browser chat without a local connection, run the CLI yourself and upload `brief.json`. Do not describe a hosted chat sandbox as your laptop or VPS.

Do not bypass shell approvals or expose a public unauthenticated execution endpoint.

## Gemini CLI

1. Follow https://geminicli.com/docs/get-started/installation/ for the current installation and runtime requirements.
2. Authenticate through its supported account flow.
3. Start `gemini` in the repository and ask it to use `GEMINI.md` and `START_HERE.md`.
4. Ask it to run local commands and load a single relevant skill. Portable Markdown can be read explicitly even if automatic discovery differs by version.
5. Verify the resulting files rather than relying on a verbal success message.

## GitHub Copilot

1. Follow https://docs.github.com/en/copilot/get-started/cli-quickstart. The npm route documented at review time uses Node.js 22+ and `npm install -g @github/copilot`.
2. Start `copilot` from this repository, authenticate with `/login`, and review directory trust prompts.
3. Ask it to read `.github/copilot-instructions.md`, `START_HERE.md`, and the relevant skill.
4. Alternatively open the checkout in an editor with Copilot and an authorised terminal.
5. Run the same demo and validation commands as any other assistant.

## Keep context small

Ask: “Read the brief, explain the three most important limitations, and propose one next experiment. Inspect detailed results only if necessary.” Do not paste complete Parquet files, thousands of rows, tokens, or the entire documentation set. Each provider retains its own policies and permissions; this toolkit does not override them.

## Compatibility honesty

The core CLI and portable instructions are provider-independent. Cross-product automatic skill discovery, hosted remote access, and login flows have not been end-to-end tested in this release. Follow official current documentation if a command or screen changes. Record your tested agent version when contributing an integration fix.
