# DIPSAUS — operationeel besluit: eerste echte prijs- en winstproef
Datum: 2026-10-26
Status: BLOCKED_PENDING_CI_AND_DATA. Research-only, geen wijzigingen aan productie.

## Vastgesteld via GitHub Actions
- Public price acquisition experiment run 40316572014: job public-price-probe QUEUED, geen logs of uitkomst.
- Portfolio profit reconciliation run 40316572019: job portfolio-profit-tests QUEUED.
- Closed-trade diagnostics run 40316571934: job profit-tests QUEUED.
- Signal prefix lookahead run 40316571841: job prefix-tests QUEUED.
- Eerder limit-fill-tests run 40316350402: job COMPLETED/SUCCESS.
- De oorzaak van de wachtrij is nog NIET vastgesteld; niet concluderen dat runner, limiet of account fout is zonder bewijs.

## Kritiek pad
1. Controleer Actions-instellingen, uitvoeringslimieten en de PR-checks via GitHub UI als jobs blijven hangen; vraag gebruiker alleen om gerichte UI-stappen indien connector geen Actions-beheer ondersteunt.
2. Voer eenmalige Stooq metadata-proef uit op een toegestaan symbool, alleen met expliciete netwerktoestemming. Geen bronlicentie of koerscorrecties veronderstellen.
3. Leg vast: bron, exacte downloadtijd, SHA256, handelsdatumbereik, ontbrekende sessies, corporate actions, symbol mapping en eventuele providerfouten.
4. Gebruik alleen gevalideerde lokale onderzoeksbestanden; laat licentie en datakwaliteit beoordelen voordat data worden gedeeld of langdurig opgeslagen.
5. Voor eerste netto winstvergelijking: identieke kandidaatset en periode, next-session-open, spread/slippage/commissie, max zes posities, 3/5/10 dagen, een simpele baseline, geen lookahead.
6. Maak onderscheid tussen een indicatieve historische simulatie en onafhankelijk out-of-sample gevalideerd rendement. Publiceer ook aantal trades, totale netto winst, expectancy, profit factor, drawdown indien chronologische equity beschikbaar, en gemiste orders.
7. Stop bij onduidelijke dataherkomst, niet-uitgevoerde CI of onvoldoende steekproef. Geen winstclaims.

## Open technische beperkingen
- GitHub-koppeling biedt geen workflow_dispatch-actie. De manual-only workflow kan bovendien onzichtbaar zijn als het workflowbestand niet op default branch bestaat.
- Stooq-netwerkprobe vanuit lokale container strandde eerder op DNS; dit bewijst niets over de provider.
- Daily OHLCV bewijst geen openingsveilingvolume, orderfills of bedrijfsactiecorrecties.
- Nieuwe profit-reportmodule gebruikt simulatietrades en is nog niet door GitHub CI bevestigd.
- Geen main-merge, live alerts, brokers, orders of frozen momentumprotocol wijzigen.
