
from datetime import datetime, timezone

import feedparser
import httpx

from radar.services.article_classifier import classify_article

SOURCES = [
    {
        "name": "Cinema Express Kannada",
        "url": "https://www.cinemaexpress.com/kannada/news",
        "kind": "page",
    },
    {
        "name": "Cini Suddi Kannada Cinema",
        "url": "https://www.cinisuddi.com/",
        "kind": "page",
    },
    {
        "name": "Oneindia Kannada Entertainment RSS",
        "url": (
            "https://kannada.oneindia.com/rss/feeds/"
            "kannada-entertainment-fb.xml"
        ),
        "kind": "rss",
    },
]



def inspect_source(source: dict) -> None:
    print(f"\n{'=' * 60}")
    print(f"Source: {source['name']}")
    print(f"URL: {source['url']}")

    try:
        response = httpx.get(
            source["url"],
            headers={
                "User-Agent": (
                    "KannadaMovieRadar/0.1 "
                    "(https://github.com/"
                    "Mounesh05/kannada-movie-radar)"
                ),
                "Accept": (
                    "application/rss+xml, application/atom+xml, "
                    "application/xml, text/html"
                ),
            },
            timeout=20,
            follow_redirects=True,
        )

        print(f"HTTP status: {response.status_code}")
        print(f"Final URL: {response.url}")

        response.raise_for_status()

        if source["kind"] == "page":
            print("Web page reachable.")
            print("Automated article ingestion not enabled.")
            return

        feed = feedparser.parse(response.content)

        if feed.bozo:
            print("Feed parser warning:", feed.bozo_exception)

        print(f"Entries found: {len(feed.entries)}")

        counts = {
            "relevant": 0,
            "needs_review": 0,
            "not_relevant": 0,
        }

        for entry in feed.entries[:20]:
            title = entry.get("title", "").strip()
            classification = classify_article(title)
            counts[classification.status] += 1

            print(f"\nTitle: {title}")
            print(f"Published: {entry.get('published', 'Unknown')}")
            print(f"Classification: {classification.status}")
            print(f"URL: {entry.get('link', '')}")

        print("\nFirst 20 entry classifications:", counts)

    except (httpx.HTTPError, ValueError) as exc:
        print(f"Source unavailable: {type(exc).__name__}")
        print(str(exc)[:300])


def main() -> None:
    print("Kannada Movie Radar — Film Source Probe")
    print("Run time:", datetime.now(timezone.utc).isoformat())
    print("Read-only: no database writes")

    for source in SOURCES:
        inspect_source(source)


if __name__ == "__main__":
    main()
