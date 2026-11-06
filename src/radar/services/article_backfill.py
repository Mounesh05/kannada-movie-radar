
from dataclasses import dataclass
from datetime import datetime

from radar.services.text_cleaner import clean_text


@dataclass(frozen=True)
class BackfillChanges:
    title: str
    published_at: datetime | None
    title_changed: bool
    date_added: bool


def plan_article_backfill(
    current_title: str,
    current_published_at: datetime | None,
    feed_title: str,
    feed_published_at: datetime | None,
) -> BackfillChanges:
    """Calculate changes without modifying the database."""

    cleaned_title = clean_text(feed_title)

    # Retain existing title if feed metadata is empty.
    new_title = (
        cleaned_title
        if cleaned_title
        else current_title
    )

    # Never replace an existing publication date.
    new_date = (
        current_published_at
        if current_published_at is not None
        else feed_published_at
    )

    return BackfillChanges(
        title=new_title,
        published_at=new_date,
        title_changed=new_title != current_title,
        date_added=(
            current_published_at is None
            and new_date is not None
        ),
    )
