"""Offline end-to-end historical portfolio experiment.

The caller supplies chronological bars and independently computed
point-in-time signals. Same-currency close marks are constructed using
fixed-tranche price ratios less an assumed half-roundtrip entry cost.
FX, dividends and exact share sizing are NOT modeled.
"""
from decimal import Decimal
from research_swing_chronological_ledger import _money
from research_swing_data_preflight import validate_research_bars
from research_swing_dataset_manifest import validate_research_dataset_manifest
from research_swing_session_fill_adapter import proposals_from_bars
from research_swing_portfolio_with_marks import backtest_portfolio_with_marks


def backtest_bars_and_signals(series_by_ticker, signals, trading_dates, *,
                              horizon=10, initial_capital=21000,
                              tranche=3500, max_positions=6,
                              roundtrip_cost_bps=50, dataset_manifest=None):
    manifest_audit = None
    if dataset_manifest is not None:
        manifest_audit = validate_research_dataset_manifest(dataset_manifest)
        if not manifest_audit['research_comparison_eligible']:
            raise ValueError('dataset_not_comparison_eligible')
    validate_research_bars(series_by_ticker, trading_dates,
                           minimum_sessions=horizon + 2)
    proposals = proposals_from_bars(
        series_by_ticker, signals, horizon=horizon,
        roundtrip_cost_bps=roundtrip_cost_bps)
    ticket = _money(tranche)
    # Split the existing fixed roundtrip return haircut equally between
    # entry and exit for interim valuations; preserve terminal net cash.
    entry_cost = ticket * _money(roundtrip_cost_bps) / 20000
    marks = {}
    for proposal in proposals:
        ticker = proposal["ticker"]
        bars = series_by_ticker[ticker]
        entry_day = proposal["entry_date"]
        exit_day = proposal["exit_date"]
        entry_bar = next(bar for bar in bars if bar["date"] == entry_day)
        entry_open = _money(entry_bar["open"])
        for bar in bars:
            day = bar["date"]
            if entry_day <= day < exit_day and day in trading_dates:
                close = _money(bar["close"])
                if close <= 0:
                    raise ValueError("invalid_close_price")
                key = (day, ticker)
                # Clamp at zero: limited-liability long equity cannot have
                # negative liquidation value, even under extreme drawdowns.
                value = max(Decimal(0), ticket * close / entry_open - entry_cost)
                if key in marks and marks[key] != value:
                    raise ValueError("conflicting_marks")
                marks[key] = value
    result = backtest_portfolio_with_marks(
        proposals, marks, trading_dates, initial_capital=initial_capital,
        tranche=tranche, max_positions=max_positions)
    # A manifest is a self-declaration, never independent provenance proof.
    # Keep synthetic and exploratory results visibly separate from validated edge.
    result["research_evidence"] = {
        "level": "manifest_declared_exploratory" if manifest_audit is not None else "technical_unverified",
        "historical_comparison_claim_allowed": False,
        "independently_validated": False,
        "reason": "independent_source_and_out_of_sample_validation_missing",
    }
    result["execution_assumptions"] = {
        "entry": "next_session_open",
        "exit": "open_after_holding_sessions",
        "cost": "fixed_roundtrip_bps_return_haircut",
        "marks": "close_ratio_less_half_roundtrip_entry_cost_no_fx_or_dividends",
        "mark_to_market_costs_included": True,
        "drawdown_cost_adjusted": True,
        "drawdown_warning": "estimated_half_roundtrip_entry_cost_only_no_intraday_fx_or_dividends",
        "daily_marks_floor": "zero_long_equity_value",
        "historical_data_provenance_verified": False,
        "dataset_manifest_checked": manifest_audit is not None,
    }
    return result
