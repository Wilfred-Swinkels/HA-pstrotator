*[Lees dit in het Nederlands](README.nl.md)*

# PstRotator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Control [PstRotator](https://www.qsl.net/yo3dmu/index_Page346.htm) (YO3DMU)
from Home Assistant with a colorful, interactive azimuthal world map: click
anywhere on the map and the antenna rotator turns straight to that bearing.

## What's included

- **Backend integration** that creates a `number` entity for the commanded
  azimuth. Every change (from the map, the HA UI, a service call, or an
  automation) is forwarded to PstRotator over the network.
- **Lovelace card** (`pstrotator-card`) with an **azimuthal-equidistant
  world map** centered on your HA home location. This projection was
  chosen deliberately instead of a plain Mercator world map: the angle of
  every point on the map relative to the center is *exactly* the true
  compass bearing (great-circle bearing) — precisely what a rotator needs.
  - Click anywhere on the map, or press and hold the line and drag it
    around → the rotator follows that direction.
  - `+5°` / `−5°` buttons (step size configurable) for fine adjustment.
  - The direction line is always exactly the radius of the circle (fixed
    length, no arrowhead) — only the angle changes.
  - Colored continents/ocean, distance rings (5000/10000/15000 km), and a
    compass rose with N/E/S/W.
  - Home location configurable via a **QTH locator** (e.g. `JO32wd`),
    manual coordinates, or automatically from Home Assistant's own home
    location.

## Installation via HACS

1. HACS → top-right **⋮** → **Custom repositories**.
2. Add this repository URL, category **Integration**.
3. Search for **PstRotator** in HACS and install it.
4. Restart Home Assistant.
5. **Settings → Devices & services → Add integration → PstRotator**.

## Configuring PstRotator

By default this integration talks to PstRotator's **Hamlib
`rotctld`-compatible** network interface:

1. In PstRotator, open **Settings** → **Rotor interfacing** (naming may
   vary by version) → enable **"Hamlib Net rotctl"** (rotctld emulation).
2. Note the **IP address** of the PC running PstRotator and the configured
   port (default `4533`).
3. Enter this **host/IP address and port** when setting up the integration
   in Home Assistant (and adjustable later through the integration's
   options).

Does your PstRotator setup use a different network protocol (e.g. the UDP
interface used by the PstRotatorAZ app)? Choose **"Custom text command"**
in the integration options and set your own command template, using `{az}`
as a placeholder for the azimuth, for example:

```
AZ{az:.1f}\n
```

## Home location (map center)

The center of the map — and therefore the zero reference for every
computed bearing — is determined in this order of priority:

1. A **QTH locator** (Maidenhead grid square, e.g. `JO32` or, more
   precisely, `JO32wd`), entered during setup or via the integration's
   options. This is the recommended approach: more precise than a country,
   and the notation amateur radio operators already use.
2. Manual **latitude/longitude**, also via the integration's options, for
   anyone who prefers plain coordinates.
3. Otherwise, automatically, Home Assistant's own **home location** (as
   set under **Settings → System → General**).

This location is passed to the card automatically via the `number` entity
— you don't need to change anything in the card configuration itself,
unless you deliberately want to override it (see `home_latitude` /
`home_longitude` below).

## Adding the card to your dashboard

After installation the card is automatically registered as a Lovelace
resource. Then add a card with:

```yaml
type: custom:pstrotator-card
entity: number.pstrotator_azimuth
title: Antenna heading
step: 5
```

Optional configuration options:

| Option | Description | Default |
|---|---|---|
| `entity` | **(required)** PstRotator's `number` entity | — |
| `title` | Title shown above the card | `PstRotator` |
| `step` | Step size of the +/− buttons | `5` |
| `home_latitude` / `home_longitude` | Override the location from the integration/HA | see "Home location" above |
| `land_color`, `ocean_from`, `ocean_to`, `line_color` | Customize colors | see `pstrotator-card.js` |

If the card doesn't appear automatically in the resource list, add it
manually via **Settings → Dashboards → Resources**:

- URL: `/pstrotator_files/pstrotator-card.js`
- Type: JavaScript module

## Services / automations

The integration uses the standard `number.set_value` service, so you can
drive the azimuth directly from automations too:

```yaml
action: number.set_value
target:
  entity_id: number.pstrotator_azimuth
data:
  value: 123.4
```

## Map data

The world data (continents) comes from [Natural Earth](https://www.naturalearthdata.com/)
(110m resolution, public domain) and is bundled locally — no external data
is fetched at runtime.

## License

MIT, see [LICENSE](LICENSE).
