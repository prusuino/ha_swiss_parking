"""Removal of entities whose garage has left the city's feed."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity


async def async_remove_entity(hass: HomeAssistant, entity: Entity) -> None:
    """Take an entity out of the state machine and out of the entity registry.

    async_remove alone leaves the registry row behind, and a row without a
    live entity comes back after a restart as a "restored", permanently
    unavailable entity — one more for every garage a feed drops, which
    Frauenfeld's history query and Bern's varying list do regularly. Only the
    registry row goes: when the garage returns under its unchanged unique id,
    Home Assistant restores its previous entity id (if still free) and its
    customizations — name, icon, area, labels, hidden/disabled state — from
    the deleted entities it keeps for a config entry; older cores create it
    afresh."""
    entity_id = entity.entity_id
    await entity.async_remove(force_remove=True)
    registry = er.async_get(hass)
    if entity_id and registry.async_get(entity_id) is not None:
        registry.async_remove(entity_id)
