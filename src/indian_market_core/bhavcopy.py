"""NSE cash bhavcopy layout conversion; output remains raw, never adjusted."""
import csv
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
LEGACY = {"SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE", "TOTTRDQTY", "TIMESTAMP"}
# NSE CM bhavcopy in the UDiFF layout (BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv), used from July 2024.
UDIFF = {"TradDt", "TckrSymb", "SctySrs", "OpnPric", "HghPric", "LwPric", "ClsPric", "TtlTradgVol"}


def read_one(path, series, rows):
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
