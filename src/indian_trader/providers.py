"""Explicit opt-in data utilities; no order API methods."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .core import read_bars

FIELDS = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]


def save(rows, output):
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    with open(output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def yahoo(symbol, start, end, output):
    """Daily raw OHLC only. Provider adjustment decisions must be documented."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise ValueError('Install Yahoo extra: pip install -e ".[yahoo]"') from e
    frame = yf.Ticker(symbol).history(start=start,end=end,interval="1d",auto_adjust=False,actions=False)
    if frame.empty:
        raise ValueError("provider returned no data; check symbol, entitlement and dates")
    rows=[]
    for t,r in frame.iterrows():
        if t.tzinfo is None:
            raise ValueError("provider timestamp lacks timezone")
        # Explicit daily bar opening timestamp; provider index often uses midnight.
        dt=t.to_pydatetime().replace(hour=9,minute=15,second=0,microsecond=0)
        if dt.date() >= datetime.now(dt.tzinfo).date():
            continue # exclude the current, potentially incomplete daily bar
        rows.append(dict(timestamp=dt.isoformat(),symbol=symbol,open=float(r["Open"]),high=float(r["High"]),low=float(r["Low"]),close=float(r["Close"]),volume=float(r["Volume"])))
    if not rows:
        raise ValueError("no completed historical daily bars")
    save(rows,output)
    read_bars(output)
    return {"output":str(output),"rows":len(rows),"source":"Yahoo via yfinance", "adjustment":"raw; corporate-action handling required", "end":"exclusive"}


IST = timezone(timedelta(hours=5, minutes=30))
LEGACY = {"SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "TOTTRDQTY", "TIMESTAMP"}
# NSE CM bhavcopy in the UDiFF layout (BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv), used from July 2024.
UDIFF = {"TradDt", "TckrSymb", "SctySrs", "OpnPric", "HghPric", "LwPric", "ClsPric", "TtlTradgVol"}


def bhavcopy(paths, output, series="EQ"):
    """Normalise one or more NSE cash-market bhavcopies (legacy or UDiFF layout, one series, default EQ) into one canonical file. Unknown layouts are rejected."""
    paths = [paths] if isinstance(paths, (str, bytes)) or hasattr(paths, "suffix") else list(paths)
    rows, layouts = [], set()
    for path in paths:
        layouts.add(_bhav_one(path, series, rows))
    if not rows:
        raise ValueError(f"no {series} rows")
    rows.sort(key=lambda r: (r["symbol"], r["timestamp"]))
    save(rows, output)
    read_bars(output, max(500000, len(rows)))
    return {"rows": len(rows), "files": len(paths), "output": str(output), "layout": sorted(layouts), "series": series, "adjustment": "raw", "source": "user-supplied NSE CM bhavcopy"}


def _bhav_one(path, series, rows):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.strip() for c in reader.fieldnames or []}
        if LEGACY <= cols:
            layout = "legacy"
            for r in reader:
                r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
                if r["SERIES"] != series:
                    continue
                d = datetime.strptime(r["TIMESTAMP"], "%d-%b-%Y").replace(hour=9, minute=15, tzinfo=IST)
                rows.append(dict(timestamp=d.isoformat(), symbol=r["SYMBOL"], open=r["OPEN"], high=r["HIGH"], low=r["LOW"], close=r["CLOSE"], volume=r["TOTTRDQTY"]))
        elif UDIFF <= cols:
            layout = "udiff"
            for r in reader:
                r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
                if r["SctySrs"] != series or (r.get("FinInstrmTp") not in (None, "", "STK")):
                    continue
                d = datetime.strptime(r["TradDt"], "%Y-%m-%d").replace(hour=9, minute=15, tzinfo=IST)
                rows.append(dict(timestamp=d.isoformat(), symbol=r["TckrSymb"], open=r["OpnPric"], high=r["HghPric"], low=r["LwPric"], close=r["ClsPric"], volume=r["TtlTradgVol"]))
        else:
            raise ValueError("Unknown bhavcopy layout: expected legacy NSE CM (SYMBOL, SERIES, OPEN ...) or UDiFF (TradDt, TckrSymb, SctySrs, OpnPric ...) columns; see docs/data.md.")
    return layout
