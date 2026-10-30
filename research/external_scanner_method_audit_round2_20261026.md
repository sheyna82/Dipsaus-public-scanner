# DIPSAUS — externe tradingsoftware, tweede vergelijkingsronde
Datum: 2026-10-26. Status: documentatie-audit, research-only. Geen externe packages geïnstalleerd of code overgenomen.

## Primaire bronnen en componenten

### Backtrader
- https://github.com/mementum/backtrader
- https://github.com/mementum/backtrader/blob/master/setup.py
- Licentie: GPLv3+ volgens setup.py. Geen broncode kopiëren naar DIPSAUS zonder licentiebeoordeling.
- Bruikbaar als methodisch voorbeeld: brokerfill-simulatie, limitorders, commissies, slippage, volumefills, meerdere tijdreeksen en kalenders.
- Risico: cheat-on-open/cheat-on-close simulatiemodi zijn ongeschikt als bewijs van uitvoerbare historische resultaten. Onderzoek expliciete tijdsvolgorde.

### vectorbt (community)
- https://github.com/polakowo/vectorbt
- https://github.com/polakowo/vectorbt/blob/master/LICENSE.md
- Licentie: Apache 2.0 WITH Commons Clause, niet behandelen als onbeperkte standaard Apache 2.0.
- Bruikbaar als inspiratie: vectorized multi-parameter vergelijking, strategievarianten, portefeuillekosten en drawdown-overzichten.
- Geen code overnemen voordat de Commons Clause en optionele dependencylicenties zijn beoordeeld. Geen PRO-functies veronderstellen.

### QuantStats
- https://github.com/ranaroussi/quantstats
- https://github.com/ranaroussi/quantstats/blob/main/pyproject.toml
- Licentie: Apache-2.0 volgens projectmetadata.
- Bruikbaar: profit factor, expectancy, drawdown, rolling return, downside risk, Monte Carlo gevoeligheid en benchmarkrapporten.
- Geen package installeren nodig voor eerste stap: verifieer onafhankelijke metriekberekeningen met synthetische tests en later met echte historische portefeuilleresultaten.

### Freqtrade
- https://www.freqtrade.io/en/2026.3/lookahead-analysis/
- https://www.freqtrade.io/en/stable/recursive-analysis/
- https://github.com/freqtrade/freqtrade/blob/develop/docs/hyperopt.md
- Bruikbaar als methodische inspiratie: lookahead-analysis (indicatoren/signalen bij verkorte data), recursive-analysis (warmupgevoeligheid), expliciete train/test scheiding bij parameteroptimalisatie en controle van kosten/exitregels.
- Primair gericht op crypto; geen trading-bot, exchange connector, hyperopt of automatische orders overnemen.
- Licentie van exact te hergebruiken code en dependencies nog afzonderlijk verifiëren; geen broncode gekopieerd.

## Wat DIPSAUS al heeft
- Onderzoekssimulaties voor next-session-open fills, 3/5/10 dagen, kosten, maximaal zes posities, score-ranglijsten, drawdown en walk-forward.
- Deze modules hebben nog GEEN bewezen out-of-sample edge; echte data-ingestie en gecontroleerde bronrechten ontbreken.

## Prioriteit op winst, niet indicatorenaantal
1. **Freqtrade-idee:** onafhankelijke prefix-consistency / no-lookahead tests op elke signaalberekening. Dit voorkomt vals aantrekkelijke winsten.
2. **Backtrader-idee:** onafhankelijke fill- en limietordercontrole; geen optimistische close-to-close uitvoerbaarheid.
3. **QuantStats-idee:** onafhankelijke risicorapportage (expectancy, profit factor, worst drawdown) uit NETTO gesloten trades.
4. **vectorbt-idee:** efficiënte vergelijking van kleine vooraf vastgelegde parameterroosters, uitsluitend op trainingsperioden, met holdout zonder bijstellen.
5. Daarna pas eventueel externe bibliotheken installeren als licentie, afhankelijkheden, veiligheid en empirische meerwaarde aantoonbaar zijn.

## Grenzen
Geen live orders, geen nieuwe externe dependencies, geen geheimen, geen wijzigingen aan main, productiealerts of het bevroren momentumprotocol. Vergelijk winst na kosten op identieke cohorten; niet achteraf de beste strategie op dezelfde testset kiezen.
