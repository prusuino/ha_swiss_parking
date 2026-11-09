"""Shared device info: one device per configured city."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CITIES, CONF_CITY, DOMAIN, VERSION
from .localization import t


def device_info(hass: HomeAssistant, entry: ConfigEntry) -> DeviceInfo:
    city = entry.data[CONF_CITY]
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        sw_version=VERSION,
        name=t("device_name", hass, city=CITIES[city]["name"]),
        manufacturer="Swiss Parking",
        model=CITIES[city]["name"],
        configuration_url="https://github.com/prusuino/ha_swiss_parking",
    )
