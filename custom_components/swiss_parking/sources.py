"""Per-city data source adapters.

Each adapter fetches one city's live parking-guidance feed and returns a
normalized dict keyed by a stable per-garage id:

    {
        "id": str,            # stable id, used in unique_ids
        "name": str,          # display name of the garage
        "free": int | None,   # currently free spaces
        "total": int | None,  # capacity, None if the source doesn't report it
        "status": str,        # STATUS_OPEN / STATUS_CLOSED / STATUS_UNKNOWN
        "latitude": float | None,
        "longitude": float | None,
        "address": str | None,
        "link": str | None,
        "last_update": str | None,  # ISO timestamp as reported by the source
    }

There is no national aggregator for parking data (unlike ich-tanke-strom.ch
for EV chargers) — every city publishes its own feed in its own format, so
each gets a small dedicated parser. All feeds are public and unauthenticated.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify

from .const import (
    CITY_BASEL,
    CITY_BERN,
    CITY_FRAUENFELD,
    CITY_WINTERTHUR,
    CITY_ZURICH,
    FETCH_TIMEOUT_SECONDS,
    STATUS_CLOSED,
    STATUS_OPEN,
    STATUS_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)

ZURICH_URL = "https://www.pls-zh.ch/plsFeed/rss"
BASEL_URL = "https://data.bs.ch/api/explore/v2.1/catalog/datasets/100088/records?limit=100"
WINTERTHUR_URL = (
    "https://stadtplan.winterthur.ch/wms/Parkleitsystem"
    "?Service=WFS&Version=1.1.0&Request=GetFeature&TypeName=ms:ParkleitsystemLayer"
)
BERN_URL = "https://www.parking-bern.ch/parkdata.xml"
FRAUENFELD_URL = (
    "https://data.tg.ch/api/explore/v2.1/catalog/datasets/frauenfeld-1/records"
    "?limit=40&order_by=-timestamp"
)

# The Bern feed identifies most garages only by code (P01...P10). Names and
# coordinates taken from the operator's own site (www.parking-bern.ch),
# extracted 2026-07-18. Unknown names pass through as-is.
BERN_GARAGES = {
    "P01": ("Bahnhof Parking", 46.949712, 7.4385273),
    "P02": ("Metro Parking", 46.949566, 7.4442887),
    "P03": ("Rathaus Parking", 46.949149, 7.4520349),
    "P04": ("Parking City West", 46.946988, 7.4348151),
    "P05": ("Mobiliar Parking", 46.945215, 7.437787),
    "P06": ("Casinoparking", 46.946885, 7.4478077),
    "P08": ("expo Parking", 46.957102, 7.4677419),
    "P09": ("Parkplatz BERNEXPO", 46.96077, 7.4670392),
    "P10": ("Kursaal Parking", 46.952943, 7.448015),
    "P+R": ("Park + Ride Neufeld", 46.963428, 7.4321007),
}


async def _fetch_text(hass: HomeAssistant, url: str) -> str:
    session = async_get_clientsession(hass)
    async with session.get(url, timeout=FETCH_TIMEOUT_SECONDS) as resp:
        resp.raise_for_status()
        return await resp.text()


async def _fetch_json(hass: HomeAssistant, url: str) -> dict:
    session = async_get_clientsession(hass)
    async with session.get(url, timeout=FETCH_TIMEOUT_SECONDS) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


def _int_or_none(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


async def fetch_zurich(hass: HomeAssistant) -> dict[str, dict]:
    """PLS Stadt Zürich RSS feed (CC-0). Per item: title "Parkhaus Accu /
    Otto-Schütz-Weg", description "open /  164". No capacity, no coords."""
    text = await _fetch_text(hass, ZURICH_URL)
    root = ET.fromstring(text)

    garages: dict[str, dict] = {}
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        description = (item.findtext("description") or "").strip()
        link = (item.findtext("link") or "").strip() or None
        pub_date = (item.findtext("pubDate") or "").strip() or None

        name, _, address = (part.strip() for part in title.partition("/"))
        if name.lower().startswith("parkhaus "):
            name = name[len("parkhaus ") :]
        if not name:
            continue

        status_raw, _, free_raw = (part.strip() for part in description.partition("/"))
        status = {"open": STATUS_OPEN, "closed": STATUS_CLOSED}.get(status_raw.lower(), STATUS_UNKNOWN)

        match = re.search(r"pid=([A-Za-z0-9_-]+)", link or "")
        garage_id = match.group(1) if match else slugify(name)

        garages[garage_id] = {
            "id": garage_id,
            "name": name,
            "free": _int_or_none(free_raw),
            "total": None,
            "status": status,
            "latitude": None,
            "longitude": None,
            "address": address or None,
            "link": link,
            "last_update": pub_date,
        }
    return garages


async def fetch_basel(hass: HomeAssistant) -> dict[str, dict]:
    """Parkleitsystem Basel via the cantonal open data portal (data.bs.ch,
    dataset 100088). JSON with capacity, coordinates, address, and status."""
    data = await _fetch_json(hass, BASEL_URL)

    garages: dict[str, dict] = {}
    for entry in data.get("results", []):
        garage_id = entry.get("id2") or entry.get("id") or slugify(entry.get("name") or "")
        if not garage_id:
            continue
        coords = entry.get("geo_point_2d") or {}
        status = {"offen": STATUS_OPEN, "geschlossen": STATUS_CLOSED}.get(
            (entry.get("status") or "").lower(), STATUS_UNKNOWN
        )
        garages[garage_id] = {
            "id": garage_id,
            "name": entry.get("name") or entry.get("title") or garage_id,
            "free": _int_or_none(entry.get("free")),
            "total": _int_or_none(entry.get("total")),
            "status": status,
            "latitude": coords.get("lat"),
            "longitude": coords.get("lon"),
            "address": entry.get("address"),
            "link": entry.get("link"),
            "last_update": entry.get("published"),
        }
    return garages


