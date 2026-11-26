# DIPSAUS laatste technische reparatieronde

Basis `d1dddb124da418811caf739a99a6229bf9c23d93`. De reparaties gebruiken de bestaande private meldingshistorie, koersvalidator en capaciteitscontrole.

| Regressie | Bevinding op de basiscommit | Gedrag na reparatie |
| --- | --- | --- |
| R01–R02 | Na verval tijdens reservering blokkeerde de opgeslagen vroege of bevestigde melding de volgende geldige poging. | Een nieuwe koers- en bewijsvalidatie kan opnieuw reserveren. Een oudere geslaagde fase blijft gelden als een promotie vervalt. |
| R03 | Dezelfde sleutel werd niet herhaald. Een onzekere vroege aflevering kon wel gevolgd worden door een bevestigde melding op dezelfde dag. | Zolang aflevering die dag onzeker is, blijven beide fasen geblokkeerd. Een serverfout of time-out blijft onzeker. |
| R04–R05 | Ontbrekende bronmetadata en kwalificatietijden konden door de poort. Een opgegeven kwalificatie die tijdens reservering verliep, werd al tegengehouden. | De automatische melding vereist een herkende bron, een bij de koers passend voltooide minuutbalk en actuele kwalificatie van dezelfde herstelroute. Na het opslaan van de reservering volgt dezelfde controle. |
| R06 | Vroege meldingen die aantoonbaar niet waren verzonden, telden mee voor het dagbudget. | Verval vóór verzending en definitieve afwijzing tellen niet mee. Reserveringen en onzekere afleveringen blijven meetellen. |
| R07 | Een overlap met het automatische register kon de handmatige of portefeuillebewaking uit de ronde houden. | Handmatige bewaking draait onafhankelijk van de rotatie. Een ticker die beide routes volgen, gebruikt één koersopvraag met aparte routebevindingen. |
| R08 | Een afgeleverd financieel scenario bleef na afzien van aankoop ruimte innemen. | Een expliciet besluit kan de exacte reservering eenmaal vrijgeven. Andere reserveringen en actuele kapitaal- en positiegrenzen blijven gelden. |
| R09 | De volgorde van vroege signalen volgde de invoervolgorde. | Rangschikking gebruikt herovering van de herstelzone, relatieve afstand tussen hogere bodem en herstelbodem, consistentie van het koersverloop en quoteactualiteit. |
| R10 | De doorbraak onder de herstelbodem werd al als invalidatie geregistreerd. | Een melding vereist een nieuwe, gevalideerde structuur vanaf de geregistreerde breuk. |

## Capaciteit vrijgeven

Een geautoriseerde beheerder kan in de bestaande **private** `config/notification_quality_gate.json` een besluit opnemen in `eu_capacity_declines`. Kopieer de exacte sleutel en `notified_utc` uit het afgeleverde `FINANCIAL_ENTRY_CONFIRMED`-record. `decided_utc` is de werkelijke beslissingstijd, met tijdzone. Voorbeeld met fictieve gegevens.

```json
{
  "eu_capacity_declines": [
    {
      "reservation_key": "EU-RESEARCH|EXAMPLE.PA|FINANCIAL_ENTRY_CONFIRMED|2026-11-26",
      "notified_utc": "2026-11-26T10:00:00+00:00",
      "decided_utc": "2026-11-26T10:05:00+00:00"
    }
  ]
}
```

De runner slaat `capacity_released_utc` op bij het bestaande record. Herhaling van het besluit heeft geen extra effect. Een onzekere of nog lopende aflevering kan op deze manier geen ruimte vrijgeven. De afgeleverde melding blijft meetellen voor het dagbudget en de ontdubbeling. Een verandering in de posities wist openstaande adviezen van dezelfde dag niet. Financiële capaciteit wordt opnieuw getoetst aan de actuele, onafhankelijk beoordeelde portefeuille-invoer. De vrijgave verandert geen brokerorder.

## Reproduceerbare controles

```bash
python -m pip install --require-hashes -r requirements.lock
python -m pip check
git ls-files -z '*.py' | xargs -0 python -m py_compile
python -m unittest -v test_final_recovery_repairs test_eu_research_freshness.EUBrokerAndHandoffTests.test_R08_decline_releases_exact_reservation_once_and_preserves_limits
python -m unittest discover -p 'test*.py'
```

De regressietests simuleren klok, provider, opslag, aflevering en brokerinvoer. Koersdrempels, meldingslimieten en bewakingsintervallen behouden hun bestaande waarden. `trade_ready` en `order_placement_enabled` blijven `False`. Empirische kalibratie en historische prestatievalidatie vallen buiten deze ronde.
