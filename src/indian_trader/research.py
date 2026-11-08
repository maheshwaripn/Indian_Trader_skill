"""Long-only reference engines. Independent equal-cash sleeves, next-open fills.

Costs: `costs="india"` (default) charges dated NSE statutory items plus a broker preset per order (see costs.py);
`costs="bps"` keeps the v0.1 flat fee per side. Passing `fee_bps` without `costs` selects "bps".
Products: delivery (trend default), intraday (ORB default) and futures (whole lots from a dated lot table, margin check).
"""
import math
import random
from collections import defaultdict
from datetime import timedelta, timezone
from . import costs as charges
from .core import finite, parse_time, suspect_jumps

IST = timezone(timedelta(hours=5, minutes=30))
SESSION = list(range(555, 930, 5))          # 09:15 .. 15:25 IST bar opens


def lot_for(lots, symbol, day):
    """lots: {symbol: [(effective_date, lot), ...]} sorted by date; the latest effective on or before `day`."""
    rows = (lots or {}).get(symbol)
    if not rows:
        raise ValueError(f"futures need a lot size for {symbol}; pass a lot table (symbol,effective_date,lot)")
    lot = None
    for start, size in rows:
        if start <= day:
            lot = size
    if lot is None:
        raise ValueError(f"no lot size for {symbol} on or before {day}")
    return lot


