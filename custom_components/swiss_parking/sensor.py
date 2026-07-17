"""Sensors: one free-spaces sensor per garage of the configured city.

Garages can appear/disappear in the source feeds, so the entity list is
diffed on every coordinator update (same pattern as the connector sensors
of the charging-stations integration)."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CITIES, DOMAIN, STATUS_CLOSED
from .coordinator import SwissParkingCoordinator
from .device import device_info
from .localization import localized_status, t

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SwissParkingCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: dict[str, GarageFreeSpacesSensor] = {}
    city_slug = slugify(CITIES[coordinator.city]["name"])

    @callback
    def _sync_entities() -> None:
        garages = coordinator.data or {}

        new_entities = []
        for garage_id, garage in garages.items():
            if garage_id not in known:
                known[garage_id] = GarageFreeSpacesSensor(hass, coordinator, entry, garage_id, city_slug)
                new_entities.append(known[garage_id])
        if new_entities:
            async_add_entities(new_entities)

        for garage_id in [g for g in known if g not in garages]:
            entity = known.pop(garage_id)
            hass.async_create_task(entity.async_remove(force_remove=True))

    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))
    _sync_entities()


class GarageFreeSpacesSensor(CoordinatorEntity[SwissParkingCoordinator], SensorEntity):
    """Free spaces of one garage; everything else as attributes."""

    _attr_has_entity_name = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: SwissParkingCoordinator,
        entry: ConfigEntry,
        garage_id: str,
        city_slug: str,
    ) -> None:
        super().__init__(coordinator)
        self._hass_ref = hass
        self._garage_id = garage_id
        garage = (coordinator.data or {}).get(garage_id, {})
        self._attr_name = garage.get("name") or garage_id
        self._attr_unique_id = f"{entry.entry_id}_{garage_id}"
        self._attr_device_info = device_info(hass, entry)
        self._attr_attribution = CITIES[coordinator.city]["attribution"]
        self.entity_id = f"sensor.parking_{city_slug}_{slugify(self._attr_name)}"

    def _garage(self) -> dict:
        return (self.coordinator.data or {}).get(self._garage_id) or {}

    @property
    def native_value(self):
        return self._garage().get("free")

    @property
    def icon(self):
        garage = self._garage()
        if garage.get("status") == STATUS_CLOSED:
            return "mdi:garage-lock"
        free = garage.get("free")
        if free is not None and free == 0:
            return "mdi:garage-variant"
        return "mdi:parking"

    @property
    def extra_state_attributes(self):
        garage = self._garage()
        total = garage.get("total")
        free = garage.get("free")
        occupancy = None
        if total and free is not None and total > 0:
            occupancy = round((total - free) * 100 / total)
        return {
            "status": localized_status(garage.get("status"), self._hass_ref),
            "total": total,
            "occupancy_percent": occupancy,
            "address": garage.get("address"),
            "link": garage.get("link"),
            "latitude": garage.get("latitude"),
            "longitude": garage.get("longitude"),
            "last_update": garage.get("last_update"),
        }
