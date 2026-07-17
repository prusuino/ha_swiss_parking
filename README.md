# Swiss Parking

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration that shows the live number of free parking spaces in the car parks of Swiss cities, sourced from each city's official parking-guidance system (Parkleitsystem).

## Supported cities

| City | Car parks | Source |
|---|---|---|
| Zürich | ~36 | PLS Parkleitsystem Stadt Zürich (RSS, CC-0) |
| Basel | 16 | Kanton Basel-Stadt open data portal (JSON) |
| Winterthur | 13 | Stadtplan Winterthur (WFS) |
| Bern | ~12 | Berner Parkhäuser (XML) |

There is no national aggregator for parking data in Switzerland — each city publishes its own feed in its own format, so each city has its own small adapter. Other cities either publish no machine-readable real-time feed at all, or their feed was found dead at the time of writing (St. Gallen) or requires an access token (Geneva). New adapters are welcome — open an issue if your city publishes a feed.

## What it provides

One config entry per city (add the integration again for another city):

| Entity | Type | Description |
|---|---|---|
| `sensor.parking_<city>_<garage>` | Sensor | State = currently free spaces of one car park. Attributes: localized status (open/closed), capacity, occupancy %, address, link, coordinates, last update. |
| `geo_location.parking_...` | Geo-location | One map marker per car park with known coordinates, labeled with the live number of free spaces ("158 free") or "Closed". State = distance from your Home Assistant home zone (km). Zürich's feed contains no coordinates, so Zürich creates sensors only. |

Data refreshes every 2 minutes. Garages appearing in or disappearing from a feed are picked up automatically.

The map markers are hidden from Home Assistant's auto-generated default dashboard (which would draw every `geo_location` entity in the system); add your own Map card with `geo_location_sources: [swiss_parking]` and `label_mode: attribute` / `attribute: status` to see them with their live labels.

## Language

Entity and device names as well as status values adapt automatically to your Home Assistant language setting — German, English, French, and Italian are supported, with English as the fallback. Garage names from the sources are shown as-is.

## Installation

### HACS (recommended)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**, add this repository URL with category **Integration**.
2. Search for **"Swiss Parking"** and install.
3. Restart Home Assistant.

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

## Data sources & license

See [NOTICE.md](NOTICE.md) for the per-city data sources and their attribution requirements. The integration sets the appropriate `attribution` attribute on every entity. For Bern, the operator requires a link to [www.parking-bern.ch](https://www.parking-bern.ch) — the integration carries it as an entity attribute; please keep it visible if you republish the data.

## Disclaimer

This is an unofficial integration, not affiliated with, endorsed by, or supported by any of the cities, their parking-guidance system operators, or the garage operators. Displayed availability may lag behind reality; no guarantee is given for correctness or availability of the data.

## License

[MIT](LICENSE) — the license covers this integration's code only, not the data provided by the sources.
