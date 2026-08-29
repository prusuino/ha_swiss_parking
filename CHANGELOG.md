# Changelog

## 1.2.0 — 2026-08-29

- **Fixed: map markers go unavailable while a city's feed is unreachable**, as the sensors already did. Until now a marker kept showing its last known label ("158 free") indefinitely, however stale the number behind it was. It comes back by itself with the next successful update.
- **Fixed: map markers you made visible by hand are no longer hidden again on every restart.** The old code re-applied its "hidden" flag to any marker that had none — which is exactly what unhiding one leaves behind, so the choice never survived a restart. New markers are still hidden by default so they do not flood Home Assistant's auto-generated overview map; existing ones are left alone.
- **Nothing to do on your side.** No entity is renamed, removed or re-created, and every sensor and map marker keeps the entity id it has. The markers' unique ids already include the config entry, so two city entries never compete for the same marker — no migration was needed.
- Documented: a map marker's entity id follows its localized name (`geo_location.parkhaus_…` on a German instance, `geo_location.car_park_…` on an English one), so it differs between installations. The README now shows how to address markers independently of the language — the map card's `geo_location_sources` and the `source` attribute in templates.
- README: the installation instructions now describe the HACS default listing, with a My Home Assistant button that opens the integration directly in HACS.

## 1.1.0 — 2026-07-18

- New: **Frauenfeld** (Stadt Frauenfeld / Kanton Thurgau open data portal).

## 1.0.0 — 2026-07-18

- Initial release: live free-space sensors and map markers for the car parks of Zürich, Basel, Winterthur and Bern.
