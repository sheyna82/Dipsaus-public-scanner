# DIPSAUS — professioneel swingtradingonderzoek, ronde 4
Datum 2026-10-26. Research-only. Geen wijziging productie, orders, frozen protocol of main.

## Bronnen en verifieerbare methoden
- Schwab swing trading: https://www.schwab.com/learn/story/swing-trading-strategies
- Schwab trade plan: https://www.schwab.com/learn/story/5-elements-smart-trade-plan
- QuantConnect walk-forward: https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/walk-forward-optimization
- QuantConnect research guide: https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/research-guide
- QuantConnect slippage: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/key-concepts
- QuantConnect reconciliation: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation

## Prioriteiten
1. Marktregime × setup: trend pullback, breakout en mean-reversion afzonderlijk toetsen; regime op basis van vooraf bekende gegevens.
2. Dynamische uitstap vs vaste 3/5/10/15/20/30/40 handelsdagen. Trailing thesis invalidation zonder verplichte stoporders, winstneming en opportunity cost.
3. Portfolio capital allocation: netto winst per ingezet kapitaal en per dag, maximaal zes gelijktijdige posities, correlation/sector budget, cash drag, turnover, position sizing.
4. Causale walk-forward: training op verleden, embargo/purge voor overlappende trades, onafhankelijke holdout, voorkomen van survivorship- en lookahead-bias.
5. Realistische uitvoering: next-session-open signal-to-fill, limietorder kan ongevuld blijven, commissies, spread, slippage, EUR/USD en gapstress.
6. Paper trading en trade journal: signaal en rationale vooraf vastleggen, vervolgens vergelijking met werkelijke uitvoering.

## Verplichte falsificatie
- Alle modellen vergelijken met simpele baseline op exact hetzelfde universum, dezelfde perioden en dezelfde totale kapitaalruimte.
- Geen selectie van de best presterende horizon achteraf op de holdout.
- Rapportage van netto gerealiseerde winst, drawdown, turnover, tijd in markt, confidence intervals en onzekerheid bij kleine samples.
- De huidige Yahoo proef heeft kleine geselecteerde symbolenset en onbevestigde licentie/corporate-action behandeling; dus geen productie- of winstclaims.

## Eerstvolgende bouwbare proef
Ontwikkel één offline benchmark die dezelfde historisch vastgelegde signalen parallel afwikkelt onder vaste exits en dynamische exits, met portfolio cash ledger, next-open fills, en causale train/test-splits. Stop met extra signalen toevoegen totdat deze basisvergelijking aantoonbaar werkt.
