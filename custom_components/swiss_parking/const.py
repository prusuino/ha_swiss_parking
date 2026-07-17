"""Constants for the Swiss Parking integration."""
DOMAIN = "swiss_parking"

UPDATE_INTERVAL_MINUTES = 2
FETCH_TIMEOUT_SECONDS = 30

CONF_CITY = "city"

CITY_ZURICH = "zurich"
CITY_BASEL = "basel"
CITY_WINTERTHUR = "winterthur"
CITY_BERN = "bern"

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
}

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_UNKNOWN = "unknown"
