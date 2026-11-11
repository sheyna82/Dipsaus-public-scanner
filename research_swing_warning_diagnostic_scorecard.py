"""Research-only professional-style signal diagnostics; no trading decisions.

Evaluate false alarms, missed crashes and out-of-sample stability. All decisions
use information available at the close; labels are future outcomes only.
"""
from research_swing_warning_component_ablation import evaluate_warning_components, SIGNALS

def warning_diagnostic_scorecard(bars, *, horizons=(5,10,15), step=15):
    results={}
    for h in horizons:
        sample=evaluate_warning_components(bars,horizon=h,step=step)
        comparisons={}
        for name in SIGNALS:
            part=sample["components"][name]
            all_stats=part["all"]
            late=part["late"]
            total_events=all_stats["tp"]+all_stats["fn"]
            total_alerts=all_stats["tp"]+all_stats["fp"]
            comparisons[name]={
                "alerts":total_alerts,
                "caught_large_drawdowns":all_stats["tp"],
                "missed_large_drawdowns":all_stats["fn"],
                "false_alarms":all_stats["fp"],
                "false_alarm_fraction":round(all_stats["fp"]/total_alerts,4) if total_alerts else None,
                "missed_event_fraction":round(all_stats["fn"]/total_events,4) if total_events else None,
                "late_precision_lift":late["lift"],
                "late_true_positives":late["tp"],
                "late_false_positives":late["fp"],
                "late_evidence_sufficient":late["tp"]>=20 and late["fp"]>=20,
                "candidate_for_live_exit":False,
            }
        results[str(h)]={"observations":sample["observations"],
                         "purged_boundary_observations":sample["purged_boundary_observations"],
                         "signals":comparisons}
    return {"horizons":results,"research_only":True,"trade_ready":False,
            "portfolio_net_return_tested":False,"edge_proven":False}
