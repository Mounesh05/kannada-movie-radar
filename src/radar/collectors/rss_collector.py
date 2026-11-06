
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from radar.services.date_parser import parse_feed_date
from radar.services.text_cleaner import clean_text


def collect_rss(feed_url: str) -> list[dict[str, Any]]:
    """Fetch and normalize RSS or Atom article metadata."""

    try:
        response = httpx.get(
            feed_url,
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": "KannadaMovieRadar/0.1",
            },
        )
        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            raise RuntimeError(
                "RSS access denied (HTTP 403). "
                "Check whether automated access is permitted."
            ) from exc
        raise

    parsed = feedparser.parse(response.content)

    if parsed.bozo and not parsed.entries:
        raise ValueError("Invalid RSS or Atom feed")

    source_name = clean_text(
        parsed.feed.get("title", feed_url)
    )

    collected_at = datetime.now(timezone.utc)
    articles = []

    for entry in parsed.entries:
        title = clean_text(entry.get("title"))
        url = entry.get("link", "").strip()

        if not title or not url:
            continue

        date_info = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
        )

        articles.append(
            {
                "title": title,
                "url": url,
                "source": source_name,
                "published_at": parse_feed_date(date_info),
                "collected_at": collected_at.isoformat(),
            }
        )

    return articles
