"""Content-addressed raw data snapshots with SQLite catalogue and explicit revisions.

Snapshot paths are stored relative to the bank folder, so the workspace can be moved or copied. Catalogues written by
v0.1 (absolute paths) are still read: a missing absolute path falls back to raw/<hash>/<file name> inside the bank."""
import json
import re
import shutil
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from .core import digest, quality, read_bars, stamp

ADJUSTMENTS = ("raw", "adjusted", "unknown")


@contextmanager
def connect(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # SQLite transaction contexts do not close the connection themselves.
    with closing(sqlite3.connect(root / "catalogue.sqlite", timeout=30)) as con:
        with con:
            con.execute("CREATE TABLE IF NOT EXISTS datasets (name TEXT, hash TEXT, source TEXT, captured TEXT, path TEXT, quality TEXT, PRIMARY KEY(name,hash))")
            if "adjustment" not in [r[1] for r in con.execute("PRAGMA table_info(datasets)")]:
                con.execute("ALTER TABLE datasets ADD COLUMN adjustment TEXT NOT NULL DEFAULT 'unknown'")
            yield con


def resolve(root, stored):
    """Bank-relative path, or a v0.1 absolute path that still exists, or the same file inside this bank."""
    p = Path(stored)
    if not p.is_absolute():
        return Path(root) / p
    if p.exists():
        return p
    return Path(root) / "raw" / p.parent.name / p.name


def ingest(root, name, path, source, max_rows, adjustment="unknown"):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
        raise ValueError("dataset name must contain only letters, digits, underscores or hyphens")
    if not source.strip():
        raise ValueError("source is required")
    if adjustment not in ADJUSTMENTS:
        raise ValueError("adjustment must be raw, adjusted or unknown")
    bars = read_bars(path, max_rows)
    report = quality(bars)
    sha = digest(path)
    relative = Path("raw") / sha / Path(path).name
    destination = Path(root) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(path, destination)
    if digest(destination) != sha:
        raise ValueError("stored snapshot hash mismatch")
    with connect(root) as con:
        con.execute("INSERT OR IGNORE INTO datasets (name,hash,source,captured,path,quality,adjustment) VALUES (?,?,?,?,?,?,?)",
                    (name, sha, source, stamp(), relative.as_posix(), json.dumps(report), adjustment))
    out = {"name": name, "sha256": sha, "path": str(destination), "adjustment": adjustment, "quality": report}
    if adjustment != "adjusted" and report["suspect_corporate_actions"]:
        out["warning"] = "Moves that look like unadjusted splits or bonuses were found; returns across them are wrong until adjusted."
    return out


def catalogue(root):
    with connect(root) as con:
        rows = con.execute("SELECT name,hash,source,captured,path,adjustment FROM datasets ORDER BY captured DESC").fetchall()
    return [dict(zip(("name", "sha256", "source", "captured_at", "path", "adjustment"), r[:4] + (str(resolve(root, r[4])), r[5]))) for r in rows]


def verify(root):
    result = []
    for r in catalogue(root):
        p = Path(r["path"])
        result.append({"name": r["name"], "sha256": r["sha256"], "ok": p.exists() and digest(p) == r["sha256"]})
    return result
