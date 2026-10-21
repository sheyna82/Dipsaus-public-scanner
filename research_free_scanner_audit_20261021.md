# Gratis scanneronderzoek — onderzoeksnotities (21 oktober 2026)

Status: **documentatieonderzoek**, geen bewijs van handelsvoordeel. Geen betaalde tools, API's of databronnen toegestaan. Geen live wijzigingen.

## 1. Freqtrade (gratis open source; primair crypto)

Officiële documentatie:
- https://www.freqtrade.io/en/stable/lookahead-analysis/
- https://docs.freqtrade.io/en/latest/backtesting/
- https://www.freqtrade.io/en/stable/strategy-101/

**Relevante technieken**
- `lookahead-analysis` vergelijkt basisbacktests met gewijzigde indicatorberekeningen om ongeoorloofd gebruik van toekomstige koersdata op te sporen.
- Backtests expliciteren orderuitvoeringsaannames: limietprijzen binnen de candle worden in de simulatie als gevuld beschouwd; stoploss kan tegen een theoretische prijs gevuld worden; werkelijkheid kent gaps, slippage en niet-uitgevoerde orders.
- Dry-run/forward testing is essentieel naast historische tests.

**DIPSAUS-conclusie**: de offline follow-through module gebruikt alleen latere koersen voor evaluatie; dat is goed, maar we hebben nog geen end-to-end audit dat signalen, marktomstandigheden, sectorlabels en historische selecties *op het signaalmoment* beschikbaar waren. Een CI-test op een synthetische dataset bewijst dit niet. Voeg daarom geen prestatieclaims toe.

**Wat we kunnen overnemen zonder code te kopiëren**: as-of tijdstempels, audit op toekomstige informatie, conservatieve uitvoeringsscenario's, en aparte forward-paper-validatie. Freqtrade is geen directe aandelen-databron voor EU/VS.

## 2. Microsoft Qlib (gratis open source)

Officiële bron:
- https://github.com/microsoft/qlib
- https://github.com/microsoft/qlib/blob/main/docs/index.rst
- https://github.com/microsoft/qlib/blob/main/qlib/backtest/backtest.py

**Relevante technieken**
- Gescheiden datalaag, strategie, uitvoeringssimulatie en evaluatierapportage.
- Expliciete experimentregistratie en point-in-time dataondersteuning in de documentatie.
- Portefeuille-evaluatie in plaats van uitsluitend één koerssignaal.

**DIPSAUS-conclusie**: onze afzonderlijke onderzoeksmodules lijken qua scheiding van verantwoordelijkheden op dit patroon, maar zijn niet verbonden met een geverifieerde historische dataset. Qlib is geen bewijs dat gratis, betrouwbare Europese en Amerikaanse historische datasets beschikbaar zijn.

## 3. Kritische openstaande punten vóór integratie

1. **As-of controle**: bewijs per historische waarneming dat earningsdatum, sector, marktfase, ATR en signaal toen al bekend waren.
2. **Matching**: huidige `dipsaus_offline_risk_matching.py` matcht sector, marktregime en ATR, maar **niet dezelfde kalenderperiode**. Dat kan historische vergelijking ernstig vertekenen. De greedy-matching is bovendien volgordegevoelig.
3. **Kosten en fills**: simuleer conservatieve scenario's voor limietorders en overnight gaps; niet doen alsof een geraakt niveau een gegarandeerde fill betekent.
4. **Selectiebias**: neem alle genomineerde signalen, ontbrekende gegevens en delistings mee.
5. **Forward paper audit**: leg signalen vast vóór de uitkomst; evalueer pas daarna. Geen orders.
6. **Datarechten**: gratis bekijken is niet hetzelfde als gratis automatisch ophalen en herpubliceren. Verifieer voorwaarden per bron.

## Prioriteit

**Eerst** punt 1 en 2 repareren/testen. **Daarna** gecontroleerde gratis dataprovenance en historische evaluatie. Pas na die stappen eventuele koppeling aan live waarschuwingen overwegen. De methoden van betaalde earnings-platforms zijn uitsluitend onderzoeksreferenties; geen scraping of betaalde afhankelijkheden.
