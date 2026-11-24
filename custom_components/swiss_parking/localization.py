"""Runtime texts (DE/EN/FR/IT) following the Home Assistant language, for
the two places Home Assistant's translations cannot reach: the map label,
which carries the live number of free spaces ("158 frei"), and the title of
a new config entry. Entity and device names and the status attribute come
from the translation files.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant

STRINGS = {
    "entry_title": {
        "de": "Parkhäuser {city}",
        "en": "Car parks {city}",
        "fr": "Parkings {city}",
        "it": "Parcheggi {city}",
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
}


def _lang(hass: HomeAssistant) -> str:
    language = (hass.config.language or "en").split("-")[0]
    return language if language in ("de", "en", "fr", "it") else "en"


def t(key: str, hass: HomeAssistant, **kwargs) -> str:
    texts = STRINGS.get(key, {})
    text = texts.get(_lang(hass)) or texts.get("en") or key
    return text.format(**kwargs) if kwargs else text
