"""DataUpdateCoordinator: polls one city's parking-guidance feed."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CITIES,
    CITY_PRAIL,
    CONF_CITY,
    CONF_STATIONS,
    DOMAIN,
    PRAIL_UPDATE_INTERVAL_MINUTES,
    UPDATE_INTERVAL_MINUTES,
)
from .issues import IssueReporter
from .prail import async_fetch_prail
from .sources import FETCH_ERRORS, async_fetch_city

_LOGGER = logging.getLogger(__name__)


class SwissParkingCoordinator(DataUpdateCoordinator[dict]):
    """Fetches the garages of the configured city."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.city: str = entry.data[CONF_CITY]
        self.is_prail = self.city == CITY_PRAIL
        self.stations: set[str] = set(entry.options.get(CONF_STATIONS, []))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=PRAIL_UPDATE_INTERVAL_MINUTES if self.is_prail else UPDATE_INTERVAL_MINUTES
            ),
        )
        self.issues = IssueReporter(hass, entry.entry_id)

    async def _async_update_data(self) -> dict:
        city = CITIES[self.city]["name"]
        try:
            if self.is_prail:
                garages = await async_fetch_prail(self.hass, self.stations)
            else:
                garages = await async_fetch_city(self.hass, self.city)
        except FETCH_ERRORS as err:
            self.issues.failure("unreachable", {"city": city})
            raise UpdateFailed(f"Parking feed for {self.city} unreachable: {err}") from err
        if not garages:
            self.issues.failure("unreachable", {"city": city})
            raise UpdateFailed(f"Parking feed for {self.city} returned no garages")
        self.issues.clear("unreachable")
        return garages
