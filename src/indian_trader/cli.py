"""Stable model-independent CLI. Run --help; network occurs only in fetch-yahoo."""
import argparse
import csv
import json
import os
import platform
import random
import shutil
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import __version__
from . import bank, calendar, coach, costs, paper, providers, report, research, universe, validation
from .core import PROFILES, digest, quality, read_bars, stamp, write_json


def emit(obj):
    print(json.dumps(obj,indent=2,allow_nan=False))


def config(a):
    p=Path(a.workspace)/"config.json"
    cfg=json.loads(p.read_text()) if p.exists() else {"mode":"assisted"}
    mode=a.mode or cfg.get("mode","assisted")
    if mode not in PROFILES:
        raise ValueError("unknown resource mode")
    return mode, PROFILES[mode]


def demo(path):
    rng=random.Random(42)
    rows=[]
    d=datetime(2024,1,1,9,15,tzinfo=timezone(timedelta(hours=5,minutes=30)))
    for symbol,initial in (("DEMO_A",100),("DEMO_B",200)):
        p=initial
        for i in range(180):
            day=d+timedelta(days=i)
            if day.weekday()>=5:
                continue
            o=p*(1+rng.uniform(-.008,.008))
            p=o*(1+rng.uniform(-.025,.025))
            rows.append(dict(timestamp=day.isoformat(),symbol=symbol,open=o,high=max(o,p)*1.01,low=min(o,p)*.99,close=p,volume=100000))
    providers.save(rows,path)
    return path


def strategy_args(x):
    x.add_argument("--strategy",choices=["trend","orb"],default="trend");x.add_argument("--capital",type=float,default=100000);x.add_argument("--lookback",type=int,default=20)
    x.add_argument("--risk-pct",type=float,default=.5);x.add_argument("--stop-pct",type=float,default=2);x.add_argument("--target-r",type=float,default=2)
    x.add_argument("--costs",choices=["india","bps"],help="india (default): dated NSE charges + broker preset; bps: flat --fee-bps per side");x.add_argument("--fee-bps",type=float)
    x.add_argument("--product",choices=["delivery","intraday","futures"]);x.add_argument("--broker",choices=list(costs.BROKERS),default="flat20");x.add_argument("--slippage-bps",type=float,default=5);x.add_argument("--cost-stress",type=float,default=1.0)
    x.add_argument("--universe",help="NiftyHistory-style membership CSV: enter only when the symbol was a member");x.add_argument("--index",default="Nifty500");x.add_argument("--allow-unverified",action="store_true")
    x.add_argument("--lots",help="CSV symbol,effective_date,lot (futures)");x.add_argument("--margin-pct",type=float,default=20.0)
    x.add_argument("--strict-sessions",action="store_true");x.add_argument("--allow-suspect-jumps",action="store_true")


def strategy_params(a):
    p={k:getattr(a,k) for k in ("strategy","capital","lookback","risk_pct","stop_pct","target_r","fee_bps","slippage_bps","costs","product","broker","cost_stress","margin_pct","strict_sessions","allow_suspect_jumps")}
    if a.universe:
        p["member"]=universe.membership(a.universe,a.index,a.allow_unverified)
    if a.lots:
        p["lots"]=load_lots(a.lots)
    return p


