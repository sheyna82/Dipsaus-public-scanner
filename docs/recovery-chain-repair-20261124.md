# DIPSAUS-herstelketen

## Bereik

De onderzoeksbasis is `65830a75d25d892d0491dd73499ffc8c1552d086`. De Europese runner bouwt het gecombineerde rapport in een afzonderlijk proces en bewaart het in de bestaande private EU-state. PRE-ALERT leest het gepubliceerde rapport binnen 25 minuten en beoordeelt de kandidaten opnieuw. De drie fasen zijn `EARLY_RECOVERY`, `DEGIRO_VERIFICATION` en `FINANCIAL_ENTRY_CONFIRMED`.

Een vroege melding vereist een actuele 15-minutenwaarneming van maximaal 45 minuten en de bestaande herstel- en bodemkwaliteit. Vertraagde providerkoersen van maximaal 20 minuten kunnen een DEGIRO-controle ondersteunen. De scenariofase vraagt daarnaast bewijs dat uit de private, afzonderlijke invoer komt. Uit de rapportage afkomstige financiële claims krijgen geen gezag bij verzending. De bestaande €3.500-standaardtranche wordt per scenario gebruikt. Een nieuwe positie ontvangt geen financiële promotie zodra er zes actieve posities zijn. Het beschikbare kapitaal van €50.000, portefeuilleruimte voor bijkopen en een horizon van 5–15 handelsdagen horen bij de handmatige beoordeling. De uitvoervelden `trade_ready` en `order_placement_enabled` staan op `False`.

Elke gereserveerde Europese melding gebruikt één plek in het bestaande budget. Een promotie gebruikt opnieuw één plek. Per ronde zijn er maximaal drie reserveringen, met dagelijks vijf reguliere en twee extra prioriteitsplekken. De dag volgt `Europe/Amsterdam`. INSTAPCHECK- en BIJKOOPCHECK-registraties tellen mee als brokerverificatie. Bij een gereserveerde of onzekere afleverstatus blijft het instrument die dag stil. Verval tijdens de opslag van een reservering wordt privé geregistreerd. Uitkomst en blokkadeoorzaak van de financiële berekening blijven beschikbaar voor onderzoek.

## Onafhankelijk Europees bewijs

`eu_verified_entry_inputs` is een afzonderlijke map per providersymbool in de private EU-state. De bestaande scanner levert daarvoor momenteel geen onafhankelijke bron. Bevestiging blijft geblokkeerd zolang een bevoegde beoordelaar en actuele, onafhankelijk geverifieerde brongegevens ontbreken. De runtime leest de afzonderlijk geconfigureerde SHA256-fingerprint van de publieke beoordelaarssleutel via `DIPSAUS_EU_ENTRY_REVIEWER_SHA256`.

Een invoer bestaat uit `payload`, `public_key_pem` en `signature_b64`. Het pakket bindt het providersymbool, ISIN, operating MIC, EUR-valuta, DEGIRO bied/laat en observatietijd. `target_kind` is `FIRST_MEANINGFUL_RESISTANCE`. `inputs` bevat de expliciete kosten, wisselkoers, slippage, niveaus en verificatievlaggen van `research_net_bridge.py`. Per bewijssoort bevat `attestations` de bron, observatietijd, gecontroleerde waarden en bevestiging volgens `research_net_attestation.py`. De bied- en laatprijzen in de quote moeten overeenkomen met de quote-attestatie. Voor een EUR-notering worden koersfactor 1 en beide valutakostpercentages 0 expliciet ingevuld. De privéadministratie bewaart de handtekening bij de invoer.

Het getekende bericht bestaat uit het domein `DOMAIN` van `research_ed25519_verifier.py` gevolgd door de binaire digest uit `eu_entry_net.evidence_digest`. De private sleutel hoort bij de onafhankelijke beoordelaar. De runner verifieert de sleutelpin, de handtekening, inhoud en tijdstempels. Het controleert de brokerkoers opnieuw nadat de verzending is gereserveerd. Bij verlopen bewijs volgt een lagere fase wanneer de actuele provider- en structuurgegevens daarvoor voldoende zijn. Er is geen live brokerintegratie of route voor het plaatsen van een order.

## Amerikaanse verwerking

De runner bewaart een geldige snelle route direct en combineert die na de diepe batches met alle geslaagde diepe resultaten. Per ticker blijft het bewijs van beide routes aanwezig. De snelle steekproef bevat maximaal 72 gerangschikte en 72 roterende namen uit de officiële universumlijst. Gebrekkige oppervlaktedekking en uitgevallen batches zijn zichtbaar in de private staat. Per sweep blijven maximaal 30 eerdere routes tot zeven kalenderdagen stil beschikbaar. Nieuwe observaties kunnen een instrument opnieuw voor een melding laten kwalificeren.

Beide detectieroutes en PRE-ALERT scheiden de Yahoo-metadataquote van voltooide minuutbars. Een laatste Yahoo-update buiten het minuutraster of op de sessiegrens valt alleen weg als tijdstempel, OHLC, volume en metadata overeenkomen. Een tussengat breekt de aaneengesloten structuur en een lege laatste voltooide bar blokkeert de analyse. De monitoring behoudt het bewijs van een gebroken bodem en kan een nieuw patroon na die breuk volgen. `source_verified` blijft `False`. Kwartaalcijfers en andere materiële gebeurtenissen blijven verplichte handmatige controles. Het onafhankelijke Amerikaanse rekenscenario toetst nettowinst en netto R/R aan de eerste betekenisvolle weerstand.

## Reproduceerbare controles

```bash
python --version
python -m pip install --require-hashes -r requirements.lock
python -m pip check
git ls-files -z '*.py' | xargs -0 python -m py_compile
python -m unittest -v test_eu_research_freshness test_us_recovery_chain test_us_recovery test_us_notification_safety test_migration_safety test_research_net_scenario test_research_net_bridge
python -m unittest discover -p 'test*.py'
git diff --check 65830a75d25d892d0491dd73499ffc8c1552d086 HEAD
```

De ketentests draaien met synthetische markt- en brokerdata, lokale testrapporten en gesimuleerde opslag en aflevering. De Europese ketentest voert het gecombineerde rapportproces werkelijk uit. De Amerikaanse ketentest voert de overdrachts- en routescripts uit terwijl de bronaanroepen worden vervangen. De historische Yahoo-responses van 24 november en actuele DEGIRO-invoer zijn nodig voor onafhankelijke bronvalidatie.
