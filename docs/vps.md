# Ubuntu VPS operations

## Secure first setup

1. Provision a supported Ubuntu host with sufficient disk and a fixed public egress IP if eventual execution is intended.
2. Create a dedicated non-root operator account, SSH keys and a restricted firewall. Keep a second tested recovery route before disabling password access.
3. Install Python 3.11+, `python3-venv` and Git. Clone the repo under the operator's directory, create a virtual environment and run the tests/demo.
4. Keep credentials outside the repository with restricted permissions. The research service does not need trading credentials.
5. Use `indian-trader --mode vps doctor`. Current code is single-process; VPS mode changes row/brief budgets, not an autonomous scheduler.
6. Choose a private workspace on a volume with enough free disk. Content-addressed snapshots preserve revisions and therefore grow.

## Read dashboards privately

On the VPS, serve only a report directory, bound to localhost:

```bash
cd /path/to/Indian_Trader_skill/workspace
python3 -m http.server 8765 --bind 127.0.0.1
```

From your laptop, open an SSH tunnel:

```bash
ssh -N -L 8765:127.0.0.1:8765 user@your-vps
```

Open `http://127.0.0.1:8765/demo-dashboard.html`. Do not bind this unauthenticated server to a public interface or serve `.env`, the repository root or broker logs. Stop it with Ctrl+C when done. The static dashboard is not a trading control panel.

## Schedule existing offline jobs

The initial release can be called by cron/systemd; it does not include an ingestion daemon. Start with a health job using absolute paths:

```cron
# Example: once daily; server timezone controls this schedule.
30 18 * * * /usr/bin/flock -n /home/trader/bank-check.lock /home/trader/Indian_Trader_skill/.venv/bin/indian-trader --workspace /home/trader/Indian_Trader_skill/workspace verify-bank >> /home/trader/bank-check.log 2>&1
```

Replace paths and configure log rotation. Check the server timezone (`timedatectl`) and document whether schedules are UTC or Asia/Kolkata. A cron weekday is not an exchange trading calendar. Never use this example to schedule live trading blindly.

For larger jobs use a systemd service with `User=`, `WorkingDirectory=`, `MemoryMax=`, `CPUQuota=`, a timeout, a private environment file and a non-overlap mechanism. Size limits from actual measurements. Do not restart order workers blindly after failures; reconcile first.

## Backups and recovery

- Back up raw files, catalogue, paper ledger, configuration, private notes and run artifacts. Do not make credential backups public.
- Stop writers before copying SQLite files, or use SQLite's backup API. Copying an active database and ignoring its journal can produce an inconsistent backup.
- Catalogue paths are absolute in v0.1. For relocation, restore files then rebuild the catalogue by re-ingesting verified snapshots; do not assume paths automatically migrate.
- Verify hashes with `verify-bank` after restoration. Check paper cash/positions/fill counts against the source backup.
- Keep code commit and Python environment record alongside the backup.
- Test recovery in a separate workspace before relying on it.

## Failure handling

| Failure | Response |
|---|---|
| Provider outage | Keep old data labelled stale; no fabricated updates |
| Disk nearly full | Stop ingestion; archive verified backups; do not delete raw history automatically |
| Token expiry | Reauthenticate through broker-supported flow; no credential guessing |
| Duplicate job | Use a lock; log that the second job was skipped |
| Corrupt snapshot | Quarantine, restore verified copy, investigate cause |
| Process restart | Inspect last completed artifact and rerun idempotent ingestion; paper fills need unique IDs |
| AI unavailable | Core calculations and reports continue without AI |

The long-term managed service will add queues, incremental fetches, alerts and resumable experiments. Those are not implied by selecting `vps` today.
