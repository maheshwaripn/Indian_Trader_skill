"""Transactional manual paper fill ledger. NEVER contacts a broker."""
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from .core import finite, stamp


@contextmanager
def db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # SQLite transaction contexts do not close the connection themselves.
    with closing(sqlite3.connect(path, timeout=30)) as c:
        with c:
            c.execute("CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), cash REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS positions (symbol TEXT PRIMARY KEY, qty INTEGER, cost REAL)")
            c.execute("CREATE TABLE IF NOT EXISTS fills (id TEXT PRIMARY KEY, at TEXT, symbol TEXT, side TEXT, qty INTEGER, price REAL, fee REAL, realized REAL)")
            yield c


def initialize(path, cash):
    finite(cash, "capital", strict=True)
    with db(path) as c:
        if c.execute("SELECT 1 FROM account").fetchone():
            raise ValueError("paper account already exists; choose a different ledger to start again")
        c.execute("INSERT INTO account VALUES (1,?)", (cash,))
    return status(path)


def fill(path, fill_id, symbol, side, qty, price, fee):
    if side not in ("buy", "sell") or not symbol.strip() or not fill_id.strip():
        raise ValueError("valid side, symbol and unique fill ID required")
    if isinstance(qty, bool) or int(qty) != qty or qty < 1:
        raise ValueError("quantity must be a positive integer")
    finite(price, "price", strict=True)
    finite(fee, "fee")
    with db(path) as c:
        c.execute("BEGIN IMMEDIATE")
        if c.execute("SELECT 1 FROM fills WHERE id=?", (fill_id,)).fetchone():
            raise ValueError("duplicate fill ID; no change made")
        a = c.execute("SELECT cash FROM account WHERE id=1").fetchone()
        if not a:
            raise ValueError("initialize paper account first")
        cash = a[0]
        held, cost = c.execute("SELECT qty,cost FROM positions WHERE symbol=?", (symbol,)).fetchone() or (0, 0)
        realized = 0
        if side == "buy":
            total = qty * price + fee
            if total > cash:
                raise ValueError("insufficient paper cash")
            cash -= total
            held, cost = held + qty, cost + total
        else:
            if qty > held:
                raise ValueError("cannot sell more than held; shorting not supported")
            proceeds = qty * price - fee
            relieved = cost * qty / held
            realized = proceeds - relieved
            held, cost = held - qty, cost - relieved
            cash += proceeds
        c.execute("UPDATE account SET cash=? WHERE id=1", (cash,))
        c.execute("INSERT OR REPLACE INTO positions VALUES (?,?,?)", (symbol, held, cost))
        c.execute("INSERT INTO fills VALUES (?,?,?,?,?,?,?,?)", (fill_id, stamp(), symbol, side, qty, price, fee, realized))
    return status(path)


def status(path):
    with db(path) as c:
        a = c.execute("SELECT cash FROM account WHERE id=1").fetchone()
        if not a:
            raise ValueError("initialize paper account first")
        return {"label": "MANUAL_PAPER_LEDGER", "cash": a[0],
                "positions": [dict(zip(("symbol", "qty", "cost_basis"), r)) for r in c.execute("SELECT * FROM positions WHERE qty>0")],
                "realized_pnl": c.execute("SELECT COALESCE(SUM(realized),0) FROM fills").fetchone()[0],
                "fills": c.execute("SELECT COUNT(*) FROM fills").fetchone()[0],
                "warning": "User-supplied simulated fills; no live prices, broker execution or unrealized P&L implied."}
