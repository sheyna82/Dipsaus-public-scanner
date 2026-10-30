"""International equity research universe; symbols are candidates, not validated event data.

Exchange suffixes follow Yahoo Finance documentation. No claim of DEGIRO availability.
An earnings event must be independently sourced and time-verified before trading research.
"""
import csv
from pathlib import Path

MARKETS={
 "NL":("AS",["ASML","ADYEN","INGA","PHIA","HEIA","WKL","ASM","AKZA","ABN","RAND"]),
 "FR":("PA",["MC","OR","SAN","AIR","BNP","SU","CAP","DG","KER","BN"]),
 "DE":("DE",["SAP","SIE","ALV","BAS","BMW","MBG","DTE","IFX","RWE","DBK"]),
 "UK":("L",["SHEL","AZN","HSBA","ULVR","BP","RIO","GSK","BARC","LLOY","REL"]),
 "IT":("MI",["ENI","ENEL","ISP","UCG","STLAM","LDO","PRY","RACE"]),
 "ES":("MC",["SAN","BBVA","IBE","ITX","TEF","REP","ACS"]),
 "CH":("SW",["NESN","NOVN","ROG","UBSG","ABBN","ZURN"]),
 "SE":("ST",["VOLV-B","ATCO-A","ERIC-B","SEB-A","SAND","SKF-B"]),
 "DK":("CO",["NOVO-B","VWS","DSV","MAERSK-B"]),
 "NO":("OL",["EQNR","DNB","NHY","YAR"]),
 "FI":("HE",["NOKIA","KNEBV","SAMPO","FORTUM"]),
 "BE":("BR",["ABI","KBC","UCB"]),
 "PT":("LS",["EDP","GALP","JMT"]),
 "JP":("T",["7203","6758","9984","8306","6861","8035","6501","9432"]),
 "HK":("HK",["0700","9988","1299","0941","0388"]),
 "CA":("TO",["RY","TD","SHOP","ENB","CNQ"]),
 "AU":("AX",["BHP","CBA","CSL","WBC","NAB"]),
 "IN":("NS",["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK"]),
 "KR":("KS",["005930","000660","005380"]),
 "TW":("TW",["2330","2317","2454"]),
 "SG":("SI",["D05","O39","U11"]),
 "BR":("SA",["PETR4","VALE3","ITUB4"]),
 "ZA":("JO",["NPN","AGL","SOL"]),
}
def candidates():
    return [{"market":market,"symbol":f"{ticker}.{suffix}","status":"candidate_unverified","event_timestamp_verified":False,"degiro_tradability_verified":False} for market,(suffix,tickers) in MARKETS.items() for ticker in tickers]
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="research-international-universe.csv")
    args=p.parse_args();rows=candidates()
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(f"international_candidates={len(rows)} markets={len(MARKETS)} event_verified=0")
if __name__=="__main__":main()
