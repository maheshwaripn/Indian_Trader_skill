# Installation and troubleshooting

## Requirements

Use Python 3.11 or later, Git, and a current browser. The core uses only Python's standard library after installation. Optional Parquet and Yahoo modules install separately. No GPU is needed. Begin with a small dataset; row-count limits are not a guarantee of low memory use.

Download Python from https://www.python.org/downloads/ and Git from https://git-scm.com/downloads. Use official installers; check versions before proceeding.

## Windows PowerShell

```powershell
py --version
git --version
git clone https://github.com/maheshwaripn/Indian_Trader_skill.git
cd Indian_Trader_skill
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\indian-trader.exe doctor
.\.venv\Scripts\indian-trader.exe init --interactive
.\.venv\Scripts\indian-trader.exe demo
Start-Process workspace\demo-dashboard.html
```

Using the full executable path avoids changing PowerShell execution policy. If `py` is unavailable, use the installed Python executable. Confirm it is 3.11+.

## macOS / Linux

```bash
python3 --version
git --version
git clone https://github.com/maheshwaripn/Indian_Trader_skill.git
cd Indian_Trader_skill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
indian-trader doctor
indian-trader init --interactive
indian-trader demo
```

Open the reported HTML path in your browser. On Ubuntu 24.04, install missing prerequisites with `sudo apt update` followed by `sudo apt install python3 python3-venv git`. These administrative steps affect the machine; an assistant should explain them before execution. Do not use `sudo pip`.

## Optional formats

```bash
python -m pip install -e ".[parquet]"
python -m pip install -e ".[yahoo]"
```

Only install what you need. Capture an environment after a working install with `python -m pip freeze > workspace/environment.txt`; do not overwrite it on every run. Optional dependencies use bounded ranges, not an exact cross-platform lock; the core has no runtime dependencies.

## Updating

Commit or back up your own changes first. Run `git pull --ff-only`, reinstall with `python -m pip install -e .`, then run `python -m unittest discover -s tests -v` and the demo. Compare the version and demo output. Keep the previous Git commit and a data-bank backup so you can roll back code without deleting datasets.

## Common failures

| Symptom | Check / action |
|---|---|
| `indian-trader: command not found` | Activate the virtual environment or use its full executable path |
| Unsupported Python | Install Python 3.11+ and recreate the virtual environment |
| `No module named pyarrow` | Install the Parquet extra only if needed |
| Duplicate timestamp | Inspect duplicate rows; do not silently drop conflicting candles |
| Missing timezone | Export ISO timestamps with an explicit offset; India is `+05:30` |
| ORB rejects dataset | It requires complete standard 75-bar five-minute sessions with bar-open timestamps |
| Yahoo empty/rate limited | Check symbol/date range and wait with backoff; use a permitted alternative source |
| Config already exists | Edit `workspace/config.json` deliberately or choose `--workspace another-folder` |
| Insufficient memory | Partition by symbol/date, use `local`, and avoid loading an entire intraday archive |
| Browser chat cannot run commands | Use an authorised terminal agent or execute the documented commands yourself |

When reporting a bug, include OS, Python/package versions, command, redacted error, and a minimal synthetic example. Never attach broker tokens or account statements publicly.
