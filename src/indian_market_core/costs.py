"""Dated Indian transaction charges for cash and derivatives on NSE. Estimates for research, not a contract note.

Statutory items (STT, exchange transaction charge, SEBI fee, stamp duty, IPFT, GST) follow the dates below. Brokerage and
depository charges depend on the broker; the presets are examples to check against your own rate card. Verify the
current schedule on the NSE and broker websites before relying on a number. Sources are listed in docs/costs.md."""
from datetime import date
import math

PRODUCTS = ("delivery", "intraday", "futures", "options")
# (effective from, values). Rates are fractions of traded value (options: of premium).
SCHEDULE = {
    "delivery": [("2000-01-01", dict(stt_buy=0.001, stt_sell=0.001, exchange=0.0000325, stamp_buy=0.00015, ipft=0.000001)),
                 ("2024-10-01", dict(stt_buy=0.001, stt_sell=0.001, exchange=0.0000297, stamp_buy=0.00015, ipft=0.000001))],
    "intraday": [("2000-01-01", dict(stt_buy=0.0, stt_sell=0.00025, exchange=0.0000325, stamp_buy=0.00003, ipft=0.000001)),
                 ("2024-10-01", dict(stt_buy=0.0, stt_sell=0.00025, exchange=0.0000297, stamp_buy=0.00003, ipft=0.000001))],
    "futures": [("2000-01-01", dict(stt_buy=0.0, stt_sell=0.0001, exchange=0.000019, stamp_buy=0.00002, ipft=0.000001)),
                ("2023-04-01", dict(stt_buy=0.0, stt_sell=0.000125, exchange=0.000019, stamp_buy=0.00002, ipft=0.000001)),
                ("2024-10-01", dict(stt_buy=0.0, stt_sell=0.0002, exchange=0.0000173, stamp_buy=0.00002, ipft=0.000001)),
                ("2026-04-01", dict(stt_buy=0.0, stt_sell=0.0005, exchange=0.0000173, stamp_buy=0.00002, ipft=0.000001))],
    "options": [("2000-01-01", dict(stt_buy=0.0, stt_sell=0.0005, exchange=0.00053, stamp_buy=0.00003, ipft=0.000005)),
                ("2023-04-01", dict(stt_buy=0.0, stt_sell=0.000625, exchange=0.00053, stamp_buy=0.00003, ipft=0.000005)),
                ("2024-10-01", dict(stt_buy=0.0, stt_sell=0.001, exchange=0.0003503, stamp_buy=0.00003, ipft=0.000005)),
                ("2026-04-01", dict(stt_buy=0.0, stt_sell=0.0015, exchange=0.0003503, stamp_buy=0.00003, ipft=0.000005))],
}
SEBI, GST = 0.000001, 0.18
# Brokerage per executed order: (fraction of value, cap in INR). delivery_free: no delivery brokerage. dp: INR per delivery sell, before GST.
BROKERS = {
    "flat20": dict(pct=None, cap=20.0, delivery_free=False, dp=0.0),
    "discount": dict(pct=0.0003, cap=20.0, delivery_free=True, dp=13.5),
    "zero": dict(pct=None, cap=0.0, delivery_free=True, dp=0.0),
}


def rates(product, on):
    if product not in SCHEDULE:
        raise ValueError(f"product must be one of {', '.join(PRODUCTS)}")
    day = on if isinstance(on, str) else on.isoformat()
    day = date.fromisoformat(day[:10]).isoformat()
    if not "2023-04-01" <= day <= "2026-11-08":
        raise ValueError("Indian charge estimates cover 2023-04-01 through 2026-11-08 only; use explicit bps outside coverage")
    current = None
    for start, values in SCHEDULE[product]:
        if day[:10] >= start:
            current = values
    result = dict(current, sebi=SEBI, gst=GST)
    if day >= "2026-03-01":
        # NSE/FA/73061: unchanged combined outflow, revised component allocation.
        combined = result["exchange"] + result["ipft"]
        result.update(exchange=combined-0.000000001, ipft=0.000000001)
    return result


def brokerage(product, value, broker="flat20"):
    b = BROKERS.get(broker)
    if b is None:
        raise ValueError(f"broker preset must be one of {', '.join(BROKERS)}")
    if not math.isfinite(value) or value < 0:
        raise ValueError("traded value must be finite and nonnegative")
    if value == 0:
        return 0.0
    if product == "delivery" and b["delivery_free"]:
        return 0.0
    return b["cap"] if b["pct"] is None else min(b["pct"] * value, b["cap"])


def leg(product, on, side, value, broker="flat20", brokerage_mult=1.0):
    """Charges for one executed order of the given traded value (premium value for options)."""
    if side not in ("buy", "sell"):
        raise ValueError("side must be buy or sell")
    if not math.isfinite(brokerage_mult) or brokerage_mult < 0:
        raise ValueError("brokerage multiplier must be finite and nonnegative")
    r = rates(product, on)
    brk = brokerage(product, value, broker) * brokerage_mult
    stt = value * (r["stt_buy"] if side == "buy" else r["stt_sell"])
    exch, sebi, ipft = value * r["exchange"], value * r["sebi"], value * r["ipft"]
    stamp = value * r["stamp_buy"] if side == "buy" else 0.0
    dp = BROKERS[broker]["dp"] * (1 + GST) if product == "delivery" and side == "sell" and value > 0 else 0.0
    gst = GST * (brk + exch + sebi + ipft)
    parts = dict(brokerage=brk, stt=stt, exchange=exch, sebi=sebi, ipft=ipft, stamp=stamp, gst=gst, dp=dp)
    return dict(total=sum(parts.values()), **parts)


def round_trip(product, buy_on, sell_on, qty, buy_price, sell_price, broker="flat20"):
    if not all(math.isfinite(x) and x >= 0 for x in (qty, buy_price, sell_price)):
        raise ValueError("quantity and prices must be finite and nonnegative")
    b = leg(product, buy_on, "buy", qty * buy_price, broker)
    s = leg(product, sell_on, "sell", qty * sell_price, broker)
    return {"product": product, "buy": b, "sell": s, "total": b["total"] + s["total"],
            "note": "Estimate from dated statutory rates and a broker preset; check your contract note."}


def variable_rate(product, on, side):
    """Value-proportional part of one leg, used for position sizing."""
    if side not in ("buy", "sell"):
        raise ValueError("side must be buy or sell")
    r = rates(product, on)
    stt = r["stt_buy"] if side == "buy" else r["stt_sell"]
    stamp = r["stamp_buy"] if side == "buy" else 0.0
    return stt + stamp + (r["exchange"] + r["sebi"] + r["ipft"]) * (1 + GST)


def today():
    return date.today().isoformat()
