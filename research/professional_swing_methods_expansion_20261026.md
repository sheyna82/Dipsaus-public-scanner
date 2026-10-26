# DIPSAUS — professionele swingtrading: uitbreiding onderzoeksplan
Datum: 2026-10-26
Status: onderzoeksagenda, niet actief in productie. Geen claims over voorspellende winst.

## Onderzochte primaire bronnen
- Charles Schwab, swing trading strategies: https://www.schwab.com/learn/story/swing-trading-strategies
- Charles Schwab, five elements of a trade plan: https://www.schwab.com/learn/story/5-elements-smart-trade-plan
- Fidelity, swing trading: https://www.fidelity.com/learning-center/trading-investing/trading/swing-trading
- Fidelity, ATR: https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr
- IBD SwingTrader position sizing: https://www.investors.com/research/swing-trading/risk-management-position-sizing-swingtrader/
- Fidelity, managing positions: https://www.fidelity.com/learning-center/trading-investing/trading/managing-positions

## Toevoegen als vooraf te registreren onderzoekshypothesen
1. Exit-horizons: 3, 5, 10, 15, 20, 30, 40 handelsdagen; plus een dynamische, causale exit zonder vaste verkoopdag. Langer dan 40 dagen als afzonderlijke position-trade-controle, niet automatisch een swing.
2. Marktregime: stijgende/dalende/zijwaartse index en volatiliteitsregime; informatie alleen beschikbaar vóór instap.
3. Relatieve sterkte tegenover index en sector; vergelijk met eenvoudige baseline.
4. Multi-timeframe trend: wekelijkse richting, dagelijkse entry, optioneel intraday alleen bij betrouwbare data.
5. ATR-normalisatie: dynamische koersafstand en risicowaarschuwing; geen verplichte broker-stoporders.
6. Geschaalde entries en bijkopen na bevestigde sterkte; vergelijken met vaste tranche, zelfde totaal kapitaal en risicobudget.
7. Partial take-profit plus resterende runner versus alles-in-een-keer exit; extra commissie en spread meenemen.
8. Opportunity cost: vergelijken tussen aanhouden en kapitaal heralloceren; maximaal zes gelijktijdige posities.
9. Event-aware signalen: earnings, dividend, economische kalender, gap-risico en herkomst/tijdstempel.
10. Trade journal: ex ante hypothese, uitvoering, latere uitkomst, afwijking, kosten en benchmark.

## Evaluatieregels
- Netto gerealiseerde portefeuille-P&L na commissie, spread, slippage, liquiditeit en valutakosten waar relevant.
- Vergelijk identieke datums en universe, zelfde inzet en max zes posities; geen dubbelgebruik van kapitaal.
- Purged walk-forward, holdout, geen lookahead, overfit- en survivorship-controles, voldoende onafhankelijke trades.
- Niet de beste horizon achteraf selecteren op de testset; vooraf trainselectie, daarna onaangeroerde holdout.
- Rapportage van totale netto winst, expectancy, profit factor, drawdown, tijd in markt, turnover, kapitaalbenutting en opportunity cost.
- Persoonlijke voorkeur: geen verplichte stoploss/stoplimit; wel expliciete risicowaarschuwingen en mogelijke verkooplimieten. Risico van grote verliezen en overnight gaps niet verdoezelen.
- Geen nieuwe packages, externe broncode, brokerconnecties of orders zonder apart besluit.
- Geen wijzigingen aan main, productiealerts of frozen momentumprotocol.

## Prioriteitsvolgorde
A. Causale dynamische exits en horizonvergelijking op echte historische OHLC.
B. Marktregime + relatieve sterkte en ATR als verklarende variabelen.
C. Kapitaalrotatie, partial exits en bijkopen met gelijke risicobudgetten.
D. Eventkalender en journal, daarna out-of-sample toetsing.
