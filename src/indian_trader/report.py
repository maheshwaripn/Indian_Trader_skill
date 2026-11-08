"""Offline dashboard. No CDN, external scripts, tracking or account connection."""
import html
import json
from pathlib import Path

METRICS = {
    "net_return_pct": ("Net return %", "Ending equity / starting capital − 1, after modelled costs. Compare equal periods and risk."),
    "max_drawdown_pct": ("Max drawdown %", "Largest bar-close decline from a prior equity peak. Intrabar loss can be worse."),
    "trades": ("Completed trades", "Sample size, not independent observations. Correlated trades reduce evidence strength."),
    "win_rate_pct": ("Win rate %", "Profitable closed trades / all closed trades. A high win rate can coexist with losses."),
    "expectancy_inr": ("Expectancy INR", "Average net P&L per completed trade. Position sizing affects this measure."),
    "expectancy_r": ("Expectancy R", "Average net result per trade in multiples of the planned risk (R). Independent of position size; below zero after costs means no edge in this sample."),
    "profit_factor": ("Profit factor", "Sum of winning net P&L / absolute losing net P&L. Undefined with no losses; not proof of safety."),
    "fees_inr": ("Fees INR", "Aggregate simulated fees. Slippage is embedded in fills. Actual statutory and broker charges may differ."),
    "ending_equity": ("Ending equity INR", "Cash plus marked holdings. Compare with starting capital; beware incomplete data."),
}


def dashboard(result, output):
    def esc(x):
        return html.escape(str(x))
    cards = []
    for k, (label, helptext) in METRICS.items():
        v = result["metrics"].get(k)
        display = "N/A" if v is None else f"{v:,.2f}"
        cards.append(f'<article><span>{esc(label)}</span><strong>{display}</strong><details><summary>How to read this</summary><p>{esc(helptext)}</p></details></article>')
    points = result["equity"]
    values = [p["equity"] for p in points]
    low, high = min(values), max(values)
    # Display downsampling only; full numerical series remains in result.json.
    stride = max(1, len(points)//800)
    indexes = sorted(set(range(0,len(points),stride)) | {len(points)-1})
    coords = " ".join(f'{20+i/max(1,len(points)-1)*960:.2f},{220-(values[i]-low)/max(1e-9,high-low)*180:.2f}' for i in indexes)
    rows = "".join('<tr>'+''.join(f'<td>{esc(t.get(k,""))}</td>' for k in ("symbol","entry_time","exit_time","qty","entry","exit","net_pnl","r_multiple","reason"))+'</tr>' for t in result["trades"])
    warnings = "".join(f"<li>{esc(w)}</li>" for w in result["warnings"])
    provenance = esc(json.dumps(result.get("provenance",{}),indent=2))
    out = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Indian Trader · Research report</title><style>
:root{{color-scheme:dark}}body{{background:#0b1220;color:#e6edf7;font:16px system-ui;max-width:1200px;margin:auto;padding:28px}}h1{{font-size:32px}}h2{{margin-top:32px}}.badge{{color:#83dfca;letter-spacing:.08em}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}}article{{background:#152136;border:1px solid #2a3a52;border-radius:12px;padding:18px}}strong{{display:block;font-size:28px;margin:12px 0}}span,small{{color:#b9c9dd}}summary{{cursor:pointer;color:#83dfca}}p,li{{line-height:1.6}}svg{{width:100%;height:auto;background:#152136;border-radius:12px}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{padding:10px;border-bottom:1px solid #2a3a52;text-align:left}}.scroll{{overflow:auto}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}input{{padding:10px;background:#152136;color:white;border:1px solid #52647c}}footer{{margin:30px 0;color:#b9c9dd}}
</style><header><p class="badge">EDUCATIONAL · {esc(result['label'])}</p><h1>Indian Trader Research</h1><p>Strategy: {esc(result['strategy'])} · Read the evidence before interpreting returns.</p></header>
<section class="cards">{''.join(cards)}</section><h2>Equity through time</h2>
<svg viewBox="0 0 1000 250" role="img" aria-label="Portfolio equity curve"><polyline points="{coords}" fill="none" stroke="#83dfca" stroke-width="3"/></svg>
<p>Range INR {low:,.2f}–{high:,.2f}. From {esc(points[0]['timestamp'])} to {esc(points[-1]['timestamp'])}. X-axis follows observed bars, not equal calendar intervals.</p>
<h2>Trade review</h2><label>Filter trades <input id="filter" placeholder="Symbol or exit reason"></label><p id="count"></p><div class="scroll"><table><thead><tr>{''.join('<th>'+x+'</th>' for x in ['Symbol','Entry UTC','Exit UTC','Qty','Entry price','Exit price','Net INR','R','Reason'])}</tr></thead><tbody id="trades">{rows}</tbody></table></div>
<h2>Evidence and limitations</h2><ul>{warnings}</ul><details><summary>Run provenance</summary><pre>{provenance}</pre></details>
<h2>What to do next</h2><p>Check data coverage, compare a simple baseline, test costs, and inspect untouched periods. Do not select a strategy solely from this report. No benchmark or out-of-sample validation is implied.</p>
<footer>Educational software. You own investment decisions and financial risk. Historical simulation is not a forecast. No broker connection or live orders.</footer>
<script>const f=document.getElementById('filter'),rs=[...document.querySelectorAll('#trades tr')];function update(){{let n=0;for(const r of rs){{r.hidden=!r.textContent.toLowerCase().includes(f.value.toLowerCase());if(!r.hidden)n++;}}document.getElementById('count').textContent=n+' of '+rs.length+' trades shown';}}f.addEventListener('input',update);update();</script></html>'''
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(out,encoding="utf-8")
    return str(output)


def brief(result, limit=5):
    return {"label": result["label"], "strategy": result["strategy"], "metrics": result["metrics"],
            "parameters": result["parameters"], "warnings": result["warnings"],
            "provenance": result.get("provenance",{}),
            "worst_trades": sorted(result["trades"],key=lambda t:t["net_pnl"])[:limit],
            "review_prompt": "Explain the evidence, identify missing assumptions, compare a simpler baseline, and propose one falsifiable next experiment. Do not infer live readiness."}
