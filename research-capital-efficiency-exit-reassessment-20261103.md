# DIPSAUS — heranalyse kapitaalefficiëntie vaste versus dynamische exits (2026-11-03)

## Bron en afbakening
Herberekening van reeds bestaande resultaten in `research/first_real_dynamic_exit_comparison_20261026.md` op de **afzonderlijke** historische onderzoeksbranch `research/offline-technical-risk-20261021`. Oorspronkelijke bron noemt 96 hypothetische instapmomenten (AMD, COHU, META, SPY), USD 3.500 per trade, 10 basispunten kosten per zijde, historische Yahoo 5y OHLC niet onafhankelijk geverifieerd. De hier gebruikte totalen zijn overgenomen uit dat verslag, **niet** opnieuw uit koersdata berekend. Dit is geen nieuwe onafhankelijke validatie.

## Extra normalisatie
Per exit: `totale netto P&L / (96 × 3500 × gemiddelde houdduur in handelsdagen) × 1000`. Eenheid: **USD winst/verlies per USD 1.000 hypothetisch bezet kapitaal per handelsdag**. Bij vaste exits is de duur het gerapporteerde aantal dagen; bij trailing 8% is de gerapporteerde gemiddelde duur 24,09 dagen (afrondingsonzekerheid). Dit is een descriptieve kapitaal-tijd-ratio, **geen** annualized return, IRR, haalbaar portefeuillerendement, rangschikkingsscore of risicogecorrigeerd rendement.

| Exit | Som netto P&L (USD) | Houdduur (sessies) | USD per 1000 kapitaal-sessie |
|---|---:|---:|---:|
| 3 dagen | -1731.79 | 3 | -1.7180 |
| 5 dagen | -1501.16 | 5 | -0.8935 |
| 10 dagen | 8073.87 | 10 | 2.4029 |
| 15 dagen | 9410.14 | 15 | 1.8671 |
| 20 dagen | 15122.83 | 20 | 2.2504 |
| 30 dagen | 18005.32 | 30 | 1.7862 |
| 40 dagen | 22491.98 | 40 | 1.6735 |
| Trailing 8% | 8206.46 | 24.09 gemiddeld | 1.0139 |

## Wat dit wel en niet betekent
- De **40-daagse** exit heeft de grootste totale hypothetische netto P&L, maar **10 dagen** heeft in deze specifieke tabel de hoogste kapitaal-tijd-ratio. Dat is een verandering van rangorde door een andere meetlat, **geen** bewijs dat 10 dagen de beste strategie is.
- De 15-daagse exit scoort lager dan 10 dagen op deze ratio; de 20-daagse exit scoort hoger dan 15 dagen. Het patroon is niet monotone; een simpele regel 'korter is beter' wordt niet ondersteund.
- Alle 96 trades zijn los geteld; de ratio veronderstelt geen daadwerkelijk uitvoerbare zespositieportefeuille, en houdt geen rekening met overlap, niet-gekozen kansen, herbelegging, drawdowns, FX, brokerfills, sectorconcentratie of een onafhankelijk gekozen benchmark.
- Een langere exit kan mechanisch profiteren van algemene marktstijging; SPY zit in de instrumentset. De steekproef en exitvarianten zijn eerder onderzocht: **multiple testing / selectie achteraf** blijft een risico.
- Een hoog gemiddeld bedrag per bezette kapitaaldag zegt niets over verdeling, maximale kapitaalblokkade, tail risk, het vermogen om een nieuwe kans te financieren, of de reproduceerbaarheid buiten de steekproef.

## Professionele vervolgstap (nog niet uitgevoerd)
Herbruik de bestaande `research/candidate_portfolio_capacity.py` en `research/candidate_capacity_opportunity_audit.py` op de historische branch; voer **vooraf vastgelegde** 5/10/15-daagse en benchmarkscenario's door één chronologische zespositie-kapitaalboekhouding. Bereken netto P&L, occupied **exchange sessions**, niet-gekozen kansen, piekbezetting, sectorblootstelling, drawdown met onafhankelijke dagelijkse marks, en kwartaal/OOS stabiliteit. Houd 20/30/40-daagse varianten uitsluitend als expliciet gescheiden exploratie of benchmark. Gebruik uitsluitend as-of toegankelijke selectiefeatures; toekomstige uitkomsten mogen niet in de rangschikking terechtkomen. Pas operationele exitregels pas aan na onafhankelijke bevestiging.

**Status: descriptief, research-only, geen handelssignaal, geen automatische orders, geen wijzigingen aan main of live scanner.**
