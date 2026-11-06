
from datetime import datetime, timezone

from radar.services.article_backfill import (
    plan_article_backfill,
)


def test_clean_old_article_title():
    result = plan_article_backfill(
        current_title="Kannada &amp; Cinema",
        current_published_at=None,
        feed_title="Kannada & Cinema",
        feed_published_at=None,
    )

    assert result.title == "Kannada & Cinema"
    assert result.title_changed is True


def test_fill_missing_publication_date():
    published = datetime(
        2024, 3, 17, 3, 11,
        tzinfo=timezone.utc,
    )

    result = plan_article_backfill(
        current_title="Movie News",
        current_published_at=None,
        feed_title="Movie News",
        feed_published_at=published,
    )

    assert result.published_at == published
    assert result.date_added is True


def test_preserve_existing_date():
    original = datetime(
        2023, 1, 1, tzinfo=timezone.utc
    )

    incoming = datetime(
        2024, 1, 1, tzinfo=timezone.utc
    )

    result = plan_article_backfill(
        current_title="Movie News",
        current_published_at=original,
        feed_title="Movie News",
        feed_published_at=incoming,
    )

    assert result.published_at == original
    assert result.date_added is False


def test_no_changes_needed():
    result = plan_article_backfill(
        current_title="ಕನ್ನಡ ಸಿನಿಮಾ",
        current_published_at=None,
        feed_title="ಕನ್ನಡ ಸಿನಿಮಾ",
        feed_published_at=None,
    )

    assert result.title_changed is False
    assert result.date_added is False


def test_empty_feed_title_preserves_existing():
    result = plan_article_backfill(
        current_title="Original title",
        current_published_at=None,
        feed_title="",
        feed_published_at=None,
    )

    assert result.title == "Original title"
    assert result.title_changed is False
