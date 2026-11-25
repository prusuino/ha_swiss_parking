"""SBB P+Rail: the car parks at Swiss railway stations.

opentransportdata.swiss publishes one file with every P+Rail facility of the
country (dataset bike-and-car-parking, about 10 MB of JSON, under 1 MB on the
wire) and rebuilds it every half hour. It carries an *estimated* occupancy
between 0 and 1 for the facilities the SBB has enough data on, plus a typical
week by the hour. Nothing is counted, so there is no number of free spaces.

The file is downloaded whole and reduced to the chosen stations in the
executor.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import FETCH_TIMEOUT_SECONDS, LEVELS, STALE_PRAIL_MINUTES, STATUS_OPEN, STATUS_UNKNOWN

PRAIL_URL = "https://data.opentransportdata.swiss/dataset/bike-and-car-parking/permalink"
PRAIL_LINK = "https://data.opentransportdata.swiss/dataset/bike-and-car-parking"
TIME_ZONE = "Europe/Zurich"
WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
FORECAST_HOURS = 24


def _percent(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(min(max(value, 0), 1) * 100)


def _point(geometry: Any) -> tuple[float | None, float | None]:
    """(latitude, longitude) of the point among the facility's geometries."""
    for part in (geometry or {}).get("geometries") or [geometry or {}]:
        if part.get("type") == "Point":
            lon, lat = part["coordinates"][:2]
            return lat, lon
    return None, None


def _typical_week(forecast: Any) -> dict[tuple[int, int], int]:
    """{(weekday, hour): percent} from the published typical week."""
    week: dict[tuple[int, int], int] = {}
    for day in forecast or []:
        if day.get("dayOfWeek") not in WEEKDAYS:
            continue
        weekday = WEEKDAYS.index(day["dayOfWeek"])
        for hour in day.get("hourlyOccupancyPrediction") or []:
            percent = _percent(hour.get("occupancyRate"))
            if percent is not None:
                week[weekday, int(str(hour["localTime"])[:2])] = percent
    return week


def _forecast(week: dict[tuple[int, int], int], now: datetime, zone) -> list[dict[str, Any]]:
    """The next FORECAST_HOURS of the typical week; hours without a value are left out."""
    start = now.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    hours = []
    for offset in range(1, FORECAST_HOURS + 1):
        local = (start + timedelta(hours=offset)).astimezone(zone)
        percent = week.get((local.weekday(), local.hour))
        if percent is not None:
            hours.append({"time": local.isoformat(timespec="minutes"), "occupancy_percent": percent})
    return hours


def parse_facilities(
    raw: bytes, stations: set[str] | None, now: datetime, modified: datetime | None, zone
) -> dict[str, dict]:
    """Car facilities of the file in the shape of sources.py, plus occupancy,
    level and forecast; `stations` limits it to these ids. Without it, only
    facilities with an estimate or a typical week are returned. A malformed
    facility is skipped. Runs in the executor."""
    stale = modified is not None and now - modified > timedelta(minutes=STALE_PRAIL_MINUTES)
    facilities: dict[str, dict] = {}
    for feature in json.loads(raw)["features"]:
        try:
            props = feature["properties"]
            station_id = str(feature["id"])
            if props.get("parkingFacilityCategory") != "CAR":
                continue
            if stations is not None and station_id not in stations:
                continue
            occupancy = _percent(props.get("currentEstimatedOccupancy"))
            week = _typical_week(props.get("predictedForecastedOccupancy"))
            if stations is None and occupancy is None and not week:
                continue
            level = str(props.get("currentEstimatedOccupancyLevel") or "").lower()
            address = props.get("address") or {}
            town = " ".join(str(v) for v in (address.get("postalCode"), address.get("city")) if v)
            total = sum(
                c.get("total") or 0 for c in props.get("capacities") or [] if c.get("categoryType") == "STANDARD"
            )
            lat, lon = _point(feature.get("geometry"))
            if stale:
                occupancy, level = None, ""
            facilities[station_id] = {
                "id": station_id,
                "name": str(props["displayName"]).strip(),
                "free": None,
                "total": total or None,
                "status": STATUS_UNKNOWN if occupancy is None else STATUS_OPEN,
                "occupancy": occupancy,
                "level": level if level in LEVELS else STATUS_UNKNOWN,
                "forecast": _forecast(week, now, zone),
                "latitude": lat,
                "longitude": lon,
                "address": ", ".join(v for v in (address.get("addressLine"), town) if v) or None,
                "link": PRAIL_LINK,
                "last_update": modified.isoformat(timespec="seconds") if modified else None,
            }
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
    return facilities


async def async_fetch_prail(hass: HomeAssistant, stations: set[str] | None = None) -> dict[str, dict]:
    """Download the file and reduce it. Raises on network errors."""
    session = async_get_clientsession(hass)
    async with session.get(PRAIL_URL, timeout=FETCH_TIMEOUT_SECONDS) as resp:
        resp.raise_for_status()
        header = resp.headers.get("Last-Modified")
        raw = await resp.read()
    try:
        modified = parsedate_to_datetime(header) if header else None
    except (TypeError, ValueError):
        modified = None
    zone = await dt_util.async_get_time_zone(TIME_ZONE) or timezone.utc
    return await hass.async_add_executor_job(parse_facilities, raw, stations, dt_util.utcnow(), modified, zone)
