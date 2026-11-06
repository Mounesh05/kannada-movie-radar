
from unittest.mock import Mock, patch

from radar.collectors.rss_collector import collect_rss

SAMPLE_RSS = """
<rss version="2.0">
  <channel>
    <title>Sample Kannada Cinema News</title>
    <item>
      <title>Sample Movie Announcement</title>
      <link>https://example.com/movie-news</link>
    </item>
  </channel>
</rss>
"""


def test_collect_rss():
    response = Mock()
    response.content = SAMPLE_RSS.encode()
    response.raise_for_status.return_value = None

    with patch(
        "radar.collectors.rss_collector.httpx.get",
        return_value=response,
    ):
        articles = collect_rss(
            "https://example.com/feed.xml"
        )

    assert len(articles) == 1
    assert articles[0]["title"] == (
        "Sample Movie Announcement"
    )
    assert articles[0]["source"] == (
        "Sample Kannada Cinema News"
    )
