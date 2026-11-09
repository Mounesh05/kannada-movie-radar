
from datetime import datetime, timedelta, timezone

from radar.services.article_freshness import check_freshness

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def test_recent_article():
    result = check_freshness(NOW - timedelta(days=1), NOW)
    assert result.status == "fresh"


def test_old_article():
    result = check_freshness(NOW - timedelta(days=30), NOW)
    assert result.status == "stale"


def test_missing_date():
    result = check_freshness(None, NOW)
    assert result.status == "needs_review"


def test_future_date():
    result = check_freshness(NOW + timedelta(days=1), NOW)
    assert result.status == "needs_review"


def test_timezone_missing():
    result = check_freshness(
        datetime(2026, 11, 8, 12, 0),
        NOW,
    )
    assert result.status == "needs_review"


def test_seven_day_boundary():
    result = check_freshness(NOW - timedelta(days=7), NOW)
    assert result.status == "fresh"
