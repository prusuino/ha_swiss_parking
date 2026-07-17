# Data Sources & Attribution

This integration retrieves live parking data at runtime from the public parking-guidance feeds of the supported Swiss cities. There is no national aggregator — each city publishes its own feed under its own terms:

| City | Source | Terms |
|---|---|---|
| Zürich | [PLS Parkleitsystem Stadt Zürich](https://www.pls-zh.ch/) RSS feed | **CC-0** (stated in the feed itself) |
| Basel | [Kanton Basel-Stadt open data portal](https://data.bs.ch/explore/dataset/100088/) (Parkleitsystem Basel) | Open data of Kanton Basel-Stadt, attribution requested |
| Winterthur | [Stadtplan Winterthur WFS](https://stadtplan.winterthur.ch/) (Parkleitsystem, Tiefbauamt) | Open Government Data of Stadt Winterthur |
| Bern | [Berner Parkhäuser](https://www.parking-bern.ch/) XML interface | Free to use with a **link to www.parking-bern.ch**; resale of the data is prohibited |

The integration fulfills the attribution requirements by setting the `attribution` attribute on every entity it creates (e.g. `"Data: Berner Parkhäuser (www.parking-bern.ch)"`), which Home Assistant surfaces in the entity's "More Info" dialog, and by carrying the source link as an entity attribute where available. If you build dashboards, automations, or republish this data elsewhere, please keep the respective attribution visible — for Bern in particular, keep a link to www.parking-bern.ch.

This integration is unofficial and not affiliated with, endorsed by, or supported by any of the cities, their parking-guidance system operators, or the garage operators. It only reads their publicly published feeds.
