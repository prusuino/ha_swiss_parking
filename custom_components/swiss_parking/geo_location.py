"""Map markers: one per garage with known coordinates, labeled with the
current number of free spaces (refreshed in place on every update).

Zurich's feed has no coordinates, so Zurich entries create no markers —
the sensors carry the data regardless. Hidden from Home Assistant's
auto-generated default dashboard map, same as the charging-stations
integration."""
from __future__ import annotations

import logging

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from homeassistant.util.location import distance

from .const import CITIES, DOMAIN, STATUS_CLOSED
from .coordinator import SwissParkingCoordinator
from .localization import t

_LOGGER = logging.getLogger(__name__)
SOURCE = "swiss_parking"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SwissParkingCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: dict[str, GarageEvent] = {}
    attribution = CITIES[coordinator.city]["attribution"]

    @callback
    def _sync_entities() -> None:
        # Runs on every coordinator notification — including a failed
        # refresh, which keeps the previous data but flips
        # last_update_success. The in-place update below then writes state
        # for every surviving marker, which is what publishes the
        # availability change (see GarageEvent.available).
        garages = {
            gid: g
            for gid, g in (coordinator.data or {}).items()
            if g.get("latitude") is not None and g.get("longitude") is not None
        }

        new_entities = []
        for garage_id, garage in garages.items():
            existing = known.get(garage_id)
            if existing is None:
                known[garage_id] = GarageEvent(
                    hass, coordinator, entry, garage_id, garage, attribution
                )
                new_entities.append(known[garage_id])
            else:
                existing.update_garage(garage)
        if new_entities:
            async_add_entities(new_entities)

        for garage_id in [g for g in known if g not in garages]:
            entity = known.pop(garage_id)
            hass.async_create_task(entity.async_remove(force_remove=True))

    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))
    _sync_entities()


class GarageEvent(GeolocationEvent):
    """One garage on the map; label shows live free spaces. Lifecycle
    (appearing/disappearing) is managed by the sync function above; label
    and attributes are refreshed in place on every coordinator update, and
    availability follows the coordinator's last refresh."""

    _attr_should_poll = False
    _attr_source = SOURCE
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_has_entity_name = False
    # Hidden from Home Assistant's auto-generated default dashboard map (which
    # otherwise draws every geo_location entity in the system) — still shown
    # on a Map card that references them by source, which does not go through
    # the visible-by-default list. This applies to entities registered for the
    # first time; whether an existing entity stays hidden is the user's
    # decision alone and is never rewritten from here.
    _attr_entity_registry_visible_default = False

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: SwissParkingCoordinator,
        entry: ConfigEntry,
        garage_id: str,
        garage: dict,
        attribution: str,
    ) -> None:
        self._hass_ref = hass
        self._coordinator = coordinator
        self._garage = garage
        self._attr_attribution = attribution
        # The config entry id is part of the unique id, so two entries whose
        # feeds list the same garage each keep their own marker instead of
        # fighting over one registry entry.
        self._attr_unique_id = f"{entry.entry_id}_{garage_id}"
        prefix = t("garage_entity_prefix", hass)
        self._attr_name = f"{prefix} – {garage.get('name') or garage_id}"
        self._attr_latitude = garage.get("latitude")
        self._attr_longitude = garage.get("longitude")
        self._attr_distance = self._distance_from_home(hass, garage)

    @staticmethod
    def _distance_from_home(hass: HomeAssistant, garage: dict) -> float | None:
        meters = distance(
            hass.config.latitude,
            hass.config.longitude,
            garage.get("latitude"),
            garage.get("longitude"),
        )
        return round(meters / 1000, 2) if meters is not None else None

    @callback
    def update_garage(self, garage: dict) -> None:
        """Refresh label/attributes in place on a coordinator update, so the
        map label stays current without recreating the entity."""
        self._garage = garage
        if self.hass:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Like the sensors: while the city's feed is unreachable the marker
        is unavailable instead of showing its last known label indefinitely.
        Not a CoordinatorEntity (the lifecycle is managed by the sync
        function), so this reads the coordinator directly; the sync function
        writes state after every refresh, failed ones included, so a flip
        reaches the state machine."""
        return self._coordinator.last_update_success

    def _label(self) -> str:
        garage = self._garage
        if garage.get("status") == STATUS_CLOSED:
            return t("map_label_closed", self._hass_ref)
        free = garage.get("free")
        if free is None:
            return "?"
        return t("map_label_free", self._hass_ref, free=free)

    @property
    def icon(self):
        garage = self._garage
        if garage.get("status") == STATUS_CLOSED:
            return "mdi:garage-lock"
        free = garage.get("free")
        if free is not None and free == 0:
            return "mdi:garage-variant"
        return "mdi:parking"

    @property
    def extra_state_attributes(self):
        garage = self._garage
        return {
            "status": self._label(),
            "free": garage.get("free"),
            "total": garage.get("total"),
            "address": garage.get("address"),
            "link": garage.get("link"),
            "last_update": garage.get("last_update"),
        }
