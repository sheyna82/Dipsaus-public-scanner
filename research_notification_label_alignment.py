"""Compare emitted alert labels with independent historical price-stage hypotheses.

An apparent mismatch is a review flag, not evidence the alert was wrong:
labels can describe different strategy concepts and the screenshot timestamp
does not establish the original intraday features.
"""
def label_alignment(cases, stages):
    lookup={row["symbol"]:row for row in stages}
    output=[]
    for case in cases:
        stage=lookup.get(case.symbol,{}).get("stage","UNCLASSIFIED")
        flag=(case.family=="EARLY_RECOVERY" and stage=="MOMENTUM_NEAR_HIGH")
        output.append({"symbol":case.symbol,"emitted_family":case.family,
                       "independent_daily_stage":stage,
                       "review_early_recovery_label":flag,
                       "alert_error_proven":False,
                       "research_only":True})
    return output
