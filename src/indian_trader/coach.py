"""Deterministic completeness checklist; substantive critique is an AI/user task."""
import re

REQUIRED = {
    "hypothesis": "Explain why an edge could exist; indicators alone are not a mechanism.",
    "universe": "Define instruments and historical membership to avoid selection bias.",
    "timeframe": "Define bar interval and completed-bar timing.",
    "entry": "Specify an executable trigger and next available fill.",
    "exit": "Define stop, profit-taking, time exit and invalidation.",
    "sizing": "Specify capital, position sizing and rounding.",
    "portfolio_limits": "Define concentration, aggregate exposure and correlated risk.",
    "costs": "Include fees, spread, slippage and adverse gap scenarios.",
    "data": "Specify source, adjustments, coverage and missing-data treatment.",
    "validation": "Predefine baselines, unseen periods and rejection criteria.",
}


def review(spec):
    if not isinstance(spec, dict):
        raise ValueError("strategy specification must be a JSON object")
    gaps=[{"field":k,"why":v,"options":["Explain with an example","Propose a documented assumption","I will specify it"]} for k,v in REQUIRED.items() if not isinstance(spec.get(k), str) or not spec[k].strip()]
    unresolved=[k for k in REQUIRED if isinstance(spec.get(k),str) and re.search(r"\b(unknown|unresolved|tbd|todo|undecided)\b",spec[k],re.I)]
    return {"unresolved_fields":unresolved,"status":"INCOMPLETE" if gaps or unresolved else "READY_FOR_RESEARCH_REVIEW_NOT_VALIDATED",
            "missing":gaps,"next":"Freeze a baseline, test one change, record all trials and inspect net results on untouched periods.",
            "questions":["What result would disprove your hypothesis?","What simpler strategy should this beat?","Could fewer trades explain the apparent improvement?"],
            "warning":"Completeness is not evidence of profitability. No natural-language strategy is automatically executed."}