def run(bars, strategy="trend", capital=100000, lookback=20, risk_pct=0.5, stop_pct=2, target_r=2,
        fee_bps=None, slippage_bps=5, costs=None, product=None, broker="flat20", cost_stress=1.0,
        start=None, end=None, entry="rule", seed=None, entry_rate=None, member=None, lots=None, margin_pct=20.0,
        strict_sessions=False, allow_suspect_jumps=False):
    for name, val in (("capital", capital), ("risk_pct", risk_pct), ("stop_pct", stop_pct), ("target_r", target_r), ("cost_stress", cost_stress)):
        finite(val, name, strict=True)
    if risk_pct > 100 or stop_pct >= 100:
        raise ValueError("risk_pct must be <=100 and stop_pct <100")
    costs = costs or ("bps" if fee_bps is not None else "india")
    fee_bps = 10 if fee_bps is None else fee_bps
    finite(fee_bps, "fee_bps")
    finite(slippage_bps, "slippage_bps")
    finite(margin_pct, "margin_pct", strict=True)
    if fee_bps >= 10000 or slippage_bps >= 10000:
        raise ValueError("basis points must be below 10000")
    if lookback < 2:
        raise ValueError("lookback must be >=2")
    if strategy not in ("trend", "orb"):
        raise ValueError("unknown strategy")
    if costs not in ("india", "bps"):
        raise ValueError("costs must be india or bps")
    if entry not in ("rule", "random"):
        raise ValueError("entry must be rule or random")
    product = product or ("delivery" if strategy == "trend" else "intraday")
    if product not in ("delivery", "intraday", "futures"):
        raise ValueError("product must be delivery, intraday or futures")
    if strategy == "orb" and product == "delivery":
        raise ValueError("ORB is intraday: use product intraday or futures")
    if not bars:
        raise ValueError("no bars")
    jumps = suspect_jumps(bars)
    if jumps and product != "futures" and not allow_suspect_jumps:
        j = jumps[0]
        raise ValueError(f"{len(jumps)} overnight moves look like unadjusted splits or bonuses (first: {j['symbol']} {j['timestamp'][:10]}, "
                         f"ratio {j['ratio']}). Use adjusted prices, or pass --allow-suspect-jumps after checking them.")
    rng = random.Random(seed)
    rate = 0.05 if entry_rate is None else entry_rate
    slip = slippage_bps / 10000 * cost_stress

    def leg(side, day, value):
        if costs == "bps":
            return value * fee_bps / 10000 * cost_stress
        return charges.leg(product, day, side, value, broker, brokerage_mult=cost_stress)["total"]

    def fixed_per_trip():
        if costs == "bps":
            return 0.0
        b = charges.BROKERS[broker]
        per = 0.0 if (product == "delivery" and b["delivery_free"]) else b["cap"] * cost_stress
        return 2 * per * (1 + charges.GST) + (b["dp"] * (1 + charges.GST) if product == "delivery" else 0.0)

    def variable(side, day):
        if costs == "bps":
            return fee_bps / 10000 * cost_stress
        return charges.variable_rate(product, day, side)

    groups = defaultdict(list)
    for b in bars:
        t = parse_time(b["timestamp"]).astimezone(IST)
        if end and t.date().isoformat() > end:
            continue
        groups[b["symbol"]].append((b, t))
    if not groups:
        raise ValueError("no bars on or before the end date")
    allocation = capital / len(groups)
    trades, sleeves, rejected, skipped = [], {}, defaultdict(int), {}
    eligible_bars = 0
    for symbol, rows in sorted(groups.items()):
        cash, position, pending, history, points = allocation, None, None, [], {}
        day, opening, entered = None, [], False
        bad_days = set()
        if strategy == "orb":
            sessions = defaultdict(list)
            for _b, t in rows:
                sessions[t.date()].append(t.hour * 60 + t.minute)
            bad_days = {d for d, slots in sessions.items() if slots != SESSION}
            if bad_days and strict_sessions:
                raise ValueError("ORB requires complete standard 09:15–15:25 IST 5-minute sessions. Special sessions need separate support.")
            if bad_days:
                skipped[symbol] = sorted(d.isoformat() for d in bad_days)
        else:
            dates = [t.date() for _, t in rows]
            if len(dates) != len(set(dates)):
                raise ValueError("trend requires one daily bar per symbol per date")
        for i, (b, local) in enumerate(rows):
            minute = local.hour * 60 + local.minute
            today = local.date()
            iso = today.isoformat()
            in_window = not start or iso >= start
            if day != today:
                day, opening, entered = today, [], False
            # Orders based only on the previous completed bar.
            if pending == "sell" and position:
                raw_exit, reason = b["open"], "signal_next_open"
            else:
                raw_exit, reason = None, None
            if pending == "buy" and position is None:
                entry_px = b["open"] * (1 + slip)
                stop = entry_px * (1 - stop_pct / 100)
                stop_fill = stop * (1 - slip)
                unit = entry_px - stop_fill + variable("buy", iso) * entry_px + variable("sell", iso) * stop_fill
                fixed = fixed_per_trip()
                budget = cash * risk_pct / 100 - fixed
                qty = math.floor(budget / unit) if budget > 0 else 0
                lot = 1
                if product == "futures":
                    lot = lot_for(lots, symbol, iso)
                    qty = qty // lot * lot
                    while qty and qty * entry_px * margin_pct / 100 + leg("buy", iso, qty * entry_px) > cash:
                        qty -= lot
                        rejected["margin_reduced"] += 1
                else:
                    while qty and qty * entry_px + leg("buy", iso, qty * entry_px) > cash:
                        qty -= 1
                if qty:
                    buy_fee = leg("buy", iso, qty * entry_px)
                    cash -= buy_fee + (0 if product == "futures" else qty * entry_px)
                    position = {"qty": qty, "lot": lot, "entry": entry_px, "stop": stop,
                                "target": entry_px + target_r * (entry_px - stop), "entry_time": b["timestamp"], "buy_fee": buy_fee,
                                "planned_risk": qty * unit + fixed}
                    entered = True
                else:
                    rejected["one_unit_exceeds_risk_budget" if product != "futures" else "one_lot_exceeds_risk_budget"] += 1
            pending = None
            last_bar_today = i == len(rows) - 1 or rows[i + 1][1].date() != today
            if position and raw_exit is None:
                if b["open"] <= position["stop"]:
                    raw_exit, reason = b["open"], "gap_stop"
                elif b["low"] <= position["stop"]:
                    raw_exit, reason = position["stop"], "stop_first_if_ambiguous"
                elif b["high"] >= position["target"]:
                    raw_exit, reason = position["target"], "target"
                elif strategy == "orb" and last_bar_today:
                    raw_exit, reason = b["close"], "session_close_proxy"
                elif i == len(rows) - 1:
                    raw_exit, reason = b["close"], "end_of_sample_proxy"
            if position and raw_exit is not None:
                exit_px = raw_exit * (1 - slip)
                q = position["qty"]
                sell_fee = leg("sell", iso, q * exit_px)
                cash += (q * (exit_px - position["entry"]) if product == "futures" else q * exit_px) - sell_fee
                pnl = q * (exit_px - position["entry"]) - position["buy_fee"] - sell_fee
                trades.append({"symbol": symbol, **position, "exit": exit_px, "exit_time": b["timestamp"],
                               "fees": position["buy_fee"] + sell_fee, "net_pnl": pnl,
                               "r_multiple": pnl / position["planned_risk"] if position["planned_risk"] > 0 else None, "reason": reason})
                position = None
            ok_entry = in_window and (member is None or member(symbol, iso))
            if strategy == "trend":
                history.append(b["close"])
                if len(history) > lookback:
                    current_mean = sum(history[-lookback:]) / lookback
                    if position is None and ok_entry:
                        eligible_bars += 1
                        if entry == "random":
                            pending = "buy" if rng.random() < rate else None
                        else:
                            previous_mean = sum(history[-lookback-1:-1]) / lookback
                            if history[-2] <= previous_mean and history[-1] > current_mean:
                                pending = "buy"
                    elif position and history[-1] < current_mean:
                        pending = "sell"
            elif today not in bad_days:
                if minute < 570:
                    opening.append(b["high"])
                elif len(opening) == 3 and not entered and position is None and minute < 900 and ok_entry:
                    eligible_bars += 1
                    if entry == "random":
                        pending = "buy" if rng.random() < rate else None
                    elif b["close"] > max(opening):
                        pending = "buy"
            if in_window:
                mark = (position["qty"] * (b["close"] - position["entry"]) if product == "futures" else position["qty"] * b["close"]) if position else 0
                points[b["timestamp"]] = cash + mark
        sleeves[symbol] = points
    times = sorted({t for points in sleeves.values() for t in points})
    if not times:
        raise ValueError("no bars inside the requested window")
    last = {s: allocation for s in sleeves}
    curve, peak, max_dd = [], capital, 0.0
    for t in times:
        for s, points in sleeves.items():
            if t in points:
                last[s] = points[t]
        equity = sum(last.values())
        peak = max(peak, equity)
        dd = (equity / peak - 1) * 100
        max_dd = min(max_dd, dd)
        curve.append({"timestamp": t, "equity": round(equity, 6), "drawdown_pct": round(dd, 6)})
    trades = [t for t in trades if not start or parse_time(t["entry_time"]).astimezone(IST).date().isoformat() >= start]
    wins = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    losses = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]
    rs = [t["r_multiple"] for t in trades if t["r_multiple"] is not None]
    end_eq = curve[-1]["equity"]
    warnings = ["Educational reference strategy; not validated alpha.",
                "Fixed equal-cash sleeves; no dynamic portfolio reallocation, leverage or shorting.",
                ("Costs: dated NSE statutory charges for the '" + product + "' product and broker preset '" + broker + "'; estimates, check your contract note."
                 if costs == "india" else "Fee bps are a user-defined aggregate approximation, not a statutory tax calculator."),
                "Slippage is deterministic; depth, partial fills and price bands are not modelled.",
                "End-of-sample/session liquidation uses a close-price proxy; not a guaranteed executable fill.",
                "Without a membership file no constituent filtering is applied. Historical selection and missing delisted prices can bias results.",
                "Maximum drawdown uses bar-close marks and can understate intrabar losses."]
    if product == "futures":
        warnings.append(f"Futures: whole lots, margin {margin_pct:g}% of notional, prices treated as one continuous contract (no roll costs or basis).")
    if skipped:
        warnings.append(f"ORB skipped {sum(len(v) for v in skipped.values())} incomplete or non-standard sessions; see skipped_sessions.")
    if jumps:
        warnings.append(f"{len(jumps)} suspected unadjusted splits or bonuses were allowed through; returns across them are unreliable.")
    if entry == "random":
        warnings.append(f"RANDOM ENTRIES (seed {seed}, rate {rate:g} per eligible bar): a null model for comparison, not a strategy.")
    return {"label": "HISTORICAL_SIMULATION", "strategy": strategy,
            "parameters": {"capital": capital, "lookback": lookback, "risk_pct": risk_pct, "stop_pct": stop_pct,
                           "target_r": target_r, "costs": costs, "fee_bps": fee_bps if costs == "bps" else None, "product": product,
                           "broker": broker if costs == "india" else None, "slippage_bps": slippage_bps, "cost_stress": cost_stress,
                           "start": start, "end": end, "entry": entry, "seed": seed, "margin_pct": margin_pct if product == "futures" else None,
                           "membership_filter": member is not None},
            "metrics": {"initial_capital": capital, "ending_equity": end_eq, "net_pnl": round(end_eq-capital, 6),
                        "net_return_pct": round((end_eq/capital-1)*100, 6), "max_drawdown_pct": round(max_dd, 6),
                        "trades": len(trades), "win_rate_pct": 100*len(wins)/len(trades) if trades else None,
                        "expectancy_inr": sum(t["net_pnl"] for t in trades)/len(trades) if trades else None,
                        "expectancy_r": sum(rs)/len(rs) if rs else None,
                        "profit_factor": sum(wins)/abs(sum(losses)) if losses else None,
                        "fees_inr": sum(t["fees"] for t in trades), "rejected_zero_quantity": sum(v for k, v in rejected.items() if k != "margin_reduced"),
                        "eligible_entry_bars": eligible_bars},
            "rejections": dict(rejected), "skipped_sessions": skipped, "suspect_corporate_actions": jumps[:20],
            "trades": trades, "equity": curve, "warnings": warnings}


def daily_returns(result):
    """Close-of-day equity returns from a result's equity curve (IST dates)."""
    last = {}
    for p in result["equity"]:
        last[parse_time(p["timestamp"]).astimezone(IST).date().isoformat()] = p["equity"]
    days = sorted(last)
    prev = result["metrics"]["initial_capital"]; out = {}
    for d in days:
        out[d] = last[d] / prev - 1; prev = last[d]
    return out
