"""Config flow: pick one of the supported cities. One entry per city,
repeatable for the others."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CITIES, CONF_CITY, DOMAIN
from .localization import t
from .sources import async_fetch_city


class SwissParkingConfigFlow(ConfigFlow, domain=DOMAIN):
    """City picker with a live probe of the selected feed."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            city = user_input[CONF_CITY]
            await self.async_set_unique_id(city)
            self._abort_if_unique_id_configured()

            try:
                garages = await async_fetch_city(self.hass, city)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                if not garages:
                    errors["base"] = "no_garages"
                else:
                    return self.async_create_entry(
                        title=t("device_name", self.hass, city=CITIES[city]["name"]),
                        data={CONF_CITY: city},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_CITY): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=key, label=info["name"])
                            for key, info in CITIES.items()
                        ],
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
