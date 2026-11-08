"""NSE trading calendar: weekends, dated holidays and special sessions. Dates outside a loaded calendar's coverage are UNKNOWN."""
import json
from datetime import date, timedelta
from pathlib import Path

BUILTIN = Path(__file__).with_name("data")


def load(paths=None):
    """Merge the bundled yearly files with optional user files of the same shape."""
    files = sorted(BUILTIN.glob("nse_calendar_*.json")) + [Path(p) for p in (paths or [])]
    cal = {"holidays": set(), "special": {}, "covered": []}
    for f in files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        cal["holidays"] |= set(d.get("holidays", []))
        for s in d.get("special_sessions", []):
            cal["special"][s["date"]] = s
        c = d["coverage"]; cal["covered"].append((c["start"], c["end"]))
    return cal


def classify(cal, day):
    d = day if isinstance(day, str) else day.isoformat()
    if not any(a <= d <= b for a, b in cal["covered"]):
        return "UNKNOWN"
    if d in cal["special"]:
        s = cal["special"][d]
        return "TRADING_DAY" if (s.get("open"), s.get("close")) == ("09:15", "15:30") else "SPECIAL_SESSION"
    if d in cal["holidays"] or date.fromisoformat(d).weekday() >= 5:
        return "CLOSED"
    return "TRADING_DAY"


def check(bars, cal):
    """Daily bars: sessions the calendar expects but the file lacks, per symbol, and bars on closed days."""
    by = {}
    for b in bars:
        by.setdefault(b["symbol"], set()).add(b["timestamp"][:10] if b["timestamp"][10:11] == "T" else b["timestamp"])
    out = {}
    for sym, days in by.items():
        first, last = min(days), max(days); d = date.fromisoformat(first); missing, closed, unknown = [], [], 0
        while d.isoformat() <= last:
            k = classify(cal, d); s = d.isoformat()
            if k == "UNKNOWN": unknown += 1
            elif k in ("TRADING_DAY", "SPECIAL_SESSION") and s not in days: missing.append(s)
            elif k == "CLOSED" and s in days: closed.append(s)
            d += timedelta(days=1)
        out[sym] = {"first": first, "last": last, "missing_sessions": missing, "bars_on_closed_days": closed, "days_without_calendar": unknown}
    return {"symbols": out, "missing_total": sum(len(v["missing_sessions"]) for v in out.values()),
            "note": "Dates use the bar's UTC date; daily bars stamped 09:15 IST fall on the same date. Days outside calendar coverage are not judged."}
