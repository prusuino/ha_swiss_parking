# Swiss Parking

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
<a href="https://www.buymeacoffee.com/prusuino"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="20"></a>

A Home Assistant custom integration that shows the live number of free parking spaces in the car parks of Swiss cities, sourced from each city's official parking-guidance system (Parkleitsystem).

## Related integrations

More Home Assistant integrations from the same author:

- [Swiss Waters](https://github.com/prusuino/ha_swiss_waters) — live water temperature, water level, discharge and flood danger levels of Swiss rivers and lakes
- [Swiss Charging Stations](https://github.com/prusuino/ha_swiss_charging_stations) — real-time availability and prices of public EV charging stations in Switzerland
- [Austrian Charging Stations](https://github.com/prusuino/ha_austrian_charging_stations) — real-time availability of public EV charging stations in Austria
- [Swiss Transport](https://github.com/prusuino/ha_swiss_transport) — live public-transport departure boards and saved connections
- [Swiss Electricity Price](https://github.com/prusuino/ha_swiss_electricity_price) — electricity tariffs of any Swiss grid operator (ElCom)
- [Swiss Solar Reference Price](https://github.com/prusuino/ha_swiss_solar_reference_price) — the Swiss solar reference market price (SFOE)
- [Swiss Earthquakes](https://github.com/prusuino/ha_swiss_earthquakes) — recent Swiss earthquakes on the built-in map
- [Swiss Public Alerts](https://github.com/prusuino/ha_swiss_public_alerts) — official Swiss public alerts (Alertswiss) with home-location matching
- [Swiss Avalanche Bulletin](https://github.com/prusuino/ha_swiss_avalanche_bulletin) — the official SLF avalanche bulletin for your location
- [Innoxel Master 3](https://github.com/prusuino/ha_innoxel_master3) — local control of the Innoxel Master 3 home-automation system
- [Swiss Hail Protection](https://github.com/prusuino/ha_swiss_hail_protection) — Swiss hail warnings for your blinds: the official VKF hail-protection signal or the MeteoSwiss hail radar around your location

## Supported cities

| City | Car parks | Source |
|---|---|---|
| Zürich | ~36 | PLS Parkleitsystem Stadt Zürich (RSS, CC-0) |
| Basel | 16 | Kanton Basel-Stadt open data portal (JSON) |
| Winterthur | 13 | Stadtplan Winterthur (WFS) |
| Bern | ~12 | Berner Parkhäuser (XML) |
| Frauenfeld | 6 | Stadt Frauenfeld / Kanton Thurgau open data portal (JSON) |

There is no national aggregator for parking data in Switzerland — each city publishes its own feed in its own format, so each city has its own small adapter. Other cities either publish no machine-readable real-time feed at all, or their feed was found dead at the time of writing (St. Gallen) or requires an access token (Geneva). New adapters are welcome — open an issue if your city publishes a feed.

## What it provides

One config entry per city (add the integration again for another city):

| Entity | Type | Description |
|---|---|---|
| `sensor.parking_<city>_<garage>` | Sensor | State = currently free spaces of one car park. Attributes: localized status (open/closed/unknown), capacity, occupancy %, address, link, coordinates, last update (ISO 8601). |
| `geo_location.parking_<city>_<garage>` (markers created before 1.3.0 keep their localized id — see [Addressing the map markers](#addressing-the-map-markers)) | Geo-location | One map marker per car park with known coordinates, labeled with the live number of free spaces ("158 free") or "Closed", refreshed in place on every update; the marker goes unavailable while the city's feed is unreachable. State = distance from your Home Assistant home zone (km). Attributes: status label, free, total, address, link, last update (ISO 8601). Zürich's feed contains no coordinates, so Zürich creates sensors only. Frauenfeld reports open surface lots (no open/closed state). |

Data refreshes every 2 minutes. Garages appearing in or disappearing from a feed are picked up automatically.

### Addressing the map markers

Since 1.3.0 a new map marker gets the same fixed, language-independent entity id as its sensor: `geo_location.parking_<city>_<garage>`. Markers that existed before keep the id they have — Home Assistant applies a suggested id only when an entity is first registered — and those ids were derived from the localized name: the same car park is `geo_location.parkhaus_bahnhof_parking` on a German instance and `geo_location.car_park_bahnhof_parking` on an English one (French `geo_location.parking_…`, Italian `geo_location.parcheggio_…`). A card or template written against one of those ids does not carry over to another instance, so do not address markers by entity id — use their `source` attribute, which is always `swiss_parking`:

- **Map card** — `geo_location_sources` draws every marker of this integration (also the ones hidden from the auto-generated overview) and follows car parks as they come and go:

  ```yaml
  type: map
  geo_location_sources:
    - swiss_parking
  ```

  On Home Assistant 2025.4 or newer the source can be given as an object, which puts the live number of free spaces on the marker label:

  ```yaml
  type: map
  geo_location_sources:
    - source: swiss_parking
      label_mode: attribute
      attribute: status
  ```

- **Templates** — filter the `geo_location` domain on the `source` attribute instead of naming entities:

  ```jinja
  {{ states.geo_location
     | selectattr('attributes.source', 'eq', 'swiss_parking')
     | rejectattr('attributes.free', 'none')
     | selectattr('attributes.free', 'gt', 0)
     | map(attribute='name') | list }}
  ```

  This lists the car parks with at least one free space, in any language.

What does stay the same in every language is a marker's unique id (config entry + garage id), which is what the entity registry keys on — so renaming a marker or changing its visibility in the registry survives restarts and updates.

The map markers are hidden from Home Assistant's auto-generated default dashboard (which would draw every `geo_location` entity in the system); a Map card with `geo_location_sources` as above shows them regardless. This only applies when a marker is first created — one you made visible yourself stays visible.

## Language

Entity and device names as well as status values adapt automatically to your Home Assistant language setting — German, English, French, and Italian are supported, with English as the fallback. Garage names from the sources are shown as-is.

## Installation

### HACS (recommended)

1. Open **HACS**, search for **"Swiss Parking"** and download it — or use the button, which opens the integration directly in your HACS:

   [![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=prusuino&repository=ha_swiss_parking&category=integration)

2. Restart Home Assistant.

Until the integration shows up in the HACS search, the button above adds it as a custom repository.

### Manual

1. Copy the `custom_components/swiss_parking` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **"Swiss Parking"**.
3. Pick a city — the feed is probed live before the entry is created. Add the integration again for another city.

## Notes

- The Bern feed identifies most garages only by code (P01…P10); the integration maps these to their real names and coordinates as published on the operator's own site.
- Capacity ("total") is not reported by every source for every garage; the occupancy percentage attribute is only set where it is.
- A malformed entry in a source feed is skipped and never breaks the whole update.
- If a city's feed is unreachable, its sensors and map markers go unavailable rather than showing stale numbers; they recover on the next successful update.
- Stale data is not shown as live either: the sources' own timestamps are checked. A car park whose record is older than 24 hours reports an unknown number of free spaces (status "unknown") instead of an old one; `last_update` keeps the source's timestamp so you can see how old it is. For Basel, Bern and Frauenfeld, whose feeds are stamped on every publication, every car park is withdrawn this way as soon as the feed as a whole has not been updated for more than 60 minutes. Zürich and Winterthur only re-stamp a car park when its count changes, so a quiet hour without any change is normal there; the 60-minute feed rule is therefore not applied to those two cities, and the per-car-park limit is deliberately generous for the same reason.
- The `last_update` attribute is ISO 8601 with a time-zone offset for every city (e.g. `2026-08-29T20:37:32+02:00`), whatever format the source uses, so `as_datetime` works on it in templates.
- A car park that disappears from its city's feed is removed together with its entity-registry entry, so it does not linger as an unavailable "restored" entity. When it reappears under the same unique id, Home Assistant restores its previous entity id and your customizations (name, icon, area, labels, visibility) from its record of deleted entities; older Home Assistant versions create it afresh.

## Data sources & license

See [NOTICE.md](NOTICE.md) for the per-city data sources and their attribution requirements. The integration sets the appropriate `attribution` attribute on every entity. For Bern, the operator requires a link to [www.parking-bern.ch](https://www.parking-bern.ch) — the integration carries it as an entity attribute; please keep it visible if you republish the data.

## Disclaimer

This is an unofficial integration, not affiliated with, endorsed by, or supported by any of the cities, their parking-guidance system operators, or the garage operators. Displayed availability may lag behind reality; no guarantee is given for correctness or availability of the data.

## License

[MIT](LICENSE) — the license covers this integration's code only, not the data provided by the sources.

## Support

If this integration is useful to you, you can support its development:

<a href="https://www.buymeacoffee.com/prusuino"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="41"></a>
