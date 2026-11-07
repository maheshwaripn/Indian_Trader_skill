"""Content-addressed raw data snapshots with SQLite catalogue and explicit revisions."""
import json
import re
import shutil
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from .core import digest, quality, read_bars, stamp


@contextmanager
def connect(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # SQLite transaction contexts do not close the connection themselves.
    with closing(sqlite3.connect(root / "catalogue.sqlite", timeout=30)) as con:
        with con:
            con.execute("CREATE TABLE IF NOT EXISTS datasets (name TEXT, hash TEXT, source TEXT, captured TEXT, path TEXT, quality TEXT, PRIMARY KEY(name,hash))")
            yield con


def ingest(root, name, path, source, max_rows):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
        raise ValueError("dataset name must contain only letters, digits, underscores or hyphens")
    if not source.strip():
        raise ValueError("source is required")
    bars = read_bars(path, max_rows)
    report = quality(bars)
    sha = digest(path)
    destination = Path(root) / "raw" / sha / Path(path).name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(path, destination)
    if digest(destination) != sha:
        raise ValueError("stored snapshot hash mismatch")
    with connect(root) as con:
        con.execute("INSERT OR IGNORE INTO datasets VALUES (?,?,?,?,?,?)",
                    (name, sha, source, stamp(), str(destination.resolve()), json.dumps(report)))
    return {"name": name, "sha256": sha, "path": str(destination), "quality": report}


def catalogue(root):
    with connect(root) as con:
        return [dict(zip(("name", "sha256", "source", "captured_at", "path"), r)) for r in con.execute("SELECT name,hash,source,captured,path FROM datasets ORDER BY captured DESC")]


def verify(root):
    result = []
    for r in catalogue(root):
        p = Path(r["path"])
        result.append({"name": r["name"], "sha256": r["sha256"], "ok": p.exists() and digest(p) == r["sha256"]})
    return result
