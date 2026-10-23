"""Join causal daily features to matured future labels by decision date.

Research-only bridge. Never treats the joined records as point-in-time verified.
A future outcome is used ONLY as a supervised evaluation label.
"""
from research_daily_atr_feature_extractor import extract_daily_structure
from research_forward_drawdown_labels import label_forward_drawdown


def join_features_and_labels(payload, *, horizon=10, threshold=0.08,
                             mean_window=20, atr_window=14):
    features = extract_daily_structure(payload, mean_window=mean_window,
                                       atr_window=atr_window)
    labels = label_forward_drawdown(payload, horizon=horizon, threshold=threshold)
    label_by_date = {row["date"]: row for row in labels}
    joined = []
    for feature in features:
        label = label_by_date.get(feature["date"])
        if label is None:
            continue  # right-censored: not enough future trading days
        joined.append({
            **feature,
            "severe": label["severe"],
            "label_available_date": label["label_available_date"],
            "horizon_trading_days": label["horizon_trading_days"],
            "threshold_fraction": label["threshold_fraction"],
            "point_in_time_verified": False,
            "trade_ready": False,
        })
    return joined