async def fetch_winterthur(hass: HomeAssistant) -> dict[str, dict]:
    """Parkleitsystem Winterthur via the city's WFS (GML). Fields:
    ms:Name, ms:FreiePlaetze, ms:Kapazitaet, ms:Longitude, ms:Latitude,
    ms:LetzteAktualisierung, ms:UID. No open/closed flag in the feed."""
    text = await _fetch_text(hass, WINTERTHUR_URL)
    root = ET.fromstring(text)
    ns = {"ms": "http://mapserver.gis.umn.edu/mapserver"}

    garages: dict[str, dict] = {}
    for feature in root.iter("{http://mapserver.gis.umn.edu/mapserver}ParkleitsystemLayer"):
        name = (feature.findtext("ms:Name", namespaces=ns) or "").strip()
        if not name:
            continue
        garage_id = (feature.findtext("ms:UID", namespaces=ns) or "").strip() or slugify(name)
        free = _int_or_none(feature.findtext("ms:FreiePlaetze", namespaces=ns))
        total = _int_or_none(feature.findtext("ms:Kapazitaet", namespaces=ns))
        try:
            lat = float(feature.findtext("ms:Latitude", namespaces=ns))
            lon = float(feature.findtext("ms:Longitude", namespaces=ns))
        except (TypeError, ValueError):
            lat = lon = None
        garages[garage_id] = {
            "id": garage_id,
            "name": name,
            "free": free,
            "total": total,
            "status": STATUS_OPEN if free is not None else STATUS_UNKNOWN,
            "latitude": lat,
            "longitude": lon,
            "address": None,
            "link": None,
            "last_update": (feature.findtext("ms:LetzteAktualisierung", namespaces=ns) or "").strip() or None,
        }
    return garages


async def fetch_bern(hass: HomeAssistant) -> dict[str, dict]:
    """Berner Parkhäuser XML (www.parking-bern.ch/parkdata.xml). Attributes:
    name (mostly P-codes), state ("1" = open), spacecount (-1 = unknown),
    spacefree. Names/coordinates for the codes come from BERN_GARAGES."""
    text = await _fetch_text(hass, BERN_URL)
    text = text.lstrip("﻿")
    root = ET.fromstring(text)

    garages: dict[str, dict] = {}
    for parking in root.iter("parking"):
        raw_name = (parking.get("name") or "").strip()
        if not raw_name:
            continue
        mapped = BERN_GARAGES.get(raw_name)
        name = mapped[0] if mapped else raw_name
        lat = mapped[1] if mapped else None
        lon = mapped[2] if mapped else None

        total = _int_or_none(parking.get("spacecount"))
        if total is not None and total < 0:
            total = None

        garage_id = slugify(raw_name)
        garages[garage_id] = {
            "id": garage_id,
            "name": name,
            "free": _int_or_none(parking.get("spacefree")),
            "total": total,
            "status": STATUS_OPEN if parking.get("state") == "1" else STATUS_CLOSED,
            "latitude": lat,
            "longitude": lon,
            "address": None,
            "link": "https://www.parking-bern.ch",
            "last_update": root.get("updated"),
        }
    return garages


async def fetch_frauenfeld(hass: HomeAssistant) -> dict[str, dict]:
    """Stadt Frauenfeld via the cantonal open data portal (data.tg.ch,
    dataset frauenfeld-1). The dataset keeps history, so the query is sorted
    newest-first and only each area's most recent record is used. Open
    surface lots rather than garages — no open/closed state."""
    data = await _fetch_json(hass, FRAUENFELD_URL)

    garages: dict[str, dict] = {}
    for entry in data.get("results", []):
        name = (entry.get("name") or "").strip()
        if not name:
            continue
        garage_id = slugify(name)
        if garage_id in garages:
            continue  # newest record per area wins (results are sorted)
        coords = entry.get("koordinaten") or {}
        garages[garage_id] = {
            "id": garage_id,
            "name": name,
            "free": _int_or_none(entry.get("available_spots")),
            "total": _int_or_none(entry.get("total_spots")),
            "status": STATUS_OPEN,
            "latitude": coords.get("lat"),
            "longitude": coords.get("lon"),
            "address": None,
            "link": "https://data.tg.ch/explore/dataset/frauenfeld-1/",
            "last_update": entry.get("timestamp"),
        }
    return garages


CITY_FETCHERS = {
    CITY_ZURICH: fetch_zurich,
    CITY_BASEL: fetch_basel,
    CITY_WINTERTHUR: fetch_winterthur,
    CITY_BERN: fetch_bern,
    CITY_FRAUENFELD: fetch_frauenfeld,
}


async def async_fetch_city(hass: HomeAssistant, city: str) -> dict[str, dict]:
    """Fetch and normalize one city's garages. Raises on network errors;
    a single malformed garage entry is skipped, never fatal."""
    return await CITY_FETCHERS[city](hass)
