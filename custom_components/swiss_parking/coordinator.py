"""DataUpdateCoordinator: polls one city's parking-guidance feed."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CITIES, CONF_CITY, DOMAIN, UPDATE_INTERVAL_MINUTES
from .issues import IssueReporter
from .sources import async_fetch_city

_LOGGER = logging.getLogger(__name__)


class SwissParkingCoordinator(DataUpdateCoordinator[dict]):
    """Fetches the garages of the configured city."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.city: str = entry.data[CONF_CITY]
        self.issues = IssueReporter(hass, entry.entry_id)

    async def _async_update_data(self) -> dict:
        city = CITIES[self.city]["name"]
        try:
            garages = await async_fetch_city(self.hass, self.city)
        except Exception as err:
            self.issues.failure("unreachable", {"city": city})
            raise UpdateFailed(f"Parking feed for {self.city} unreachable: {err}") from err
        if not garages:
            self.issues.failure("unreachable", {"city": city})
            raise UpdateFailed(f"Parking feed for {self.city} returned no garages")
        self.issues.clear("unreachable")
        return garages
