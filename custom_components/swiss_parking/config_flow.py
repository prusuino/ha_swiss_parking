"""Config flow: pick one of the supported cities. One entry per city,
repeatable for the others. SBB P+Rail is offered next to the cities and asks
for the stations in a second step; they can be changed in its options."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CITIES, CITY_PRAIL, CONF_CITY, CONF_STATIONS, DOMAIN
from .localization import t
from .prail import async_fetch_prail
from .sources import FETCH_ERRORS, async_fetch_city

_LOGGER = logging.getLogger(__name__)


async def _async_probe_stations(hass: HomeAssistant) -> tuple[dict[str, dict], str | None]:
    """The P+Rail stations on offer and an error key if there are none."""
    try:
        stations = await async_fetch_prail(hass)
    except FETCH_ERRORS:
        return {}, "cannot_connect"
    except Exception:  # noqa: BLE001 - anything else is a bug, shown as such
        _LOGGER.exception("Unexpected error while loading the P+Rail stations")
        return {}, "unknown"
    return stations, None if stations else "no_garages"


def _stations_schema(stations: dict[str, dict], default: list[str]) -> vol.Schema:
    options = [
        SelectOptionDict(value=station_id, label=station["name"])
        for station_id, station in sorted(stations.items(), key=lambda item: item[1]["name"].casefold())
    ]
    return vol.Schema(
        {
            vol.Required(CONF_STATIONS, default=default): SelectSelector(
                SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.DROPDOWN)
            ),
        }
    )


class SwissParkingConfigFlow(ConfigFlow, domain=DOMAIN):
    """City picker with a live probe of the selected feed."""

    VERSION = 1

    def __init__(self) -> None:
        self._stations: dict[str, dict] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PrailOptionsFlow()

    @classmethod
    @callback
    def async_supports_options_flow(cls, config_entry: ConfigEntry) -> bool:
        """Only the P+Rail entry has something to choose."""
        return config_entry.data.get(CONF_CITY) == CITY_PRAIL

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            city = user_input[CONF_CITY]
            await self.async_set_unique_id(city)
            self._abort_if_unique_id_configured()
            if city == CITY_PRAIL:
                self._stations, error = await _async_probe_stations(self.hass)
                if error is None:
                    return await self.async_step_stations()
                errors["base"] = error
                return self._show_cities(errors)

            try:
                garages = await async_fetch_city(self.hass, city)
            except FETCH_ERRORS:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - anything else is a bug, shown as such
                _LOGGER.exception("Unexpected error while probing the %s feed", city)
                errors["base"] = "unknown"
            else:
                if not garages:
                    errors["base"] = "no_garages"
                else:
                    return self.async_create_entry(
                        title=t("entry_title", self.hass, city=CITIES[city]["name"]),
                        data={CONF_CITY: city},
                    )

        return self._show_cities(errors)

    async def async_step_stations(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_STATIONS]:
                return self.async_create_entry(
                    title=CITIES[CITY_PRAIL]["name"],
                    data={CONF_CITY: CITY_PRAIL},
                    options={CONF_STATIONS: user_input[CONF_STATIONS]},
                )
            errors["base"] = "no_stations"
        return self.async_show_form(
            step_id="stations", data_schema=_stations_schema(self._stations, []), errors=errors
        )

    def _show_cities(self, errors: dict[str, str]) -> FlowResult:
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


class PrailOptionsFlow(OptionsFlow):
    """Pick other P+Rail stations."""

    def __init__(self) -> None:
        self._stations: dict[str, dict] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_STATIONS]:
                return self.async_create_entry(data={CONF_STATIONS: user_input[CONF_STATIONS]})
            errors["base"] = "no_stations"
        elif not self._stations:
            self._stations, error = await _async_probe_stations(self.hass)
            if error is not None:
                return self.async_abort(reason=error)
        current = [s for s in self.config_entry.options.get(CONF_STATIONS, []) if s in self._stations]
        return self.async_show_form(
            step_id="init", data_schema=_stations_schema(self._stations, current), errors=errors
        )
