
from calendar import timegm
from datetime import datetime, timezone
from time import struct_time


def parse_feed_date(
    published_parsed: struct_time | None,
) -> datetime | None:
    """Convert a parsed RSS/Atom timestamp to UTC."""

    if published_parsed is None:
        return None

    try:
        timestamp = timegm(published_parsed)
        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )
    except (OverflowError, ValueError, TypeError):
        return None
