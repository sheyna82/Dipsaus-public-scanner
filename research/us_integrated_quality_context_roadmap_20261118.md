# DIPSAUS US shadow — geïntegreerde ontwikkelopdracht (18 november 2026)

Status: **gepland / ontwerp**, niet geïmplementeerd in productie. Dit dossier is een aanvulling op het bestaande onderzoek naar selectie-effectiviteit, breakout/retest en prospective cohort accounting.

## Eén samenhangend onderzoeksprogramma

Behoud de volledige discovery-denominator, inclusief kandidaten die niet door de eerste selectie komen, kandidaten in de overflow en ontbrekende vervolggegevens. Voeg de onderstaande vier onderdelen toe als **onderzoeksvelden en prioritering**, zonder de bestaande handelsgates te verzwakken.

### 1. Kwaliteitsscore 0–100 — onderzoek, geen handelsgoedkeuring

Voorlopige ontwerpwegingen (niet empirisch gevalideerd):
- herstelstructuur en meerdere tijdsframes: 30
- potentiële risk/reward en weerstand: 25
- markt-/sectortrend en relatieve sterkte: 20
- RVOL en liquiditeitskwaliteit: 15
- nieuws en bedrijfsgebeurtenissen: 10

Bereken een score alleen op basis van bewijs dat op het beslismoment beschikbaar was. Rapporteer ontbrekende componenten afzonderlijk als UNKNOWN; maak van ontbrekende data geen nulscore die een negatief technisch oordeel suggereert. Bewaar zowel raw component evidence als de gewichten/versie. Sorteer onderzoeksprioriteit op score, maar houd overflow en watchlist behouden. Geen automatische promotie naar `trade_ready`, meldingen of orders. R/R >=2 en verwachte EUR-nettowinst >=150 blijven harde gates.

### 2. Markt- en sectorcontext

Vergelijk een kandidaat met relevante Amerikaanse hoofdindex (S&P 500/Nasdaq, vooraf gedefinieerde keuze), bijbehorende sectorbenchmark en een tijdsconsistent venster. Meet relatieve sterkte en markt-/sectortrend; documenteer ticker/sector mapping, corporate actions, data-as-of, kalender en ontbrekende benchmarkhistorie. Benchmarkbewegingen zijn context, geen zelfstandig koopbewijs.

### 3. RVOL en uitvoerbare liquiditeit

Bereken RVOL met vergelijkbare handelsperioden; bij intraday bij voorkeur hetzelfde tijdstip van eerdere sessies, zonder toekomstige dagvolumes te gebruiken. Bestaande 20-daagse omzettriage blijft bestaan, maar vervangt geen actuele spread, bied-/laatkoers, diepte en uitvoerbare hoeveelheid via de werkelijke DEGIRO-route. Maak onderscheid tussen historisch laag volume, verhoogde spread, ontbrekende orderboekdata en technische afwijzing. Noem ADBE niet zonder actuele verificatie illiquide.

### 4. Kwartaalcijferswaarschuwing binnen vijf handelsdagen

Hergebruik bestaande Finnhub earnings-calendar research waar bevoegd en beschikbaar. Bereken vijf **beurssessies** vooruit met officieel geverifieerde Amerikaanse kalender inclusief feestdagen en verkorte sessies. Controleer symbool/issuer-match, datum, tijdzone, voor-/nabeursstatus, bronactualiteit en eventuele conflicten. Markeer `EARNINGS_WITHIN_5_SESSIONS` of `EARNINGS_DATE_UNKNOWN`; een lege of mislukte kalender is geen bevestiging dat er geen cijfers zijn. De waarschuwing is onderzoeks-/risicocontext, geen automatische order of nieuwe telefoonmelding zonder aparte toestemming.

## Geïntegreerde uitvoering

1. Eerst actuele isolated-branch CI en broncode verifiëren; productie en draft PR #65 blijven onaangeroerd.
2. Contract en testfixtures voor score, UNKNOWN-componenten en versiebeheer opstellen.
3. Markt-/sectorbenchmarks en RVOL alleen met bron-/as-of-provenance opnemen.
4. Vijfdaagse earnings-waarschuwing met officiële sessiekalender testen.
5. De score vergelijken met de bestaande EVALUATED/OVERFLOW/PENDING/REJECTED-cohorten, zonder achteraf te tunen op uitkomsten. Test op selectie-bias, missingness, lookahead en dekking.
6. Pas na een afzonderlijke empirische validatie en expliciete toestemming een eventuele productie-integratie bespreken.

## Niet-onderhandelbare grenzen

- Alleen `research/us-shadow-isolated-20261117` wijzigen, uitsluitend buiten Wall Street-handelsuren.
- Geen wijzigingen aan `main`, `research/integrated-evidence-20261106`, PR #65 of private productierepository.
- Geen private kandidaat-ID's, koersreeksen, gelicentieerde data of credentials in openbare code, tests, logs of artifacts.
- `trade_ready=False`, `notify=False`, `automatic_orders=False`, `order_placement_enabled=False`.
- Geen automatische stoploss/stoplimit of orders.
- Synthetische regressietests bewijzen geen echte voorspellende effectiviteit.
