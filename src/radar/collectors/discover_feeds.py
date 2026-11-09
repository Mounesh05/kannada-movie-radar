
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import feedparser
import httpx

SITES = [
    "https://www.cinisuddi.com/",
    "https://www.cinemaexpress.com/kannada/news",
]


class FeedFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.feeds = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return

        attributes = dict(attrs)

        if (
            "alternate" in attributes.get("rel", "").split()
            and attributes.get("type", "") in {
                "application/rss+xml",
                "application/atom+xml",
            }
        ):
            href = attributes.get("href")

            if href:
                self.feeds.append(href)


def check_site(url):
    print(f"\n{'=' * 60}")
    print("Website:", url)

    try:
        response = httpx.get(
            url,
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "KannadaMovieRadar/0.1 "
                    "(https://github.com/Mounesh05/"
                    "kannada-movie-radar)"
                )
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print("Website unavailable:", exc)
        return

    finder = FeedFinder()
    finder.feed(response.text)

    if not finder.feeds:
        print("No RSS/Atom feed advertised in page HTML.")
        return

    for href in dict.fromkeys(finder.feeds):
        feed_url = urljoin(str(response.url), href)

        if (
            urlsplit(feed_url).hostname
            != urlsplit(url).hostname
        ):
            print("External feed reference:", feed_url)
            continue

        print("\nDiscovered feed:", feed_url)

        try:
            feed_response = httpx.get(
                feed_url,
                timeout=20,
                follow_redirects=True,
            )
            print("HTTP:", feed_response.status_code)

            feed_response.raise_for_status()

            feed = feedparser.parse(feed_response.content)

            print("Entries:", len(feed.entries))

            for entry in feed.entries[:5]:
                print("-", entry.get("title", "Untitled"))

        except httpx.HTTPError as exc:
            print("Feed unavailable:", exc)


def main():
    print("Read-only RSS discovery")
    print("No database or Kafka writes")

    for site in SITES:
        check_site(site)


if __name__ == "__main__":
    main()
