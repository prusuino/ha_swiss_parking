"""Removal of entities whose garage has left the city's feed."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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


@callback
def async_remove_orphans(hass: HomeAssistant, entry: ConfigEntry, domain: str, garage_ids) -> None:
    """At setup: drop the registry rows of this entry's `domain` entities whose
    car park is no longer in the feed. The in-memory diffing above only sees
    car parks that leave while Home Assistant runs; one that left while it was
    down would otherwise stay behind as a "restored", unavailable entity."""
    keep = {f"{entry.entry_id}_{garage_id}" for garage_id in garage_ids}
    registry = er.async_get(hass)
    for reg in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg.domain == domain and reg.unique_id not in keep:
            registry.async_remove(reg.entity_id)
