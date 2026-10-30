# Eerste vaste versus dynamische exit — echte vijfjaarsreeksen (2026-10-26)

Bron: GitHub Actions run 40316862372, artifact 12647277768, Yahoo 5y raw OHLC voor AMD, COHU, META, SPY. Niet onafhankelijk gevalideerd.

Opzet: 96 vaste instapmomenten (24 per symbool), tijdindices vanaf 260 telkens 40 handelsdagen verder. $3500 per hypothetische trade, gehele aandelen, 10 basispunten kosten per zijde, entry en exit tegen openingskoers. Vaste exits 3/5/10/15/20/30/40 handelsdagen versus trailing 8% terugval vanaf hoogste slotkoers (beslissing op close, verkoop volgende open), minimaal 3, maximaal 40 dagen.

| exit | som netto P&L USD | gemiddeld USD | positieve trades |
|---|---:|---:|---:|
| 3d | -1731.79 | -18.04 | 41 |
| 5d | -1501.16 | -15.64 | 51 |
| 10d | 8073.87 | 84.10 | 57 |
| 15d | 9410.14 | 98.02 | 60 |
| 20d | 15122.83 | 157.53 | 61 |
| 30d | 18005.32 | 187.56 | 67 |
| 40d | 22491.98 | 234.29 | 61 |
| trailing 8% | 8206.46 | 85.48 | 54 |

Gemiddelde dynamische looptijd: 24.09 handelsdagen.

ZEER BELANGRIJK: dit zijn 96 onafhankelijke hypothetische trades, geen haalbaar cumulatief portefeuillerendement. Geen koopselectie door DIPSAUS, geen gelijktijdige kapitaalboekhouding, geen walk-forward holdout, geen regimecorrectie. SPY is ook als instrument getest, niet als afzonderlijke baseline. Langere duur impliceert meer marktblootstelling en verklaart mogelijk de positieve trend. Corporate actions, bronrechten, EUR/USD, spreads, liquiditeit en limietfills niet volledig geverifieerd. Geen bewijs dat 40 dagen optimaal is. Geen productieaanpassing of handelsadvies.

Volgende stap: eerlijke portefeuillevergelijking met vast kapitaal, maximaal zes posities, gescheiden train/holdout, benchmark met gelijk risico en opportunity cost.
