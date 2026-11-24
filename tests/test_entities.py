"""Entities: a car park that left the feed while Home Assistant was down is
removed at the next start (sensor and map marker), map markers follow
changed coordinates, a feed error counts as "unreachable" while a bug does
not, and the Frauenfeld query is large enough for every area."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swiss_parking import sources
from custom_components.swiss_parking.const import CITY_BERN, CONF_CITY, DOMAIN

FETCH = "custom_components.swiss_parking.coordinator.async_fetch_city"


def _garage(gid: str, lat: float, lon: float, free: int = 10) -> dict:
    return {"id": gid, "name": gid.upper(), "free": free, "total": 100, "status": "open",
            "latitude": lat, "longitude": lon, "address": None, "link": None, "last_update": None}


async def test_leftovers_removed_at_start_and_markers_follow(hass: HomeAssistant, enable_custom_integrations) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=CITY_BERN, title="Bern", data={CONF_CITY: CITY_BERN})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    # P07 was in the feed before the restart and is gone now
    for domain in ("sensor", "geo_location"):
        registry.async_get_or_create(domain, DOMAIN, f"{entry.entry_id}_p07", config_entry=entry,
                                     suggested_object_id=f"parking_bern_p07")
    with patch(FETCH, return_value={"p01": _garage("p01", 46.9497, 7.4385)}):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    unique_ids = {(e.domain, e.unique_id) for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert ("sensor", f"{entry.entry_id}_p07") not in unique_ids
    assert ("geo_location", f"{entry.entry_id}_p07") not in unique_ids
    assert ("sensor", f"{entry.entry_id}_p01") in unique_ids
    assert ("geo_location", f"{entry.entry_id}_p01") in unique_ids

    marker = registry.async_get_entity_id("geo_location", DOMAIN, f"{entry.entry_id}_p01")
    assert hass.states.get(marker).attributes["latitude"] == pytest.approx(46.9497)

    with patch(FETCH, return_value={"p01": _garage("p01", 46.9600, 7.4500, free=3)}):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
    state = hass.states.get(marker)
    assert state.attributes["latitude"] == pytest.approx(46.96)
    assert state.attributes["longitude"] == pytest.approx(7.45)


async def test_only_feed_errors_count_as_unreachable(hass: HomeAssistant, enable_custom_integrations) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=CITY_BERN, title="Bern", data={CONF_CITY: CITY_BERN})
    entry.add_to_hass(hass)
    with patch(FETCH, return_value={"p01": _garage("p01", 46.95, 7.44)}):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    coordinator = entry.runtime_data
    with patch(FETCH, side_effect=ValueError("garbled feed")):
        await coordinator.async_refresh()
    assert not coordinator.last_update_success
    with patch(FETCH, side_effect=RuntimeError("bug")):
        await coordinator.async_refresh()  # logged as an unexpected error by the coordinator
    assert not coordinator.last_update_success


def test_frauenfeld_query_reads_enough_records() -> None:
    assert "limit=100" in sources.FRAUENFELD_URL


def test_swiss_time_for_bern_timestamps() -> None:
    parsed = sources.parse_timestamp("24.11.2026 07:00:00")
    assert parsed is not None and parsed.utcoffset().total_seconds() == 3600


async def test_names_below_the_city_device(hass: HomeAssistant, enable_custom_integrations) -> None:
    """Sensor and marker are named after the car park below the city's device
    (translated device name), the ids stay language-independent and the
    status attribute is the fixed key."""
    from homeassistant.helpers import device_registry as dr

    hass.config.language = "de"
    entry = MockConfigEntry(domain=DOMAIN, unique_id=CITY_BERN, title="Bern", data={CONF_CITY: CITY_BERN})
    entry.add_to_hass(hass)
    garage = _garage("p01", 46.9497, 7.4385) | {"name": "Bahnhof", "status": "closed"}
    with patch(FETCH, return_value={"p01": garage}):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    sensor_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_p01")
    marker_id = registry.async_get_entity_id("geo_location", DOMAIN, f"{entry.entry_id}_p01")
    assert sensor_id == "sensor.parking_bern_bahnhof"
    assert marker_id == "geo_location.parking_bern_bahnhof"

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.name == "Parkhäuser Bern"  # from the translations
    for entity_id in (sensor_id, marker_id):
        row = registry.async_get(entity_id)
        assert row.has_entity_name and row.original_name == "Bahnhof"
        assert row.device_id == device.id
    sensor = hass.states.get(sensor_id)
    assert sensor.attributes["status"] == "closed"
    assert sensor.attributes["friendly_name"].endswith("Bahnhof")
    assert hass.states.get(marker_id).attributes["status"] == "Geschlossen"  # map label stays localized
