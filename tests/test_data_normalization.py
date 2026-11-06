
from datetime import datetime, timezone
from time import gmtime

from radar.services.date_parser import parse_feed_date
from radar.services.text_cleaner import clean_text


def test_html_entities():
    assert clean_text("Tom &amp; Jerry") == "Tom & Jerry"
    assert clean_text("&apos;ಕಾಥಲ್&apos;") == "'ಕಾಥಲ್'"


def test_whitespace_normalization():
    assert clean_text("  ಕನ್ನಡ \n ಸಿನಿಮಾ  ") == "ಕನ್ನಡ ಸಿನಿಮಾ"


def test_empty_text():
    assert clean_text(None) == ""
    assert clean_text("   ") == ""


def test_valid_rss_date():
    parsed = gmtime(1762473600)

    result = parse_feed_date(parsed)

    assert result == datetime.fromtimestamp(
        1762473600,
        tz=timezone.utc,
    )


def test_missing_date():
    assert parse_feed_date(None) is None
