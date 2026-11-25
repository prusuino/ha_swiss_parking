"""Constants for the Swiss Parking integration."""
import json
from pathlib import Path

DOMAIN = "swiss_parking"

UPDATE_INTERVAL_MINUTES = 2
FETCH_TIMEOUT_SECONDS = 30

# Staleness cutoffs on the sources' own timestamps (see sources.mark_stale):
# a feed whose newest record is older than this counts as dead — only for
# feeds stamped on every publication (sources.FEED_STAMPED_CITIES) ...
STALE_FEED_MINUTES = 60
# ... and a single garage whose own record is older than this is withdrawn.
STALE_GARAGE_HOURS = 24

# SBB P+Rail: the published file is rebuilt every half hour, and an estimate
# from a file older than this is withdrawn.
PRAIL_UPDATE_INTERVAL_MINUTES = 30
STALE_PRAIL_MINUTES = 180

CONF_CITY = "city"
CONF_STATIONS = "stations"

CITY_ZURICH = "zurich"
CITY_BASEL = "basel"
CITY_WINTERTHUR = "winterthur"
CITY_BERN = "bern"
CITY_FRAUENFELD = "frauenfeld"
CITY_STGALLEN = "stgallen"
# Not a city: the P+Rail car parks of the SBB, of which the user picks stations.
CITY_PRAIL = "sbb_prail"

# Every supported city with its display name and per-source attribution.
# One config entry per city; the adapter functions live in sources.py.
CITIES = {
    CITY_ZURICH: {
        "name": "Zürich",
        "attribution": "Data: Parkleitsystem Stadt Zürich (CC-0)",
    },
    CITY_BASEL: {
        "name": "Basel",
        "attribution": "Data: Parkleitsystem Basel / Kanton Basel-Stadt (data.bs.ch)",
    },
    CITY_WINTERTHUR: {
        "name": "Winterthur",
        "attribution": "Data: Parkleitsystem Stadt Winterthur",
    },
    CITY_BERN: {
        "name": "Bern",
        # Terms of the operator: integrations must link to the source site.
        "attribution": "Data: Berner Parkhäuser (www.parking-bern.ch)",
    },
    CITY_FRAUENFELD: {
        "name": "Frauenfeld",
        "attribution": "Data: Stadt Frauenfeld / Kanton Thurgau (data.tg.ch)",
    },
    CITY_STGALLEN: {
        "name": "St. Gallen",
        # CC BY-NC 4.0: name the publisher and the licence.
        "attribution": "Data: PLS Parkleitsystem St.Gallen AG / Stadt St.Gallen (daten.stadt.sg.ch, CC BY-NC 4.0)",
    },
    CITY_PRAIL: {
        "name": "SBB P+Rail",
        "attribution": "Data: SBB (opentransportdata.swiss), estimated occupancy",
    },
}

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_UNKNOWN = "unknown"

LEVELS = ("low", "medium", "high")

# The integration's own version, shown on the service card. Read from the
# manifest so that a release never needs to touch two places.
VERSION: str = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))["version"]
