"""Repair notice: a city feed unreachable or empty for three refreshes in a
row, withdrawn with the next good refresh."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swiss_parking.const import CITY_BERN, CONF_CITY, DOMAIN
from custom_components.swiss_parking.coordinator import SwissParkingCoordinator

FETCH = "custom_components.swiss_parking.coordinator.async_fetch_city"
GARAGES = {"p01": {"id": "p01", "name": "Bahnhof", "free": 12, "total": 100, "status": "open"}}


def _issue(hass, entry):
    return ir.async_get(hass).async_get_issue(DOMAIN, f"unreachable_{entry.entry_id}")


async def test_feed_unreachable_or_empty(hass: HomeAssistant, enable_custom_integrations) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=CITY_BERN, title="Bern", data={CONF_CITY: CITY_BERN})
    entry.add_to_hass(hass)
    coordinator = SwissParkingCoordinator(hass, entry)
    with patch(FETCH, side_effect=OSError("down")):
        await coordinator.async_refresh()
        await coordinator.async_refresh()
    assert _issue(hass, entry) is None
    with patch(FETCH, return_value={}):  # an empty feed counts as a failure as well
        await coordinator.async_refresh()
    issue = _issue(hass, entry)
    assert issue is not None and issue.translation_placeholders == {"city": "Bern"}
    with patch(FETCH, return_value=GARAGES):
        await coordinator.async_refresh()
    assert coordinator.data == GARAGES
    assert _issue(hass, entry) is None
