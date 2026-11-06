
from datetime import datetime
from typing import Any

import feedparser
import httpx


def collect_rss(feed_url: str) -> list[dict[str, Any]]:
    """Collect article metadata from an RSS feed."""

    response = httpx.get(
        feed_url,
        timeout=20,
        follow_redirects=True,
        headers={
            "User-Agent": "KannadaMovieRadar/0.1"
        },
    )
    response.raise_for_status()

    parsed = feedparser.parse(response.content)

    if parsed.bozo and not parsed.entries:
        raise ValueError("Invalid RSS or Atom feed")

    articles = []

    for entry in parsed.entries:
        if not entry.get("title") or not entry.get("link"):
            continue

        articles.append({
            "title": entry.title,
            "url": entry.link,
            "published": entry.get("published"),
            "source": parsed.feed.get("title", feed_url),
            "collected_at": datetime.now().isoformat(),
        })

    return articles
