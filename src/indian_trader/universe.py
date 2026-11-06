"""NiftyHistory import audit. Never silently reconcile conflicting records."""
import csv
from datetime import date
from .core import digest


def members(text):
    return set(x.strip() for x in text.split(",") if x.strip())


def audit(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"effective_date", "index_type", "inclusions", "exclusions", "symbols"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Expected NiftyHistory effective_date,index_type,inclusions,exclusions,symbols")
        rows = list(reader)
    if not rows:
        raise ValueError("empty constituent file")
    previous, previous_date, events, counts = {}, {}, [], []
    for r in rows:
        d = date.fromisoformat(r["effective_date"])
        index = r["index_type"]
        if index in previous_date and d <= previous_date[index]:
            raise ValueError("effective dates must increase per index")
        previous_date[index] = d
        current, inc, exc = [members(r[k]) for k in ("symbols", "inclusions", "exclusions")]
        counts.append(len(current))
        if index in previous:
            expected = (previous[index] - exc) | inc
            if current != expected:
                events.append({"effective_date": d.isoformat(), "index": index,
                               "unexpected_in_snapshot": sorted(current - expected),
                               "missing_from_snapshot": sorted(expected - current)})
        previous[index] = current
    return {"source": "https://niftyhistory.in/", "sha256": digest(path), "rows": len(rows),
            "first": min(r["effective_date"] for r in rows), "last": max(r["effective_date"] for r in rows),
            "min_members": min(counts), "max_members": max(counts),
            "transition_mismatches": len(events), "mismatches": events,
            "status": "REQUIRES_RECONCILIATION" if events else "INTERNALLY_CONSISTENT_NOT_SOURCE_VERIFIED",
            "publication_times_available": False,
            "warning": "No redistribution licence inferred. Membership is not a substitute for delisted security prices or dated identity mappings."}


def asof(path, on, index="Nifty500", allow_unverified=False):
    report = audit(path)
    if report["transition_mismatches"] and not allow_unverified:
        raise ValueError("Conflicting constituent history: reconcile first or explicitly use --allow-unverified for exploratory snapshots")
    target = date.fromisoformat(on)
    with open(path, encoding="utf-8-sig", newline="") as f:
        eligible = [r for r in csv.DictReader(f) if r["index_type"] == index and date.fromisoformat(r["effective_date"]) <= target]
    if not eligible:
        raise ValueError("No membership snapshot available on or before requested date")
    row = max(eligible, key=lambda r: r["effective_date"])
    return {"as_of": on, "effective_date": row["effective_date"], "index": index,
            "symbols": sorted(members(row["symbols"])), "verified": False,
            "semantics": "snapshot forward-filled until next event; publication time unavailable",
            "stale_possible": on > report["last"], "audit_status": report["status"]}
