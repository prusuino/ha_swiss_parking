"""Swiss Parking – Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SwissParkingCoordinator

type SwissParkingConfigEntry = ConfigEntry[SwissParkingCoordinator]

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "geo_location"]


async def async_setup_entry(hass: HomeAssistant, entry: SwissParkingConfigEntry) -> bool:
    coordinator = SwissParkingCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SwissParkingConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
