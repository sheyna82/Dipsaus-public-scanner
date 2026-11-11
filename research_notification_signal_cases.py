"""Research-only, deterministic classification of DIPSAUS phone notification cases.

No quote fetching, broker orders, notification sending or production state writes.
These are observations, not proof of profitable trades.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SignalCase:
    symbol: str
    family: str
    observed_local_time: str
    evidence: str
    entry_confirmed: bool = False
    price_at_signal: Optional[float] = None

    def as_dict(self):
        return vars(self).copy()

CASES_2026_10_26 = (
    SignalCase("EXE", "EXIT_ZONE_REVIEW", "13:51", "KOERSZONECHECK - GEEN WINSTBEVESTIGING"),
    SignalCase("VIST", "EARLY_RECOVERY", "13:51", "VROEGE HERSTELKANS"),
    SignalCase("FANG", "EARLY_RECOVERY", "13:46", "VROEGE HERSTELKANS"),
    SignalCase("LNG", "BREAKOUT_HOLD_RETEST", "13:46", "BREAKOUT-HOLD-RETEST"),
    SignalCase("VIE.PA", "EU_ENTRY_RESEARCH", "12:42", "INSTAPCHECK score 4"),
    SignalCase("MC.PA", "EU_ENTRY_RESEARCH", "12:41", "INSTAPCHECK score 4"),
    SignalCase("MBG.DE", "EU_ENTRY_RESEARCH", "12:41", "INSTAPCHECK score 4"),
    SignalCase("FER.MC", "EU_ENTRY_RESEARCH", "12:41", "INSTAPCHECK score 4"),
)

def audit_cases(cases=CASES_2026_10_26):
    """Fail closed: screenshot times lack timezone and prices; no performance claim."""
    return {
        "count": len(cases),
        "families": sorted({case.family for case in cases}),
        "symbols": [case.symbol for case in cases],
        "ready_for_net_return_study": all(
            case.price_at_signal is not None and case.entry_confirmed
            for case in cases
        ),
        "missing": ["UTC event timestamp", "source quote at signal",
                    "next executable bid/ask", "subsequent daily OHLCV",
                    "transaction costs and benchmark"],
        "research_only": True,
    }
