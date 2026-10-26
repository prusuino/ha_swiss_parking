# Changelog

## 1.3.1 — 2026-10-26

- Releases now carry the integration as a zip file (`swiss_parking.zip`), and HACS downloads that file instead of the individual files from the repository (`zip_release` in `hacs.json`). No functional change; the download count shown by HACS starts with this release.
- Nothing to do after updating.

## 1.3.0 — 2026-08-29

- **Fixed: a car park that disappears from its city's feed no longer lingers as an unavailable "restored" entity.** Until now only the live entity was removed and its entity-registry entry stayed behind, so after the next restart the car park came back as a permanently unavailable sensor (and map marker) — one more for every car park a feed drops. The registry entry is now removed together with the entity. When the car park returns under its unchanged unique id, Home Assistant restores its previous entity id and your customizations (name, icon, area, labels, visibility) from its record of deleted entities; older Home Assistant versions create it afresh.
- **New: stale data is no longer shown as live.** The sources' own timestamps are now checked: a car park whose record is older than 24 hours reports an unknown number of free spaces (status "unknown") instead of an old one, and for Basel, Bern and Frauenfeld — whose feeds are stamped on every publication — every car park does so as soon as the feed as a whole has not been updated for more than 60 minutes; `last_update` keeps the source's timestamp so you can see how old it is. Zürich and Winterthur only re-stamp a car park when its count changes, so the 60-minute feed rule is not applied to them (a quiet hour without any change would otherwise look like a dead feed). Until now a city that stopped publishing (Frauenfeld's history dataset, Bern's feed-level timestamp) kept its last numbers as "live" indefinitely. Sensors and markers still go unavailable while a feed is unreachable, as before.
- **Changed: the `last_update` attribute is ISO 8601 for every city** (e.g. `2026-08-29T20:37:32+02:00`). Zürich used the RSS date format (`Sat, 29 Aug 2026 18:24:21 GMT`), Bern `29.08.2026 20:37:32`, Winterthur a space-separated form — templates now parse all of them the same way with `as_datetime`. A template that matched one of the old formats needs adjusting.
- **Changed: new map markers get a fixed, language-independent entity id** — `geo_location.parking_<city>_<garage>`, the same pattern as the sensors — instead of one derived from the localized name (`geo_location.parkhaus_…`, `geo_location.car_park_…`). This applies to markers created from now on only: Home Assistant applies a suggested entity id when an entity is first registered, so every marker that already exists keeps the entity id it has. The `source` attribute remains the way to address markers on any instance (see the README).
- **Fixed: English texts in the "Add integration" dialog.** The English translation file was missing, so an instance in English (or any language other than German, French, Italian) showed raw keys such as `cannot_connect` instead of the messages.
- **Nothing to do on your side** unless a template of yours parsed `last_update`. No sensor or marker is renamed, removed or re-created by this update; unique ids are unchanged.
- README: the map-card example now starts with the plain form that works on every supported Home Assistant version; the labelled form (`label_mode: attribute`) is marked as needing Home Assistant 2025.4 or newer. New notes on stale data, the `last_update` format and the removal of vanished car parks. SECURITY.md now describes what the integration actually does: unauthenticated HTTPS requests to the five city feeds, no user data sent, home coordinates used locally only.
- Brand logo: `logo.png` is now the 1x rendition (600×160) and `logo@2x.png` the 2x one; both used to be the same 1200×320 file.

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
