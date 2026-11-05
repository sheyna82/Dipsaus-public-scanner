"""Broad international DIPSAUS research candidates, NOT broker-confirmed instruments.

Every symbol needs an exact DEGIRO ISIN + exchange + currency check before
any live alert. Yahoo-style symbols are data-provider identifiers, not orders.
"""
from collections import Counter

COUNTRIES = {
 "US": ("AAPL","MSFT","NVDA","AMZN","META","GOOGL","JPM","BAC","XOM","CVX","CAT","RTX","UNH","JNJ","KO","PG","NEM","FCX","NEE","PLD"),
 "CA": ("RY.TO","TD.TO","ENB.TO","CNQ.TO","SHOP.TO","BAM.TO"),
 "NL": ("ASML.AS","ASM.AS","ADYEN.AS","INGA.AS","PHIA.AS","HEIA.AS","WKL.AS"),
 "DE": ("SAP.DE","SIE.DE","ALV.DE","BAS.DE","DTE.DE","RHM.DE","BMW.DE","IFX.DE"),
 "FR": ("MC.PA","OR.PA","TTE.PA","AIR.PA","SAN.PA","SU.PA","BNP.PA"),
 "GB": ("AZN.L","SHEL.L","HSBA.L","ULVR.L","RIO.L","RR.L"),
 "CH": ("NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ABBN.SW"),
 "SE": ("VOLV-B.ST","ATCO-A.ST","ERIC-B.ST","INVE-B.ST"),
 "DK": ("NOVO-B.CO","MAERSK-B.CO","DSV.CO"),
 "NO": ("EQNR.OL","DNB.OL","NHY.OL"),
 "FI": ("NOKIA.HE","KNEBV.HE","SAMPO.HE"),
 "IT": ("ENI.MI","ENEL.MI","ISP.MI","RACE.MI"),
 "ES": ("SAN.MC","IBE.MC","ITX.MC","FER.MC"),
 "BE": ("ABI.BR","UCB.BR","KBC.BR"),
 "PT": ("EDP.LS","GALP.LS","JMT.LS"),
 "AT": ("EBS.VI","OMV.VI"),
 "PL": ("PKN.WA","PZU.WA"),
 "IE": ("KRZ.IR","A5G.IR"),
 "JP": ("7203.T","6758.T","8306.T","8035.T","9984.T","6501.T"),
 "HK": ("0700.HK","1299.HK","0005.HK","0388.HK"),
 "AU": ("BHP.AX","CBA.AX","CSL.AX","WBC.AX","WES.AX"),
 "SG": ("D05.SI","O39.SI","U11.SI"),
}
BENCHMARKS = ("SPY", "IWM")
def international_candidate_manifest():
    rows = [{"country": country, "research_symbol": symbol,
             "degiro_verified": False, "isin": None, "exchange_mic": None,
             "trading_currency": None, "live_alert_eligible": False}
            for country, symbols in COUNTRIES.items() for symbol in symbols]
    symbols = [row["research_symbol"] for row in rows]
    if len(symbols) != len(set(symbols)):
        raise ValueError("duplicate_research_symbol")
    return {"research_only": True, "trade_ready": False,
            "countries": len(COUNTRIES), "candidate_count": len(rows),
            "broker_verified_count": 0, "benchmarks": list(BENCHMARKS),
            "country_counts": dict(Counter(row["country"] for row in rows)),
            "candidates": rows}