def load_lots(path):
    lots={}
    with open(path,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            lot=int(r["lot"])
            if lot<1: raise ValueError("lot must be a positive integer")
            lots.setdefault(r["symbol"].strip(),[]).append((r["effective_date"].strip(),lot))
    return {k:sorted(v) for k,v in lots.items()}


def parser():
    p=argparse.ArgumentParser(description="Educational Indian equity research. No live orders.")
    p.add_argument("--version",action="version",version=__version__)
    p.add_argument("--workspace",default="workspace")
    p.add_argument("--mode",choices=list(PROFILES))
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor")
    x=sub.add_parser("init"); x.add_argument("--source",choices=["csv","parquet","yahoo","nse","dhan","zerodha"],default="csv"); x.add_argument("--interactive",action="store_true")
    sub.add_parser("demo")
    x=sub.add_parser("validate"); x.add_argument("file")
    x=sub.add_parser("ingest"); x.add_argument("file"); x.add_argument("--name",required=True); x.add_argument("--source",required=True);x.add_argument("--adjustment",choices=["raw","adjusted","unknown"],default="unknown")
    sub.add_parser("catalogue");sub.add_parser("verify-bank")
    x=sub.add_parser("universe-audit");x.add_argument("file");x.add_argument("--output")
    x=sub.add_parser("universe-asof");x.add_argument("file");x.add_argument("--date",required=True);x.add_argument("--index",default="Nifty500");x.add_argument("--allow-unverified",action="store_true")
    x=sub.add_parser("research");x.add_argument("file");strategy_args(x);x.add_argument("--start");x.add_argument("--end");x.add_argument("--entry",choices=["rule","random"],default="rule");x.add_argument("--seed",type=int)
    x=sub.add_parser("evaluate");x.add_argument("file");strategy_args(x);x.add_argument("--dev",nargs=2,required=True,metavar=("START","END"));x.add_argument("--val",nargs=2,required=True,metavar=("START","END"));x.add_argument("--final",nargs=2,metavar=("START","END"));x.add_argument("--open-final",action="store_true");x.add_argument("--seeds",type=int,default=30);x.add_argument("--min-trades",type=int,default=30)
    x=sub.add_parser("sweep");x.add_argument("file");strategy_args(x);x.add_argument("--grid",required=True,help='JSON, e.g. {"lookback":[10,20,40],"stop_pct":[1,2,3]}');x.add_argument("--dev",nargs=2,required=True,metavar=("START","END"));x.add_argument("--min-trades",type=int,default=20);x.add_argument("--flips",type=int,default=1000)
    x=sub.add_parser("cost-calc");x.add_argument("--product",choices=list(costs.PRODUCTS),required=True);x.add_argument("--qty",type=float,required=True);x.add_argument("--buy-price",type=float,required=True);x.add_argument("--sell-price",type=float,required=True);x.add_argument("--buy-date",required=True);x.add_argument("--sell-date");x.add_argument("--broker",choices=list(costs.BROKERS),default="flat20")
    x=sub.add_parser("calendar-check");x.add_argument("file");x.add_argument("--calendar",action="append",help="extra calendar JSON in the bundled format")
    x=sub.add_parser("scan");x.add_argument("file");x.add_argument("--lookback",type=int,default=20)
    x=sub.add_parser("dashboard");x.add_argument("result");x.add_argument("--output",default="workspace/dashboard.html")
    x=sub.add_parser("brief");x.add_argument("result")
    x=sub.add_parser("coach");x.add_argument("spec")
    x=sub.add_parser("fetch-yahoo");x.add_argument("--symbol",required=True);x.add_argument("--start",required=True);x.add_argument("--end",required=True);x.add_argument("--output",required=True)
    x=sub.add_parser("convert-bhavcopy");x.add_argument("files",nargs="+");x.add_argument("--output",required=True);x.add_argument("--series",default="EQ")
    x=sub.add_parser("paper-init");x.add_argument("--capital",type=float,default=100000)
    sub.add_parser("paper-status")
    x=sub.add_parser("paper-fill");x.add_argument("--id",required=True);x.add_argument("--symbol",required=True);x.add_argument("--side",choices=["buy","sell"],required=True);x.add_argument("--qty",type=int,required=True);x.add_argument("--price",type=float,required=True);x.add_argument("--fee",type=float);x.add_argument("--auto-fee",choices=["delivery","intraday","futures","options"]);x.add_argument("--broker",choices=list(costs.BROKERS),default="flat20");x.add_argument("--at",help="fill time with UTC offset, e.g. 2026-11-09T10:05:00+05:30")
    x=sub.add_parser("paper-mark");x.add_argument("prices",help="canonical OHLCV file; the latest close per symbol marks open positions")
    return p


def execute(a):
    mode,profile=config(a)
    root=Path(a.workspace)
    ledger=root/"paper.sqlite"
    if a.command=="doctor":
        return {"python":platform.python_version(),"python_ok":sys.version_info>=(3,11),"os":platform.system(),"cpu_count":os.cpu_count(),"disk_free_gib":round(shutil.disk_usage('.').free/2**30,2),"mode":mode,"profile":profile,"ai_calls":0,"network_required":False,"note":"Single-process v0.1; row limits enforced. CPU/RAM quotas and AI review counts are guidance, not OS/session enforcement."}
    if a.command=="init":
        if (root/"config.json").exists():
            raise ValueError("configuration exists; edit it explicitly or select another workspace")
        if a.interactive:
            print("Modes: local, assisted, lab, vps. Source: csv, parquet, yahoo, nse, dhan, zerodha.")
            mode=input(f"Mode [{mode}]: ").strip() or mode
            a.source=input(f"Source [{a.source}]: ").strip() or a.source
            if mode not in PROFILES or a.source not in ("csv","parquet","yahoo","nse","dhan","zerodha"):
                raise ValueError("unknown mode or source")
        cfg={"mode":mode,"source":a.source,"operating_state":"research","ai_access":"manual","risk_owner":"user","live_orders_supported":False}
        write_json(root/"config.json",cfg)
        return {"configuration":cfg,"next":"Run demo, then read docs/data.md for your chosen source."}
    if a.command=="demo":
        path=demo(root/"demo.csv")
        result=research.run(read_bars(path,profile["max_rows"]))
        result["label"]="SYNTHETIC_DEMO_NOT_MARKET_DATA"
        result["provenance"]={"seed":42,"version":__version__,"data_sha256":digest(path)}
        write_json(root/"demo-result.json",result)
        report.dashboard(result,root/"demo-dashboard.html")
        write_json(root/"demo-brief.json",report.brief(result,profile["brief_candidates"]))
        return {"dashboard":str(root/"demo-dashboard.html"),"result":str(root/"demo-result.json"),"brief":str(root/"demo-brief.json"),"metrics":result["metrics"],"label":result["label"]}
    if a.command=="validate":
        return quality(read_bars(a.file,profile["max_rows"]))
    if a.command=="ingest":
        return bank.ingest(root/"bank",a.name,a.file,a.source,profile["max_rows"],a.adjustment)
    if a.command=="catalogue":
        return bank.catalogue(root/"bank")
    if a.command=="verify-bank":
        result=bank.verify(root/"bank")
        if any(not x["ok"] for x in result):
            raise ValueError("bank integrity check failed; inspect stored snapshots")
        return result
    if a.command=="universe-audit":
        result=universe.audit(a.file)
        if a.output:
            write_json(a.output,result)
            return {k:v for k,v in result.items() if k!="mismatches"}|{"details":a.output}
        return result
    if a.command=="universe-asof":
        return universe.asof(a.file,a.date,a.index,a.allow_unverified)
    if a.command=="research":
        started=time.perf_counter()
        bars=read_bars(a.file,profile["max_rows"])
        result=research.run(bars,**strategy_params(a),start=a.start,end=a.end,entry=a.entry,seed=a.seed)
        run_id=uuid.uuid4().hex[:12]
        folder=root/"runs"/run_id
        result["provenance"]={"run_id":run_id,"created_at":stamp(),"version":__version__,"data_sha256":digest(a.file),"mode":mode,"seconds":round(time.perf_counter()-started,4),"ai_calls":0,"data_quality":quality(bars)}
        write_json(folder/"result.json",result)
        write_json(folder/"brief.json",report.brief(result,profile["brief_candidates"]))
        report.dashboard(result,folder/"dashboard.html")
        return {"run_id":run_id,"folder":str(folder),"metrics":result["metrics"],"warnings":result["warnings"]}
    if a.command in ("evaluate","sweep"):
        bars=read_bars(a.file,profile["max_rows"]); params=strategy_params(a); run_id=uuid.uuid4().hex[:12]; folder=root/"runs"/run_id
        if a.command=="evaluate":
            out=validation.evaluate(bars,params,tuple(a.dev),tuple(a.val),tuple(a.final) if a.final else None,a.open_final,a.seeds,gates={"min_trades":a.min_trades})
        else:
            out=validation.sweep(bars,params,json.loads(a.grid),tuple(a.dev),a.min_trades,a.flips)
        out["parameters"]={k:v for k,v in params.items() if k not in ("member","lots")}|{"universe":a.universe,"lots":a.lots}
        out["provenance"]={"run_id":run_id,"created_at":stamp(),"version":__version__,"data_sha256":digest(a.file),"mode":mode,"ai_calls":0}
        write_json(folder/f"{a.command}.json",out)
        summary={k:out[k] for k in ("verdict","checks") if k in out} if a.command=="evaluate" else {"selected":out["selected"],"reality_check":out["reality_check"],"settings_tried":out["settings_tried"]}
        return {"run_id":run_id,"file":str(folder/f"{a.command}.json"),**summary}
    if a.command=="cost-calc":
        return costs.round_trip(a.product,a.buy_date,a.sell_date or a.buy_date,a.qty,a.buy_price,a.sell_price,a.broker)
    if a.command=="calendar-check":
        return calendar.check(read_bars(a.file,profile["max_rows"]),calendar.load(a.calendar))
    if a.command=="scan":
        if a.lookback<2:
            raise ValueError("lookback must be >=2")
        groups={}
        for b in read_bars(a.file,profile["max_rows"]):
            groups.setdefault(b["symbol"],[]).append(b)
        candidates=[]
        for s,rows in groups.items():
            if len(rows)>a.lookback:
                closes=[b["close"] for b in rows]
                avg=sum(closes[-a.lookback:])/a.lookback
                prior=sum(closes[-a.lookback-1:-1])/a.lookback
                if closes[-2]<=prior and closes[-1]>avg:
                    candidates.append({"symbol":s,"timestamp":rows[-1]["timestamp"],"close":closes[-1],"sma":avg,"signal":"close_crossed_above_sma"})
        write_json(root/"scan.json",{"candidates":candidates})
        return {"candidates":candidates[:profile["brief_candidates"]],"total":len(candidates),"universe_count":len(groups),"full_output":str(root/"scan.json"),"note":"Historical latest-bar screen, not a live signal. No PIT filtering implied."}
    if a.command=="dashboard":
        return {"dashboard":report.dashboard(json.loads(Path(a.result).read_text()),a.output)}
    if a.command=="brief":
        return report.brief(json.loads(Path(a.result).read_text()),profile["brief_candidates"])
    if a.command=="coach":
        return coach.review(json.loads(Path(a.spec).read_text()))
    if a.command=="fetch-yahoo":
        return providers.yahoo(a.symbol,a.start,a.end,a.output)
    if a.command=="convert-bhavcopy":
        return providers.bhavcopy(a.files,a.output,a.series)
    if a.command=="paper-init":
        return paper.initialize(ledger,a.capital)
    if a.command=="paper-status":
        return paper.status(ledger)
    if a.command=="paper-fill":
        fee=a.fee if a.fee is not None else (None if a.auto_fee else 0)
        return paper.fill(ledger,a.id,a.symbol,a.side,a.qty,a.price,fee,a.at,a.auto_fee,a.broker)
    if a.command=="paper-mark":
        return paper.status(ledger,paper.latest_prices(read_bars(a.prices,profile["max_rows"])))


def main():
    try:
        emit(execute(parser().parse_args()))
    except (ValueError,KeyError,OSError,ImportError) as e:
        print(f"ERROR: {e}",file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    sys.exit(main())
