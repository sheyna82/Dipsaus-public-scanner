# Gratis dataprovenance — onderzoekscontrole (21 oktober 2026)

Doel: earnings-onderzoek zonder betaalde API's, scraping van afgeschermde sites of live wijzigingen.

## SEC EDGAR: geschikt als officiële Amerikaanse bron

Officiële documentatie:
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/about/webmaster-frequently-asked-questions

- **Kosten**: SEC data.sec.gov submissions en XBRL companyfacts zijn publiek, zonder authenticatie/API-sleutel. Overheidsinhoud en openbare EDGAR filings zijn vrij te benaderen en hergebruiken.
- **Beschikbare gegevens**: filing history, 10-Q/10-K/8-K en XBRL companyfacts; geen analistenverwachtingen, optie-implied move of gegarandeerde beurskoersfeed.
- **Toegang**: SEC fair-access maximaal 10 requests/sec, gebruik een duidelijk geïdentificeerde User-Agent met contactadres; conservatief trager en met caching. Geen echte contactgegevens in publieke repository hardcoderen.
- **Historische tijd**: rapportageperiode en filed date zijn niet hetzelfde als publicatietijd. De SEC zegt expliciet dat er geen veld is dat exact aangeeft wanneer de inhoud voor het eerst op sec.gov beschikbaar was. Gebruik acceptance timestamps plus een conservatieve vertraging, niet 'period end' als publicatiedatum.
- **Correcties**: amendments en revisies kunnen later beschikbaar komen; selecteer uitsluitend destijds beschikbare filings voor backtests. Een huidige companyfacts-download is geen point-in-time snapshot.
- **Reikwijdte**: voor EXE moet de correcte juridische entiteit en CIK afzonderlijk worden geverifieerd vóór integratie; ticker is geen stabiele primaire sleutel.

## Stooq: geen productieafhankelijkheid

Onderzoeksbronnen:
- https://stooq.com/
- https://stockmarketstack.com/tools/stooq

Stooq biedt historische marktgegevens voor persoonlijk onderzoek, maar geautomatiseerde toegang is in 2026 fragiel (captcha, blokkades, mogelijk API-sleutel), en herdistributie/licenties zijn beperkt. **Geen automatische Stooq-connector toevoegen**, geen captcha-omzeiling of scraping. Alleen handmatig onderzoek indien voorwaarden dat toestaan.

## Acceptatiecriteria vóór earnings-integratie

1. Gratis toegestane toegang en stabiele bron, inclusief EU/VS-dekking waar nodig.
2. Exacte entiteit/ticker/CIK mapping; hernoemingen en corporate actions.
3. Point-in-time publicatie-/acceptatietijd, tijdzone en amendmentcontrole.
4. Scheiding tussen officieel gerapporteerde cijfers, consensusverwachtingen en prijsreactie.
5. Missing-data expliciet; geen schijnvoorspellingen.
6. API-verzoeken alleen na afzonderlijke veiligheidsreview, met limieten, caching en geen secrets in public repo.
7. Eerst offline fixture-tests en forward-paper-validatie; geen live alerts of orders.

Status: **documentatieonderzoek**, geen SEC-verzoeken uitgevoerd, geen EXE-data ingeladen, geen handelsresultaten aangetoond.
