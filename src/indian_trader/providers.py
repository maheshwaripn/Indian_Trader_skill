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


def bhavcopy(path, output):
    """Normalise legacy NSE cash-equity CSV. Reject unknown formats explicitly."""
    rows=[]
    with open(path,encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required={"SYMBOL","SERIES","OPEN","HIGH","LOW","CLOSE","TOTTRDQTY","TIMESTAMP"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Only legacy NSE CM bhavcopy columns supported here. New UDiFF format needs an explicit mapping; see docs/data.md.")
        for r in reader:
            if r["SERIES"].strip()!="EQ":
                continue
            d=datetime.strptime(r["TIMESTAMP"].strip(),"%d-%b-%Y").replace(hour=9,minute=15,tzinfo=timezone(timedelta(hours=5,minutes=30)))
            rows.append(dict(timestamp=d.isoformat(),symbol=r["SYMBOL"].strip(),open=r["OPEN"],high=r["HIGH"],low=r["LOW"],close=r["CLOSE"],volume=r["TOTTRDQTY"]))
    if not rows:
        raise ValueError("no EQ rows")
    save(rows,output)
    read_bars(output)
    return {"rows":len(rows),"output":str(output),"adjustment":"raw", "source":"user-supplied legacy NSE CM bhavcopy"}
