"""Long-only reference engines. Independent equal-cash sleeves, next-open fills."""
import math
from collections import defaultdict
from datetime import timedelta, timezone
from .core import finite, parse_time

IST = timezone(timedelta(hours=5, minutes=30))


def run(bars, strategy="trend", capital=100000, lookback=20, risk_pct=0.5,
        stop_pct=2, target_r=2, fee_bps=10, slippage_bps=5):
    for name, val in (("capital", capital), ("risk_pct", risk_pct), ("stop_pct", stop_pct), ("target_r", target_r)):
        finite(val, name, strict=True)
    if risk_pct > 100 or stop_pct >= 100:
        raise ValueError("risk_pct must be <=100 and stop_pct <100")
    finite(fee_bps, "fee_bps")
    finite(slippage_bps, "slippage_bps")
    if fee_bps >= 10000 or slippage_bps >= 10000:
        raise ValueError("basis points must be below 10000")
    if lookback < 2:
        raise ValueError("lookback must be >=2")
    if strategy not in ("trend", "orb"):
        raise ValueError("unknown strategy")
    groups = defaultdict(list)
    for b in bars:
        groups[b["symbol"]].append(b)
    allocation = capital / len(groups)
    fee, slip = fee_bps / 10000, slippage_bps / 10000
    trades, sleeves, rejected = [], {}, 0
    for symbol, rows in sorted(groups.items()):
        cash, position, pending, history, points = allocation, None, None, [], {}
        day, opening, entered = None, [], False
        if strategy == "orb":
            sessions = defaultdict(list)
            for b in rows:
                t = parse_time(b["timestamp"]).astimezone(IST)
                sessions[t.date()].append(t.hour * 60 + t.minute)
            expected = list(range(555, 930, 5))
            if any(slots != expected for slots in sessions.values()):
                raise ValueError("ORB requires complete standard 09:15–15:25 IST 5-minute sessions. Special sessions need separate support.")
        else:
            dates = [parse_time(b["timestamp"]).astimezone(IST).date() for b in rows]
            if len(dates) != len(set(dates)):
                raise ValueError("trend requires one daily bar per symbol per date")
        for i, b in enumerate(rows):
            local = parse_time(b["timestamp"]).astimezone(IST)
            minute = local.hour * 60 + local.minute
            today = local.date()
            if day != today:
                day, opening, entered = today, [], False
            # Orders based only on the previous completed bar.
            if pending == "sell" and position:
                raw_exit, reason = b["open"], "signal_next_open"
            else:
                raw_exit, reason = None, None
            if pending == "buy" and position is None:
                entry = b["open"] * (1 + slip)
                stop = entry * (1 - stop_pct / 100)
                # Expected stop loss includes exit slippage and both-side fee allowance.
                unit_risk = entry - stop * (1 - slip) + fee * (entry + stop * (1 - slip))
                qty = math.floor(min(cash / (entry * (1 + fee)), cash * risk_pct / 100 / unit_risk))
                if qty:
                    buy_fee = qty * entry * fee
                    cash -= qty * entry + buy_fee
                    position = {"qty": qty, "entry": entry, "stop": stop,
                                "target": entry + target_r * (entry - stop), "entry_time": b["timestamp"], "buy_fee": buy_fee}
                    entered = True
                else:
                    rejected += 1
            pending = None
            if position and raw_exit is None:
                if b["open"] <= position["stop"]:
                    raw_exit, reason = b["open"], "gap_stop"
                elif b["low"] <= position["stop"]:
                    raw_exit, reason = position["stop"], "stop_first_if_ambiguous"
                elif b["high"] >= position["target"]:
                    raw_exit, reason = position["target"], "target"
                elif strategy == "orb" and minute == 925:
                    raw_exit, reason = b["close"], "session_close_proxy"
                elif i == len(rows) - 1:
                    raw_exit, reason = b["close"], "end_of_sample_proxy"
            if position and raw_exit is not None:
                exit_price = raw_exit * (1 - slip)
                sell_fee = position["qty"] * exit_price * fee
                cash += position["qty"] * exit_price - sell_fee
                pnl = position["qty"] * (exit_price - position["entry"]) - position["buy_fee"] - sell_fee
                trades.append({"symbol": symbol, **position, "exit": exit_price, "exit_time": b["timestamp"],
                               "fees": position["buy_fee"] + sell_fee, "net_pnl": pnl, "reason": reason})
                position = None
            if strategy == "trend":
                history.append(b["close"])
                if len(history) > lookback:
                    previous_mean = sum(history[-lookback-1:-1]) / lookback
                    current_mean = sum(history[-lookback:]) / lookback
                    if position is None and history[-2] <= previous_mean and history[-1] > current_mean:
                        pending = "buy"
                    elif position and history[-1] < current_mean:
                        pending = "sell"
            else:
                if minute < 570:
                    opening.append(b["high"])
                elif len(opening) == 3 and not entered and position is None and minute < 900:
                    if b["close"] > max(opening):
                        pending = "buy"
            points[b["timestamp"]] = cash + (position["qty"] * b["close"] if position else 0)
        sleeves[symbol] = points
    times = sorted({t for points in sleeves.values() for t in points})
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
    wins = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    losses = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]
    end = curve[-1]["equity"]
    return {"label": "HISTORICAL_SIMULATION", "strategy": strategy,
            "parameters": {"capital": capital, "lookback": lookback, "risk_pct": risk_pct, "stop_pct": stop_pct,
                           "target_r": target_r, "fee_bps": fee_bps, "slippage_bps": slippage_bps},
            "metrics": {"initial_capital": capital, "ending_equity": end, "net_pnl": round(end-capital, 6),
                        "net_return_pct": round((end/capital-1)*100, 6), "max_drawdown_pct": round(max_dd, 6),
                        "trades": len(trades), "win_rate_pct": 100*len(wins)/len(trades) if trades else None,
                        "expectancy_inr": sum(t["net_pnl"] for t in trades)/len(trades) if trades else None,
                        "profit_factor": sum(wins)/abs(sum(losses)) if losses else None,
                        "fees_inr": sum(t["fees"] for t in trades), "rejected_zero_quantity": rejected},
            "trades": trades, "equity": curve,
            "warnings": ["Educational reference strategy; not validated alpha.",
                         "Fixed equal-cash sleeves; no dynamic portfolio reallocation, leverage or shorting.",
                         "Fee bps are a user-defined aggregate approximation, not a statutory tax calculator.",
                         "Slippage is deterministic; depth, partial fills and price bands are not modelled.",
                         "End-of-sample/session liquidation uses a close-price proxy; not a guaranteed executable fill.",
                         "No constituent filtering is applied automatically. Historical selection and missing delisted prices can bias results.",
                         "Maximum drawdown uses bar-close marks and can understate intrabar losses."]}
