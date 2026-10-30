"""Predeclared training-only feature thresholds; research-only, no trading output."""
import statistics

FEATURE_DIRECTIONS={"relative_strength_20d_pct":"HIGH",
                    "volume_ratio_20d":"HIGH",
                    "atr_14_pct":"LOW"}

def training_median_thresholds(observations):
    """Observations are (date_index, feature_dict); no outcome fitting.

    Thresholds are medians of the training population, not optimized for returns.
    Caller must enforce chronological split and supply training rows only.
    """
    if len(observations)<30:
        return {"status":"INSUFFICIENT_TRAINING_OBSERVATIONS","trade_ready":False}
    thresholds={}
    for key in FEATURE_DIRECTIONS:
        values=[row[key] for _,row in observations if row.get("status")=="DESCRIPTIVE_ONLY"
                and isinstance(row.get(key),(int,float))]
        if len(values)<30:
            return {"status":"INSUFFICIENT_VALID_FEATURES","trade_ready":False}
        thresholds[key]=statistics.median(values)
    return {"status":"TRAINING_ONLY_THRESHOLDS","trade_ready":False,
            "thresholds":thresholds,"training_observations":len(observations)}

def label(features, thresholds):
    if features.get("status")!="DESCRIPTIVE_ONLY" or thresholds.get("status")!="TRAINING_ONLY_THRESHOLDS":
        return {"status":"BLOCKED","trade_ready":False}
    t=thresholds["thresholds"]
    return {"status":"RESEARCH_ONLY","trade_ready":False,
            "passes":{key:(features[key]>=t[key] if direction=="HIGH"
                           else features[key]<=t[key])
                      for key,direction in FEATURE_DIRECTIONS.items()}}
