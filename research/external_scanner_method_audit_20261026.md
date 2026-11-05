# DIPSAUS — externe scannercomponenten: eerste broncode-audit
Datum: 2026-10-26
Status: research-only; geen installatie, import, live alerts of orderuitvoering.

## Gecontroleerde primaire bestanden
- Optedge: https://github.com/kaiuribess/Optedge (README, LICENSE, docs/VALIDATION.md, risk/research_guard.py)
- QuantConnect LEAN: https://github.com/QuantConnect/Lean (README, LICENSE)

## Vastgestelde licenties
- Optedge: MIT. Bij overnemen van substantiële code copyright- en licentietekst behouden.
- LEAN: Apache-2.0. Bij overnemen licentie en relevante NOTICE-/wijzigingsverplichtingen controleren.
- Geen code overgenomen; licenties van overige tools nog afzonderlijk te verifiëren.

## Bruikbare methoden uit Optedge
1. Uitvoerbare swings scheiden van shadow/Watch/Skip, ongeldige of nul-omvang signalen.
2. Vaste uitkomsthorizons 1, 3, 5, 10 en 20 voltooide handelsdagen; deduplicatie per ticker/richting/instapdag.
3. Netto resultaat na spread/slippage, winstfactor, maximale drawdown, SPY/QQQ en willekeurige baseline.
4. Factorinformatiewaarde uitsluitend berekenen op geldige, niet-gedupliceerde, uitvoerbare signalen.
5. Bron- en modelversies aan elke voorspelling en uitkomst koppelen.
6. Onvoldoende steekproef, verouderde data en risicoverslechtering expliciet tonen.

### Belangrijke beperkingen
- Optedge's 50%-winratewaarschuwing is geen universeel break-evencriterium: dat hangt af van gemiddelde winst/verlies en kosten.
- De 500 gesloten trades, 100 horizons/10 dagen en -20% drawdown zijn projectregels, geen bewezen optimale DIPSAUS-grenzen.
- Optedge bevat opties, futures en brokerfuncties die DIPSAUS niet nodig heeft. Geen brokerintegratie of automatische orders overnemen.
- Stop-gebaseerde exits niet omzetten in automatische stoplossorders; alleen als onderzoeks-/waarschuwingssignaal.

## LEAN: nuttige ontwerpprincipes
- Realistische orderfills, transactiekosten, portfolio accounting en event-driven simulatie.
- Scheiding research/backtest/live; voor DIPSAUS alleen research-ideeën evalueren.
- Volledige engine integreren is voorlopig onnodig zwaar; bouw eerst kleine deterministische simulaties.

## Prioriteit voor de DIPSAUS-winstdoelstelling
A. Vaste 3/5/10-dagen uitkomsten per technisch herstel- en eventmodel apart.
B. Netto portfolio-P&L na spread, commissie, slippage en realistische uitvoerbaarheid.
C. Vergelijk vaste exit, winstdoel, trailing winstbewaking en tijd-exit zonder automatische orders.
D. Kapitaalallocatie en maximaal zes gelijktijdige posities; meet opportunity cost.
E. Walk-forward, chronologische holdout, survivorship- en lookaheadcontroles.
F. Alleen combineren wanneer out-of-sample portefeuille-P&L en risicogecorrigeerd resultaat verbeteren.

## Volgende technische stap
Voeg een onafhankelijke offline researchmodule met synthetische tests toe voor netto trade-P&L en 3/5/10-daagse exits. Laat de bestaande prospectieve momentumprotocol-v1 onveranderd. Registreer nieuwe swinghypothesen apart voordat live resultaten worden bekeken.

Geen claims over voorspellende waarde of hogere winst zonder onafhankelijke uitkomstdata.
