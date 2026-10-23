"""Offline property-based checks for the frozen ATR risk scoring primitives.

Run manually in an isolated research environment:
  python -m pip install 'hypothesis>=6,<7'
  python -m pytest -q research/test_atr_hypothesis_research.py

No live workflow integration or data download.
"""
import math
import pytest
from hypothesis import given, settings, strategies as st
from research_atr_incremental_holdout_scoring import fit, forecast, predict, evaluate

FLAGS = ("structure_above_20d_mean", "market_20d_positive", "atr_expanding")

@st.composite
def event(draw):
    row = {name: draw(st.booleans()) for name in FLAGS}
    row["severe"] = draw(st.booleans())
    return row

@settings(max_examples=75, deadline=None)
@given(st.lists(event(), min_size=1, max_size=30), st.lists(event(), max_size=20))
def test_probabilities_and_determinism(training, test_rows):
    model = fit(training)
    features = [{name: row[name] for name in FLAGS} for row in test_rows]
    a = forecast(model, features)
    assert a == forecast(model, features)
    assert all(0 < pred[key] < 1 for pred in a
               for key in ("baseline_probability", "atr_probability"))
    assert all(pred["trade_ready"] is False for pred in a)

@settings(max_examples=75, deadline=None)
@given(st.lists(event(), min_size=1, max_size=30), st.lists(event(), min_size=1, max_size=20))
def test_future_labels_cannot_change_forecast(training, test_rows):
    model = fit(training)
    opposite = [{**row, "severe": not row["severe"]} for row in test_rows]
    # forecast does not read outcome labels, even if accidentally supplied.
    assert forecast(model, test_rows) == forecast(model, opposite)
    scored = evaluate(predict(model, test_rows))
    assert math.isfinite(scored["baseline_brier"])
    assert math.isfinite(scored["atr_brier"])
    assert scored["trade_ready"] is False
    assert scored["independent_holdout_verified"] is False

@settings(max_examples=50, deadline=None)
@given(event(), st.sampled_from(FLAGS), st.one_of(st.none(), st.integers(), st.text()))
def test_invalid_flags_rejected(row, name, invalid):
    row[name] = invalid
    with pytest.raises(ValueError):
        fit([row])
