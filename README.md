# PstRotator voor Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Besturing van [PstRotator](https://www.qsl.net/yo3dmu/index_Page346.htm) (YO3DMU)
vanuit Home Assistant, met een kleurrijke, interactieve azimutale wereldkaart:
klik op de kaart en de antennerotor draait direct die richting op.

## Wat zit erin

- **Backend-integratie** die een `number`-entiteit aanmaakt voor de
  gecommandeerde azimuth. Elke wijziging (via de kaart, de HA-UI, een
  service-call of een automation) wordt doorgestuurd naar PstRotator over
  het netwerk.
- **Lovelace-kaart** (`pstrotator-card`) met een **azimutale equidistante
  wereldkaart**, gecentreerd op je HA-thuislocatie. Dit projectietype is
  bewust gekozen (in plaats van een gewone Mercator-wereldkaart): de hoek
  van elk punt op de kaart ten opzichte van het midden is *exact* de
  werkelijke kompaskoers (great-circle bearing) — precies wat een
  rotor nodig heeft.
  - Klik ergens op de kaart → de rotor draait naar die richting.
  - `+5°` / `−5°` knoppen (stapgrootte instelbaar) om bij te sturen.
  - Gekleurde continenten/oceaan, afstandscirkels (5000/10000/15000 km) en
    een kompasroos met N/E/S/W.

## Installatie via HACS

1. HACS → rechtsboven **⋮** → **Custom repositories**.
2. Voeg deze repository-URL toe, categorie **Integration**.
3. Zoek naar **PstRotator** in HACS en installeer.
4. Herstart Home Assistant.
5. **Instellingen → Apparaten & diensten → Integratie toevoegen → PstRotator**.

## PstRotator configureren

Deze integratie praat standaard met de **Hamlib `rotctld`-compatibele**
netwerkinterface van PstRotator:

1. Open PstRotator → **Settings** → **Rotor interfacing** (of vergelijkbaar,
   afhankelijk van je versie) → schakel **"Hamlib Net rotctl"** (rotctld
   emulation) in.
2. Noteer het IP-adres van de PC waarop PstRotator draait en de ingestelde
   poort (standaard `4533`).
3. Vul dit in tijdens het instellen van de integratie in Home Assistant.

Gebruikt jouw PstRotator-opstelling een ander netwerkprotocol (bijvoorbeeld
de UDP-interface voor de PstRotatorAZ-app)? Kies dan in de
integratie-opties **"Custom text command"** en stel je eigen commando-
template in, met `{az}` als plaatshouder voor de azimuth, bijvoorbeeld:

```
AZ{az:.1f}\n
```

## De kaart toevoegen aan je dashboard

Na installatie wordt de kaart automatisch als Lovelace-resource geregistreerd.
Voeg daarna een kaart toe met:

```yaml
type: custom:pstrotator-card
entity: number.pstrotator_azimuth
title: Antenne richting
step: 5
```

Optionele configuratie-opties:

| Optie | Omschrijving | Standaard |
|---|---|---|
| `entity` | **(verplicht)** De `number`-entiteit van PstRotator | — |
| `title` | Titel boven de kaart | `PstRotator` |
| `step` | Stapgrootte van de +/− knoppen | `5` |
| `home_latitude` / `home_longitude` | Overschrijf de HA-thuislocatie | HA-thuislocatie |
| `land_color`, `ocean_from`, `ocean_to`, `line_color` | Kleuren aanpassen | zie `pstrotator-card.js` |

Als de kaart niet automatisch verschijnt in de resource-lijst, voeg hem
handmatig toe via **Instellingen → Dashboards → Resources**:

- URL: `/pstrotator_files/pstrotator-card.js`
- Type: JavaScript module

## Services / automations

De integratie gebruikt de standaard `number.set_value`-service, dus je kunt
de azimuth ook rechtstreeks vanuit automations aansturen:

```yaml
action: number.set_value
target:
  entity_id: number.pstrotator_azimuth
data:
  value: 123.4
```

## Kaartdata

De werelddata (continenten) komt van [Natural Earth](https://www.naturalearthdata.com/)
(110m resolutie, publiek domein) en wordt lokaal meegeleverd — er wordt geen
externe data opgehaald tijdens gebruik.

## Licentie

MIT, zie [LICENSE](LICENSE).
