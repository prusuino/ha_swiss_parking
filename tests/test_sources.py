"""The source helpers: timestamp parsing in the formats the cities use, the
stale-data withdrawal and the Zürich RSS adapter against a faked download."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.swiss_parking.const import STATUS_CLOSED, STATUS_OPEN, STATUS_UNKNOWN
from custom_components.swiss_parking.sources import _int_or_none, fetch_zurich, mark_stale, parse_timestamp

NOW = datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)


def test_timestamps_of_every_city_format():
    assert parse_timestamp("2026-11-09T09:30:00+01:00") == datetime(2026, 11, 9, 9, 30, tzinfo=timezone(timedelta(hours=1)))
    assert parse_timestamp("2026-11-09T08:30:00+00") == datetime(2026, 11, 9, 8, 30, tzinfo=timezone.utc)  # Winterthur
    bern = parse_timestamp("09.11.2026 10:30:00")  # Swiss local time
    assert bern.tzinfo is not None and bern.hour == 10
    assert bern.utcoffset() == timedelta(hours=1)
    rss = parse_timestamp("Mon, 09 Nov 2026 09:30:00 +0100")  # Zürich
    assert rss == datetime(2026, 11, 9, 9, 30, tzinfo=timezone(timedelta(hours=1)))
    assert parse_timestamp("") is None and parse_timestamp(None) is None
    assert parse_timestamp("gestern") is None
    assert _int_or_none(" 164 ") == 164 and _int_or_none("n/a") is None


def _garage(gid, free, stamp):
    return {"id": gid, "name": gid, "free": free, "total": 200, "status": STATUS_OPEN, "last_update": stamp}


def test_stale_feed_withdraws_every_garage():
    old = (NOW - timedelta(hours=2)).isoformat()
    garages = {"a": _garage("a", 10, old), "b": _garage("b", 20, old)}
    result = mark_stale(garages, NOW)
    assert all(g["free"] is None and g["status"] == STATUS_UNKNOWN for g in result.values())
    assert result["a"]["total"] == 200 and result["a"]["last_update"] == old  # the rest is kept


def test_quiet_feed_without_feed_cutoff_keeps_recent_garages():
    fresh = (NOW - timedelta(minutes=90)).isoformat()
    ancient = (NOW - timedelta(hours=30)).isoformat()
    garages = {"a": _garage("a", 10, fresh), "b": _garage("b", 20, ancient), "c": _garage("c", 5, None)}
    result = mark_stale(garages, NOW, feed_cutoff=False)
    assert result["a"]["free"] == 10 and result["a"]["status"] == STATUS_OPEN
    assert result["b"]["free"] is None and result["b"]["status"] == STATUS_UNKNOWN
    assert result["c"]["free"] == 5  # no stamp at all: left alone


def test_no_stamp_anywhere_leaves_the_feed_alone():
    garages = {"a": _garage("a", 10, None)}
    assert mark_stale(garages, NOW) == garages


RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>PLS</title>
<item><title>Parkhaus Accu / Otto-Schütz-Weg</title><description>open /  164</description>
<link>https://www.pls-zh.ch/parkhaus/accu?pid=accu</link><pubDate>Mon, 09 Nov 2026 09:30:00 +0100</pubDate></item>
<item><title>Parkhaus Urania / Uraniastrasse 3</title><description>closed /  0</description>
<link>https://www.pls-zh.ch/parkhaus/urania</link><pubDate>Mon, 09 Nov 2026 09:30:00 +0100</pubDate></item>
<item><title>Parkhaus Nowhere / </title><description>unknown / ?</description></item>
<item><title></title><description>open / 5</description></item>
</channel></rss>"""


@pytest.mark.asyncio
async def test_zurich_adapter():
    with patch("custom_components.swiss_parking.sources._fetch_text", AsyncMock(return_value=RSS)):
        garages = await fetch_zurich(None)
    assert set(garages) == {"accu", "urania", "nowhere"}  # the item without a title is skipped
    accu = garages["accu"]
    assert accu["name"] == "Accu" and accu["address"] == "Otto-Schütz-Weg"
    assert accu["free"] == 164 and accu["status"] == STATUS_OPEN
    assert accu["last_update"] == "2026-11-09T09:30:00+01:00"
    assert garages["urania"]["status"] == STATUS_CLOSED and garages["urania"]["free"] == 0
    assert garages["urania"]["id"] == "urania"  # no pid in the link: the slug of the name
    assert garages["nowhere"]["status"] == STATUS_UNKNOWN and garages["nowhere"]["free"] is None
    assert garages["nowhere"]["address"] is None and garages["nowhere"]["last_update"] is None
