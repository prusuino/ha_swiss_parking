"""Swiss Parking – Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SwissParkingCoordinator
from .issues import async_clear_entry_issues

type SwissParkingConfigEntry = ConfigEntry[SwissParkingCoordinator]

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "geo_location"]


async def async_setup_entry(hass: HomeAssistant, entry: SwissParkingConfigEntry) -> bool:
    coordinator = SwissParkingCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload(hass: HomeAssistant, entry: SwissParkingConfigEntry) -> None:
    """Other P+Rail stations were picked in the options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: SwissParkingConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_clear_entry_issues(hass, entry.entry_id)
    return unloaded
