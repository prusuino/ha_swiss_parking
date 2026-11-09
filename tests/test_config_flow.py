"""Config flow tests: city pick with a live probe, an unreachable or empty
feed and one entry per city. The feed is faked."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.swiss_parking.const import CITY_BERN, CITY_ZURICH, CONF_CITY, DOMAIN

FLOW = "custom_components.swiss_parking.config_flow."
GARAGES = {"accu": {"id": "accu", "name": "Accu", "free": 164, "total": None, "status": "open"}}


async def test_city_setup(hass: HomeAssistant, enable_custom_integrations) -> None:
    with patch(FLOW + "async_fetch_city", return_value=GARAGES) as probe:
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: CITY_ZURICH})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_CITY: CITY_ZURICH}
    assert "Zürich" in result["title"]
    assert result["result"].unique_id == CITY_ZURICH
    probe.assert_awaited_once()


async def test_unreachable_and_empty_feed(hass: HomeAssistant, enable_custom_integrations) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with patch(FLOW + "async_fetch_city", side_effect=OSError("down")):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: CITY_BERN})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    with patch(FLOW + "async_fetch_city", return_value={}):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: CITY_BERN})
    assert result["errors"] == {"base": "no_garages"}


async def test_one_entry_per_city(hass: HomeAssistant, enable_custom_integrations) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=CITY_ZURICH, title="Zürich", data={CONF_CITY: CITY_ZURICH}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_CITY: CITY_ZURICH})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
