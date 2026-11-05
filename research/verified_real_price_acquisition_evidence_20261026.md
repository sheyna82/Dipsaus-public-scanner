# DIPSAUS — eerste bevestigde echte marktdata, GitHub-run 40316862372
Datum: 2026-10-26. Research-only. Geen live handelsadvies.

## Direct gecontroleerd in GitHub joblog
- Run 40316862372, job 121551526139, COMPLETED/SUCCESS.
- Stooq AMD 2026-10-01 t/m 2026-10-23: unavailable, vendor_http_error:404. Een groene workflow betekent dus niet dat elke provider slaagt.
- Yahoo chart HTTP 200 voor AMD, daarna genormaliseerde (nog niet onafhankelijk geverifieerde) reeksen:
  - TSLA, META, COHU, AMZN, PLTR, AMD, SPY: elk 251 waarnemingen van 2025-10-24 t/m 2026-10-23.
  - COHU, AMD, META, SPY: elk 1255 waarnemingen van 2021-10-25 t/m 2026-10-23.
- Hashes, tijdstippen en bronclaims in joblog; geen rechten of authenticiteit onafhankelijk bevestigd.
- Vijfjaars momentum/holdout en downside exploratie is uitgevoerd. Signalen wisselen per holdout. Downside evidence gate gaf 'descriptive_evidence_sufficient: false' wegens overlappende of ontbrekende onafhankelijke intervallen.
- Geen bevestigde winstgevende strategie, geen sluitende 3/5/10-daagse netto portfoliovergelijking met daadwerkelijke volgende-open uitvoeringen op deze dataset.

## Kritieke vervolgstap
Gebruik uitsluitend gecontroleerde dataset met vastgelegde provenance en aanpassing voor splits/dividenden. Ontwikkel op basis van die reeksen een causale, gelijktijdige baselinevergelijking met next-session-open, transactiekosten, liquiditeitsbeperkingen, maximaal zes posities en 3/5/10 handelsdagen. Leg selectiecriteria vooraf vast; valideer zonder terugkijken en zonder datalek. Geen externe orders of productieaanpassingen.

## Veiligheid
Onderzoeksbranch, geen wijzigingen aan main, bevroren momentumprotocol, productiealerts of brokerkoppelingen.
