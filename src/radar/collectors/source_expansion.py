
import argparse

from radar.collectors.rss_collector import collect_rss
from radar.database.articles import save_article
from radar.services.article_classifier import classify_article

FEEDS = {
    "oneindia_entertainment": (
        "https://kannada.oneindia.com/rss/feeds/"
        "kannada-entertainment-fb.xml"
    ),
    "cinema_kamalu": (
        "https://www.aparadhakesavalu.net/"
        "rss/category/cinema-kamalu"
    ),
    "bevarahani": (
        "https://bevarahani.com/rss/category/CINEMA"
    ),
}



def collect_sources(
    save: bool = False,
    limit: int = 10,
) -> dict:
    """Collect RSS headlines with optional database storage."""

    if not 1 <= limit <= 50:
        raise ValueError("Limit must be between 1 and 50")

    summary = {
        "fetched": 0,
        "inserted": 0,
        "failed_feeds": 0,
    }

    for name, feed_url in FEEDS.items():
        print(f"\n========== {name} ==========")

        try:
            articles = collect_rss(feed_url)

        except (RuntimeError, ValueError, Exception) as exc:
            summary["failed_feeds"] += 1
            print(f"Feed unavailable: {type(exc).__name__}")
            continue

        print(f"Available articles: {len(articles)}")

        for article in articles[:limit]:
            classification = classify_article(article["title"])

            summary["fetched"] += 1

            print(f"\nTitle: {article['title']}")
            print(f"URL: {article['url']}")
            print(f"Published: {article['published_at']}")
            print(f"Classification: {classification.status}")   
            if not save:
                continue
            inserted = save_article(
                source_name=article["source"],
                feed_url=feed_url,
                title=article["title"],
                article_url=article["url"],
                published_at=article["published_at"],
                classification_status=classification.status,
                classification_reason=classification.reason,
            )

            if inserted:
                summary["inserted"] += 1

    print("\n========== SUMMARY ==========")
    print(f"Fetched: {summary['fetched']}")
    print(f"Inserted: {summary['inserted']}")
    print(f"Failed feeds: {summary['failed_feeds']}")

    if not save:
        print("PREVIEW ONLY — No database changes.")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test and collect Kannada cinema RSS sources"
    )

    parser.add_argument("--save", action="store_true")
    parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    collect_sources(
        save=args.save,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
