"""Runtime localization (DE/EN/FR/IT) following the Home Assistant language.

Same pattern as the other integrations of this author: STRINGS maps a key to
per-language texts, t() resolves against hass.config.language with English
as the fallback. Used for entity/device names and status words — garage
names from the sources are shown as-is.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import STATUS_CLOSED, STATUS_OPEN, STATUS_UNKNOWN

STRINGS = {
    "device_name": {
        "de": "Parkhäuser {city}",
        "en": "Car Parks {city}",
        "fr": "Parkings {city}",
        "it": "Parcheggi {city}",
    },
    "free_spaces_suffix": {
        "de": "Freie Plätze",
        "en": "Free spaces",
        "fr": "Places libres",
        "it": "Posti liberi",
    },
    "status_open": {
        "de": "Offen",
        "en": "Open",
        "fr": "Ouvert",
        "it": "Aperto",
    },
    "status_closed": {
        "de": "Geschlossen",
        "en": "Closed",
        "fr": "Fermé",
        "it": "Chiuso",
    },
    "status_unknown": {
        "de": "Unbekannt",
        "en": "Unknown",
        "fr": "Inconnu",
        "it": "Sconosciuto",
    },
    "map_label_free": {
        "de": "{free} frei",
        "en": "{free} free",
        "fr": "{free} libres",
        "it": "{free} liberi",
    },
    "map_label_closed": {
        "de": "Geschlossen",
        "en": "Closed",
        "fr": "Fermé",
        "it": "Chiuso",
    },
    "garage_entity_prefix": {
        "de": "Parkhaus",
        "en": "Car park",
        "fr": "Parking",
        "it": "Parcheggio",
    },
}

STATUS_KEYS = {
    STATUS_OPEN: "status_open",
    STATUS_CLOSED: "status_closed",
    STATUS_UNKNOWN: "status_unknown",
}


def _lang(hass: HomeAssistant) -> str:
    language = (hass.config.language or "en").split("-")[0]
    return language if language in ("de", "en", "fr", "it") else "en"


def t(key: str, hass: HomeAssistant, **kwargs) -> str:
    texts = STRINGS.get(key, {})
    text = texts.get(_lang(hass)) or texts.get("en") or key
    return text.format(**kwargs) if kwargs else text


def localized_status(status: str | None, hass: HomeAssistant) -> str:
    return t(STATUS_KEYS.get(status or STATUS_UNKNOWN, "status_unknown"), hass)
