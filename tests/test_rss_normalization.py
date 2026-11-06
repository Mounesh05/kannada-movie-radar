
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from radar.collectors.rss_collector import collect_rss

RSS = """
<rss version="2.0">
  <channel>
    <title>Kannada Cinema</title>
    <item>
      <title>Kannada &amp; Movie News</title>
      <link>https://example.com/article</link>
      <pubDate>Fri, 06 Nov 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_rss_normalization():
    response = Mock()
    response.content = RSS.encode("utf-8")
    response.raise_for_status.return_value = None

    with patch(
        "radar.collectors.rss_collector.httpx.get",
        return_value=response,
    ):
        articles = collect_rss(
            "https://example.com/feed.xml"
        )

    assert len(articles) == 1
    assert articles[0]["title"] == "Kannada & Movie News"
    assert articles[0]["published_at"] == datetime(
        2026, 11, 6, 12, 0,
        tzinfo=timezone.utc,
    )
