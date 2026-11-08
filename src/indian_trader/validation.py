"""Evidence checks around the reference engines: date windows, baselines, random-entry nulls, cost stress,
bootstrap intervals in R, parameter sweeps with neighbour (plateau) scores and a reality check across every setting tried.

Typical use: choose settings on the development window only, then run the validation window once, and keep the
final window untouched until you have decided. Nothing here proves an edge; it makes luck and costs visible."""
from datetime import date
import itertools
import math
import random
from statistics import median
from . import costs as charges
from .core import parse_time
from .research import IST, daily_returns, run


def validate_windows(*windows):
    previous = None
    for bounds in windows:
        if bounds is None:
            continue
        if len(bounds) != 2 or not all(bounds):
            raise ValueError("Each window requires explicit start and end dates")
        start, end = map(date.fromisoformat, bounds)
        if start > end or (previous is not None and start <= previous):
            raise ValueError("Windows must be chronological, nonoverlapping and nonempty")
        previous = end


def window(start, end):
    return {"start": start, "end": end}


def buy_and_hold(bars, start, end, capital=100000, product="delivery", broker="flat20", costs="india", fee_bps=10, slippage_bps=5):
    """Equal cash per symbol, bought at the first open in the window and sold at the last close, same cost model."""
    by = {}
    for b in bars:
        d = parse_time(b["timestamp"]).astimezone(IST).date().isoformat()
        if (not start or d >= start) and (not end or d <= end):
            by.setdefault(b["symbol"], []).append((d, b))
    if not by:
        return None
    alloc, slip, total = capital / len(by), slippage_bps / 10000, 0.0
    for rows in by.values():
        (d0, first), (d1, last) = rows[0], rows[-1]
        px_in, px_out = first["open"] * (1 + slip), last["close"] * (1 - slip)
        fee_in = (lambda v, d0=d0: charges.leg(product, d0, "buy", v, broker)["total"]) if costs == "india" else (lambda v: v * fee_bps / 10000)
        qty = math.floor(alloc / (px_in * 1.002))
        while qty and qty * px_in + fee_in(qty * px_in) > alloc:
            qty -= 1
        cash = alloc - qty * px_in - fee_in(qty * px_in)
        fee_out = charges.leg(product, d1, "sell", qty * px_out, broker)["total"] if costs == "india" else qty * px_out * fee_bps / 10000
        total += cash + qty * px_out - fee_out
    return {"net_return_pct": (total / capital - 1) * 100, "symbols": len(by)}


def bootstrap_r(trades, n=2000, seed=7):
    """95% interval of mean R per trade, resampling trading days (trades exiting the same day move together)."""
    by = {}
    for t in trades:
        if t.get("r_multiple") is not None:
            by.setdefault(t["exit_time"][:10], []).append(t["r_multiple"])
    days = list(by.values())
    if len(days) < 5:
        return None
    if n < 40:
        raise ValueError("bootstrap requires at least 40 samples")
    rng = random.Random(seed); means = []
    for _ in range(n):
        pick = [r for _ in days for r in rng.choice(days)]
        means.append(sum(pick) / len(pick))
    means.sort()
    return {"low": means[int(0.025 * n)], "high": means[int(0.975 * n) - 1], "days": len(days)}


def null_runs(bars, params, start, end, seeds=30):
    """Random entries with the same exits, sizing, costs and window, entering at the rule's own rate."""
    if not 1 <= seeds <= 10000:
        raise ValueError("seeds must be between 1 and 10000")
    rule = run(bars, **params, start=start, end=end)
    eligible = rule["metrics"]["eligible_entry_bars"] or 1
    rate = min(1.0, max(rule["metrics"]["trades"], 1) / eligible)
    out = []
    for s in range(seeds):
        r = run(bars, **params, start=start, end=end, entry="random", seed=1000 + s, entry_rate=rate)
        out.append(r["metrics"]["net_return_pct"])
    out.sort()
    strat = rule["metrics"]["net_return_pct"]
    return {"rule_net_return_pct": strat, "null_median": median(out), "null_p90": out[int(0.9 * (len(out) - 1))],
            "share_of_nulls_beaten": sum(x < strat for x in out) / len(out), "seeds": seeds, "entry_rate": rate}


