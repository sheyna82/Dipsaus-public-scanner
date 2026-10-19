"""Conservative event opportunity research; never emits executable buy signals."""
from datetime import date, timedelta

def classify_event_opportunities(event_date, today, metrics=None):
    """Return research stages and evidence requirements, not probabilistic predictions.

    metrics may contain fresh, independently verified prices/option implied moves.
    Missing inputs MUST NOT be filled with guesses.
    """
    if isinstance(event_date,str):
        event_date=date.fromisoformat(event_date)
    if today is None: today=date.today()
    delta=(event_date-today).days
    m=metrics or {}
    result=[]
    if 2<=delta<=10:
        result.append({"stage":"PRE_EVENT_RUN_UP","eligible":False,
          "reason":"Research only: confirm higher low/retest, liquidity, R/R, gross EUR3500 potential and exit before release",
          "event_risk":"Exit before release unless separate EVENT_HOLD assessment approves exposure"})
    if 0<=delta<=3:
        required=("issuer_confirmed_date","fresh_quote","implied_move_pct","historical_event_moves",
                  "consensus_and_guidance","downside_gap_stress_pct","upside_scenario_pct")
        missing=[k for k in required if k not in m]
        result.append({"stage":"EVENT_HOLD","eligible":False,
          "reason":("Insufficient evidence: "+", ".join(missing)) if missing else
                   "Manual high-risk review required; option implied move does not imply direction; stop-loss cannot cap gap loss",
          "event_risk":"Binary gap risk; no automated buy, sizing or assumed win probability"})
    if -3<=delta<=0:
        result.append({"stage":"POST_EVENT_RECOVERY","eligible":False,
          "reason":"Wait for actual results, guidance, fresh post-release quotes, confirmed higher low/retest, spread and R/R",
          "event_risk":"Do not chase first gap or assume historical levels remain valid"})
    return result

def event_research_text(symbol,event_date,today,metrics=None):
    stages=classify_event_opportunities(event_date,today,metrics)
    if not stages:return None
    details=" | ".join(x["stage"]+": "+x["reason"] for x in stages)
    return (f"{symbol}: EVENT OPPORTUNITY RESEARCH {event_date}. {details}. "
            "Check issuer IR, options-implied magnitude (not direction), historical reactions, "
            "expectations, potential gross EUR3500 and worst plausible overnight gap. "
            "Geen koopbevestiging; no buy-ready signal, no automated orders, no assumed probabilities.")
