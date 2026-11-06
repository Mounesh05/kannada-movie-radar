
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx


def collect_rss(feed_url: str) -> list[dict[str, Any]]:
    """Collect article metadata from an RSS or Atom feed."""

    try:
        response = httpx.get(
            feed_url,
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": "KannadaMovieRadar/0.1"
            },
        )
        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            raise RuntimeError(
                "RSS access denied (HTTP 403). "
                "Check whether the publisher permits "
                "automated access."
            ) from exc
        raise

    parsed = feedparser.parse(response.content)

    if parsed.bozo and not parsed.entries:
        raise ValueError("Invalid RSS or Atom feed")

    articles = []

    for entry in parsed.entries:
        if not entry.get("title") or not entry.get("link"):
            continue

        articles.append({
            "title": entry.title.strip(),
            "url": entry.link.strip(),
            "published": entry.get("published"),
            "source": parsed.feed.get("title", feed_url),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })

    return articles
