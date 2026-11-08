"""Transactional manual paper fill ledger. NEVER contacts a broker.

Money is stored as integer paise (schema version 2); ledgers written by v0.1 (floating rupees) are converted on first
open. Each fill records the time it happened (`at`, user supplied, with UTC offset) and when it was recorded."""
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from . import costs as charges
from .core import finite, parse_time, stamp

SCHEMA = 2


def paise(x):
    return int(round(float(x) * 100))


def rupees(p):
    return p / 100


@contextmanager
def db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # SQLite transaction contexts do not close the connection themselves.
    with closing(sqlite3.connect(path, timeout=30)) as c:
        with c:
            version = c.execute("PRAGMA user_version").fetchone()[0]
            tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if version < SCHEMA and "account" in tables:
                _migrate_v1(c)
            c.execute("CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), cash_paise INTEGER NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS positions (symbol TEXT PRIMARY KEY, qty INTEGER, cost_paise INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS fills (id TEXT PRIMARY KEY, at TEXT, recorded TEXT, symbol TEXT, side TEXT, qty INTEGER, price_paise INTEGER, fee_paise INTEGER, realized_paise INTEGER)")
            c.execute(f"PRAGMA user_version={SCHEMA}")
            yield c


def _migrate_v1(c):
    c.execute("ALTER TABLE account RENAME TO account_v1"); c.execute("ALTER TABLE positions RENAME TO positions_v1"); c.execute("ALTER TABLE fills RENAME TO fills_v1")
    c.execute("CREATE TABLE account (id INTEGER PRIMARY KEY CHECK(id=1), cash_paise INTEGER NOT NULL)")
    c.execute("CREATE TABLE positions (symbol TEXT PRIMARY KEY, qty INTEGER, cost_paise INTEGER)")
    c.execute("CREATE TABLE fills (id TEXT PRIMARY KEY, at TEXT, recorded TEXT, symbol TEXT, side TEXT, qty INTEGER, price_paise INTEGER, fee_paise INTEGER, realized_paise INTEGER)")
    c.execute("INSERT INTO account SELECT id, CAST(ROUND(cash*100) AS INTEGER) FROM account_v1")
    c.execute("INSERT INTO positions SELECT symbol, qty, CAST(ROUND(cost*100) AS INTEGER) FROM positions_v1")
    c.execute("INSERT INTO fills SELECT id, at, at, symbol, side, qty, CAST(ROUND(price*100) AS INTEGER), CAST(ROUND(fee*100) AS INTEGER), CAST(ROUND(realized*100) AS INTEGER) FROM fills_v1")
    for t in ("account_v1", "positions_v1", "fills_v1"):
        c.execute(f"DROP TABLE {t}")


def initialize(path, cash):
    finite(cash, "capital", strict=True)
    with db(path) as c:
        if c.execute("SELECT 1 FROM account").fetchone():
            raise ValueError("paper account already exists; choose a different ledger to start again")
        c.execute("INSERT INTO account VALUES (1,?)", (paise(cash),))
    return status(path)


def auto_fee(product, at, side, qty, price, broker="flat20"):
    """Estimated statutory charges plus broker preset for this one order (see costs.py)."""
    return charges.leg(product, at[:10], side, qty * price, broker)["total"]


def fill(path, fill_id, symbol, side, qty, price, fee=None, at=None, product=None, broker="flat20"):
    if side not in ("buy", "sell") or not symbol.strip() or not fill_id.strip():
        raise ValueError("valid side, symbol and unique fill ID required")
    if isinstance(qty, bool) or int(qty) != qty or qty < 1:
        raise ValueError("quantity must be a positive integer")
    finite(price, "price", strict=True)
    at = parse_time(at).isoformat() if at else stamp()
    if fee is None:
        if not product:
            raise ValueError("give --fee, or --auto-fee PRODUCT to estimate charges")
        fee = auto_fee(product, at, side, qty, price, broker)
    finite(fee, "fee")
    price_p, fee_p = paise(price), paise(fee)
    with db(path) as c:
        c.execute("BEGIN IMMEDIATE")
        if c.execute("SELECT 1 FROM fills WHERE id=?", (fill_id,)).fetchone():
            raise ValueError("duplicate fill ID; no change made")
        a = c.execute("SELECT cash_paise FROM account WHERE id=1").fetchone()
        if not a:
            raise ValueError("initialize paper account first")
        cash = a[0]
        held, cost = c.execute("SELECT qty,cost_paise FROM positions WHERE symbol=?", (symbol,)).fetchone() or (0, 0)
        realized = 0
        if side == "buy":
            total = qty * price_p + fee_p
            if total > cash:
                raise ValueError("insufficient paper cash")
            cash -= total
            held, cost = held + qty, cost + total
        else:
            if qty > held:
                raise ValueError("cannot sell more than held; shorting not supported")
            proceeds = qty * price_p - fee_p
            relieved = round(cost * qty / held)
            realized = proceeds - relieved
            held, cost = held - qty, cost - relieved
            cash += proceeds
        c.execute("UPDATE account SET cash_paise=? WHERE id=1", (cash,))
        c.execute("INSERT OR REPLACE INTO positions VALUES (?,?,?)", (symbol, held, cost))
        c.execute("INSERT INTO fills VALUES (?,?,?,?,?,?,?,?,?)", (fill_id, at, stamp(), symbol, side, qty, price_p, fee_p, realized))
    return status(path)


def status(path, prices=None):
    """prices: optional {symbol: (price, as_of)} to mark open positions (unrealised P&L before exit charges)."""
    with db(path) as c:
        a = c.execute("SELECT cash_paise FROM account WHERE id=1").fetchone()
        if not a:
            raise ValueError("initialize paper account first")
        pos = [dict(zip(("symbol", "qty", "cost_basis"), (r[0], r[1], rupees(r[2])))) for r in c.execute("SELECT symbol,qty,cost_paise FROM positions WHERE qty>0")]
        out = {"label": "MANUAL_PAPER_LEDGER", "cash": rupees(a[0]), "positions": pos,
               "realized_pnl": rupees(c.execute("SELECT COALESCE(SUM(realized_paise),0) FROM fills").fetchone()[0]),
               "fills": c.execute("SELECT COUNT(*) FROM fills").fetchone()[0],
               "warning": "User-supplied simulated fills; no live prices or broker execution."}
    if prices is not None:
        unreal, missing = 0.0, []
        for p in pos:
            if p["symbol"] in prices:
                px, asof = prices[p["symbol"]]
                p.update(mark=px, marked_at=asof, unrealized_pnl=round(p["qty"] * px - p["cost_basis"], 2)); unreal += p["unrealized_pnl"]
            else:
                missing.append(p["symbol"])
        out.update(unrealized_pnl=round(unreal, 2), equity=round(out["cash"] + sum(p.get("mark", 0) * p["qty"] for p in pos), 2), unmarked=missing,
                   mark_note="Marked at the latest close in the supplied file; exit charges are not deducted.")
    return out


def latest_prices(bars):
    last = {}
    for b in bars:
        last[b["symbol"]] = (b["close"], b["timestamp"])
    return last
