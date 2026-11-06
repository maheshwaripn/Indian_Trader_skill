"""Shared deterministic validation and persistence helpers."""
import csv
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

PROFILES = {
    "local": {"max_rows": 100000, "brief_candidates": 3, "max_experiments": 4, "suggested_ai_reviews": 0},
    "assisted": {"max_rows": 500000, "brief_candidates": 5, "max_experiments": 12, "suggested_ai_reviews": 1},
    "lab": {"max_rows": 2000000, "brief_candidates": 10, "max_experiments": 40, "suggested_ai_reviews": 3},
    "vps": {"max_rows": 2000000, "brief_candidates": 5, "max_experiments": 20, "suggested_ai_reviews": 2},
}


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Unique temp filename avoids collisions between independent writers.
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", dir=p.parent, delete=False, encoding="utf-8") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")
        tmp = f.name
    os.replace(tmp, p)


def finite(value, name, minimum=0, strict=False):
    n = float(value)
    if not math.isfinite(n) or n < minimum or (strict and n == minimum):
        raise ValueError(f"{name} must be finite and {'greater than' if strict else 'at least'} {minimum}")
    return n


def parse_time(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("timestamp requires explicit UTC offset, e.g. 2026-01-05T09:15:00+05:30")
    return d.astimezone(timezone.utc)


def read_bars(path, max_rows=500000):
    """Strict canonical OHLCV input. Timestamps are bar OPEN times."""
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError as e:
            raise ValueError('Install the parquet extra: pip install -e ".[parquet]"') from e
        pf = pq.ParquetFile(path)
        if pf.metadata.num_rows > max_rows:
            raise ValueError("row budget exceeded; partition the dataset or select another profile")
        raw = pf.read().to_pylist()
    else:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            raw = []
            for row in reader:
                if len(raw) >= max_rows:
                    raise ValueError("row budget exceeded; partition the dataset or select another profile")
                raw.append(row)
    if not raw:
        raise ValueError("empty dataset")
    result, seen, previous = [], set(), {}
    for number, row in enumerate(raw, 2):
        try:
            symbol = str(row["symbol"]).strip()
            if not symbol or len(symbol) > 80:
                raise ValueError("invalid symbol")
            dt = parse_time(str(row["timestamp"]))
            key = (symbol, dt)
            if key in seen:
                raise ValueError("duplicate instrument timestamp")
            if symbol in previous and dt <= previous[symbol]:
                raise ValueError("timestamps must increase within each symbol")
            seen.add(key)
            previous[symbol] = dt
            b = {k: finite(row[k], k, strict=True) for k in ("open", "high", "low", "close")}
            b["volume"] = finite(row["volume"], "volume")
            if b["low"] > min(b["open"], b["close"]) or b["high"] < max(b["open"], b["close"]) or b["low"] > b["high"]:
                raise ValueError("invalid OHLC envelope")
            b.update(symbol=symbol, timestamp=dt.isoformat())
            result.append(b)
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"row {number}: {e}") from e
    return result


def quality(bars):
    groups = {}
    for b in bars:
        groups.setdefault(b["symbol"], []).append(b)
    return {
        "status": "STRUCTURALLY_VALID", "rows": len(bars), "symbols": len(groups),
        "first": min(b["timestamp"] for b in bars), "last": max(b["timestamp"] for b in bars),
        "zero_volume_bars": sum(b["volume"] == 0 for b in bars),
        "coverage": {s: {"rows": len(v), "first": v[0]["timestamp"], "last": v[-1]["timestamp"]} for s, v in groups.items()},
        "warnings": ["Structural validation does not certify exchange-calendar completeness, freshness, corporate actions or tradability.",
                     "Historical constituent membership and delisted prices must be supplied independently."]}
