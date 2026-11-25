"""SBB P+Rail: the reduction of the station file, the setup with a station
step, the options and the entities. The file is faked."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swiss_parking.const import CITY_BERN, CITY_PRAIL, CONF_CITY, CONF_STATIONS, DOMAIN
from custom_components.swiss_parking.prail import parse_facilities

ZONE = ZoneInfo("Europe/Zurich")
NOW = datetime(2026, 11, 25, 21, 30, tzinfo=timezone.utc)  # Wednesday 22:30 local time


def _facility(fid, name, occupancy, level=None, category="CAR", forecast=None):
    return {
        "id": fid,
        "geometry": {"type": "GeometryCollection", "geometries": [
            {"type": "Polygon", "coordinates": [[[8.0, 46.0]]]}, {"type": "Point", "coordinates": [8.5, 46.5]}]},
        "properties": {
            "displayName": name, "parkingFacilityCategory": category,
            "currentEstimatedOccupancy": occupancy, "currentEstimatedOccupancyLevel": level,
            "predictedForecastedOccupancy": forecast,
            "capacities": [{"categoryType": "STANDARD", "total": 63}, {"categoryType": "DISABLED_PARKING_SPACE", "total": 2}],
            "address": {"addressLine": "Bahnhofplatz 1", "postalCode": "1096", "city": "Cully"},
        },
    }


WEEK = [{"dayOfWeek": "THURSDAY", "hourlyOccupancyPrediction": [
    {"localTime": "07:00", "occupancyRate": 0.82}, {"localTime": "08:00", "occupancyRate": None}]}]
RAW = json.dumps({"features": [
    _facility("a", "Cully", 0.6244, "MEDIUM", forecast=WEEK),
    _facility("b", "Nowhere", None),
    _facility("c", "Bikes", 0.5, "LOW", category="BIKE"),
    _facility("d", "Full", 1.07, "HIGH"),
    {"id": "e", "properties": {"parkingFacilityCategory": "CAR", "currentEstimatedOccupancy": 0.1}},  # no name
]}).encode()


def test_file_is_reduced():
    stations = parse_facilities(RAW, None, NOW, NOW, ZONE)
    assert set(stations) == {"a", "d"}  # no bikes, nothing without an estimate, nothing malformed
    cully = stations["a"]
    assert (cully["occupancy"], cully["level"], cully["total"], cully["free"]) == (62, "medium", 63, None)
    assert (cully["latitude"], cully["longitude"]) == (46.5, 8.5)
    assert cully["address"] == "Bahnhofplatz 1, 1096 Cully"
    assert cully["forecast"] == [{"time": "2026-11-26T07:00+01:00", "occupancy_percent": 82}]
    assert stations["d"]["occupancy"] == 100


def test_chosen_station_stays_without_an_estimate():
    stations = parse_facilities(RAW, {"b"}, NOW, NOW, ZONE)
    assert set(stations) == {"b"}
    assert stations["b"]["occupancy"] is None and stations["b"]["level"] == "unknown"


def test_old_file_is_not_shown_as_live():
    old = parse_facilities(RAW, {"a"}, NOW, NOW - timedelta(hours=4), ZONE)["a"]
    assert old["occupancy"] is None and old["level"] == "unknown" and old["total"] == 63


async def test_setup_options_and_entities(hass: HomeAssistant, enable_custom_integrations) -> None:
    async def fetch(_hass, stations=None):
        return parse_facilities(RAW, stations, NOW, NOW, ZONE)

    base = "custom_components.swiss_parking."
    with patch(base + "config_flow.async_fetch_prail", fetch), patch(base + "coordinator.async_fetch_prail", fetch):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: CITY_PRAIL})
        assert result["step_id"] == "stations"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STATIONS: []})
        assert result["errors"] == {"base": "no_stations"}
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_STATIONS: ["a"]})
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
        entry = result["result"]
        assert entry.data == {CONF_CITY: CITY_PRAIL} and entry.options == {CONF_STATIONS: ["a"]}
        assert entry.supports_options

        state = hass.states.get("sensor.parking_sbb_p_rail_cully")
        assert state.state == "62" and state.attributes["unit_of_measurement"] == "%"
        assert state.attributes["level"] == "medium" and "free" not in state.attributes
        assert hass.states.get("geo_location.parking_sbb_p_rail_cully").attributes["status"] == "≈ 62 %"

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["step_id"] == "init"
        result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_STATIONS: ["d"]})
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
        assert hass.states.get("sensor.parking_sbb_p_rail_full").state == "100"
        assert hass.states.get("sensor.parking_sbb_p_rail_cully") is None


async def test_file_unreachable_in_the_flow(hass: HomeAssistant, enable_custom_integrations) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch("custom_components.swiss_parking.config_flow.async_fetch_prail", side_effect=OSError("down")):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: CITY_PRAIL})
    assert result["step_id"] == "user" and result["errors"] == {"base": "cannot_connect"}


def test_a_city_has_no_options() -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=CITY_BERN, data={CONF_CITY: CITY_BERN})
    assert not entry.supports_options
