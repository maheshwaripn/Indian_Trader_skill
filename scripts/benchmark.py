"""Offline reproducible payload/runtime benchmark; byte counts are not tokens."""
import json
import tempfile
import time
from pathlib import Path
from indian_trader.cli import demo
from indian_trader.core import read_bars
from indian_trader.research import run
from indian_trader.report import brief

with tempfile.TemporaryDirectory() as tmp:
    p=demo(Path(tmp)/"demo.csv")
    start=time.perf_counter()
    result=run(read_bars(p))
    seconds=time.perf_counter()-start
    full=len(json.dumps(result).encode())
    compact=len(json.dumps(brief(result)).encode())
    print(json.dumps({"task":"seeded offline demo","seconds":seconds,"full_result_bytes":full,"brief_bytes":compact,"payload_reduction_pct":100*(1-compact/full),"ai_calls":0,"note":"Payload bytes are not measured model tokens, billing or quality improvement."},indent=2))