def evaluate(bars, params, dev, val, final=None, open_final=False, seeds=30, stresses=(1.0, 2.0, 3.0), gates=None):
    """Development and validation results, stress, baseline, null and bootstrap; gates are checked on validation."""
    validate_windows(dev, val, final)
    gates = {"min_trades": 30, "min_expectancy_r": 0.0, "min_null_share": 0.9, "stress_2x_positive": True, **(gates or {})}
    windows = {"development": dev, "validation": val}
    if final and open_final:
        windows["final"] = final
    out = {"label": "VALIDATION_REPORT", "parameters": params, "windows": windows, "gates": gates, "results": {}}
    for name, (a, b) in windows.items():
        r = run(bars, **params, start=a, end=b)
        stress = {f"{k:g}x": run(bars, **{**params, "cost_stress": k}, start=a, end=b)["metrics"] for k in stresses}
        bh = buy_and_hold(bars, a, b, params.get("capital", 100000), r["parameters"]["product"] if r["parameters"]["product"] != "intraday" else "delivery",
                          params.get("broker", "flat20"), r["parameters"]["costs"], params.get("fee_bps", 10) or 10, params.get("slippage_bps", 5))
        out["results"][name] = {"metrics": r["metrics"], "stress": {k: {"net_return_pct": v["net_return_pct"], "expectancy_r": v["expectancy_r"], "trades": v["trades"]} for k, v in stress.items()},
                                "buy_and_hold": bh, "null": null_runs(bars, params, a, b, seeds), "bootstrap_r": bootstrap_r(r["trades"]),
                                "rejections": r["rejections"], "skipped_sessions": sum(len(v) for v in r["skipped_sessions"].values())}
    v = out["results"]["validation"]; m = v["metrics"]; checks = {
        "enough_trades": m["trades"] >= gates["min_trades"],
        "expectancy_r_positive": (m["expectancy_r"] if m["expectancy_r"] is not None else -math.inf) > gates["min_expectancy_r"],
        "bootstrap_excludes_zero": bool(v["bootstrap_r"] and v["bootstrap_r"]["low"] > 0),
        "beats_random_entries": v["null"]["share_of_nulls_beaten"] >= gates["min_null_share"],
        "survives_2x_costs": (not gates["stress_2x_positive"]) or (v["stress"].get("2x", {}).get("net_return_pct", -1) > 0),
        "beats_buy_and_hold": bool(v["buy_and_hold"]) and m["net_return_pct"] > v["buy_and_hold"]["net_return_pct"]}
    out["checks"] = checks
    out["verdict"] = "PASSES_PREDECLARED_CHECKS_NOT_PROOF" if all(checks.values()) else "DOES_NOT_PASS"
    out["warnings"] = ["Decide the windows, settings and checks before looking at validation; changing them afterwards makes the result development data.",
                       "Passing these checks is not evidence of future profit; it only removes some common sources of false results."]
    if final and not open_final:
        out["warnings"].append(f"Final window {final[0]} to {final[1]} kept closed. Open it once, when everything else is fixed.")
    return out


def neighbours(key, grid):
    names = list(grid)
    for i, n in enumerate(names):
        vals = grid[n]; j = vals.index(key[i])
        for k in (j - 1, j + 1):
            if 0 <= k < len(vals):
                yield key[:i] + (vals[k],) + key[i + 1:]


def sweep(bars, base, grid, dev, min_trades=20, flips=1000, block=5, seed=11):
    """Every combination of `grid` on the development window. Ranked by plateau score: mean expectancy in R of the
    setting and its one-step neighbours, so an isolated lucky setting cannot win. Includes a reality check
    (sign-flip max-t over daily returns of all settings): p is a resampling tail frequency under a block sign-symmetry null, not the probability of no edge."""
    validate_windows(dev)
    if not 1 <= block <= 252 or not 1 <= flips <= 100000:
        raise ValueError("block must be 1..252 and flips 1..100000")
    names = list(grid)
    if not names:
        raise ValueError("grid is empty")
    combos = list(itertools.product(*grid.values()))
    rows, series = {}, {}
    for key in combos:
        p = {**base, **dict(zip(names, key))}
        r = run(bars, **p, start=dev[0], end=dev[1])
        rows[key] = {**dict(zip(names, key)), "trades": r["metrics"]["trades"], "expectancy_r": r["metrics"]["expectancy_r"],
                     "net_return_pct": r["metrics"]["net_return_pct"], "max_drawdown_pct": r["metrics"]["max_drawdown_pct"]}
        series[key] = daily_returns(r)
    for key, row in rows.items():
        group = [rows[k] for k in [key, *neighbours(key, grid)] if rows[k]["trades"] >= min_trades and rows[k]["expectancy_r"] is not None]
        row["plateau_score"] = sum(g["expectancy_r"] for g in group) / len(group) if rows[key]["trades"] >= min_trades and group else None
    ranked = sorted(rows.values(), key=lambda r: -1e9 if r["plateau_score"] is None else r["plateau_score"], reverse=True)
    days = sorted({d for s in series.values() for d in s})
    X = [[series[k].get(d, 0.0) for k in combos] for d in days]
    rc = None
    if len(days) >= 20:
        def tstats(M):
            n = len(M); out = []
            for j in range(len(combos)):
                col = [row[j] for row in M]; mu = sum(col) / n; var = sum((x - mu) ** 2 for x in col) / (n - 1)
                out.append(mu / math.sqrt(var / n) if var > 0 else 0.0)
            return out
        actual = max(tstats(X)); rng = random.Random(seed); hits = 0
        for _ in range(flips):
            signs = []
            while len(signs) < len(days):
                signs += [rng.choice((-1, 1))] * block
            if max(tstats([[x * s for x in row] for row, s in zip(X, signs)])) >= actual:
                hits += 1
        rc = {"settings": len(combos), "best_t": actual, "p_value": (hits + 1) / (flips + 1), "block_days": block}
    return {"label": "PARAMETER_SWEEP_DEVELOPMENT_ONLY", "window": dev, "grid": grid, "settings_tried": len(combos),
            "selected": ranked[0] if ranked and ranked[0]["plateau_score"] is not None else None, "ranked": ranked, "reality_check": rc,
            "warnings": ["Every setting tried is listed; report them all.",
                         "Choose by plateau score, then run the validation window once with the chosen setting.",
                         "A reality-check p above 0.10 means the best result is consistent with luck across this many settings."]}
