# DIPSAUS — externe scannercomponenten: onderzoeksregister

Status: verkenning op 23 oktober 2026. **Geen broncode overgenomen.** Dit register onderscheidt vindbaarheid van daadwerkelijke code-audit. Repositories zijn zoekresultaten; functionaliteit, onderhoud, licentie en prestaties moeten per bron nog afzonderlijk worden geverifieerd.

| Externe bron | Onderzoekbare bouwsteen | Potentieel nut DIPSAUS | Verificatie |
|---|---|---|---|
| [mementum/backtrader](https://github.com/mementum/backtrader) | Event-driven backtesting, order-/kostenmodellering | Realistischer historische simulaties en frictie | Code, licentie, aannames en testkwaliteit nog inspecteren |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | Strategiebacktests en evaluatie | Tweede, onafhankelijke testimplementatie als controlegroep | Nog inspecteren |
| [lit26/Stock_Screener](https://github.com/lit26/Stock_Screener) | Screening-architectuur | Kandidatenselectie en indicatorfilters | Nog inspecteren |
| [AdamGetbags/breakoutScanner](https://github.com/AdamGetbags/breakoutScanner) | Breakout-signalen | Vergelijking vroege uitbraak versus herstel | Nog inspecteren |
| [cbyhre/Stock-News-Scanner](https://github.com/cbyhre/Stock-News-Scanner) | Nieuwssignalen | Context zonder onnodige meldingen | Nog inspecteren |
| [bilalaslam28/Automated-VSA-Pre-Market-Stock-Scanner](https://github.com/bilalaslam28/Automated-VSA-Pre-Market-Stock-Scanner) | Premarket en volume/spread-analyse | Vroegtijdige waarschuwingen en volumebevestiging | Nog inspecteren |

## Vergelijkingsrubriek per bouwsteen

1. Wat doet de implementatie daadwerkelijk? Lees code en tests, niet alleen README of claims.
2. Is het signaal causaal? Data release-tijd, look-ahead, survivorship en herzieningen.
3. Wat is de gemeten meerwaarde tegenover eenvoudige basisregels op onafhankelijk holdoutmateriaal?
4. Hoe gaat het om met foutpositieven, vertraging, transactiekosten en verschillende markten?
5. Kan het onderdeel los worden hergebruikt, of alleen als concept worden herbouwd? Controleer licentie en afhankelijkheden.
6. Past het bij DIPSAUS: herstel-swing over dagen/weken, weinig ruis, risico-informatie en limietorders zonder verplichte stoploss?
7. Kan de verbetering geïsoleerd op de onderzoeksbranch worden getest zonder live alerts of privégegevens?

## Prioriteiten

**P1:** onafhankelijke walk-forward-evaluatie, frictie, dataprovenance en leakage-audit.  
**P2:** herstel versus breakout; volume- en volatiliteitsbevestiging; regimefilters.  
**P3:** event/nieuwscontext, premarket-waarschuwingen en adaptieve alertdrempels.

## Beslisregel

Niet overnemen op basis van populariteit, marketing of een aantrekkelijke backtest. Eerst component isoleren, baseline formuleren, falsificatietest bouwen, daarna alleen bij aantoonbare meerwaarde integreren. Geen automatische handel; geen wijzigingen aan de productiebranch zonder expliciete toestemming.

## Eerste broninspectie: backtest-uitvoering (23 oktober 2026)

**Backtrader**: README beschrijft configureerbare commissies, slippage, volume filling, limit-orders, meerdere tijdframes en een expliciete *cheat-on-close/open*-optie. Voor DIPSAUS zijn vooral realistische fill-aannames en het vermijden van uitvoering tegen een nog onbekende slotkoers relevant. Project meldt GPL-3.0; code niet kopiëren zonder licentiebeoordeling. Bron: https://github.com/mementum/backtrader

**Backtesting.py**: publieke API en implementatie beschrijven spread, vaste/procentuele commissies, standaarduitvoering van marktorders op de volgende candle-open, optionele trade_on_close en limietorders. Bij DIPSAUS moeten de hypothetische limietverkopen en gemiste fills expliciet worden meegenomen, ook als de scanner zelf geen orders plaatst. Project meldt AGPL-3.0; code niet kopiëren zonder licentiebeoordeling. Bronnen: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html en https://github.com/kernc/backtesting.py/blob/master/backtesting/backtesting.py

**Besluit voor een geïsoleerde DIPSAUS-proef:** bouw eerst een eigen, kleine execution-assumption-audit die scenario's vergelijkt (volgende opening versus slotkoers, spread, kosten, niet-uitgevoerde limietorders) op synthetische OHLCV. Dit is **niet** hetzelfde als een gevalideerde strategiebacktest en bewijst geen voorspellende waarde. Geen externe code of afhankelijkheid importeren.

**Open punten:** testdekking van de twee upstream-projecten, actuele onderhoudsstatus, exacte order-fill-semantiek bij gaps en gedeeltelijke uitvoering, licentieadvies en realistische brokerdata. De vier overige projecten zijn nog niet inhoudelijk geaudit.
