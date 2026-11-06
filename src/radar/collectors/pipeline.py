
import argparse
from datetime import datetime, timezone

from radar.collectors.rss_collector import collect_rss
from radar.database.articles import save_article


def parse_published(value: str | None):
    # Preserve the original timestamp later during
    # the improved date-normalization phase.
    return None


def run_pipeline(feed_url: str) -> None:
    articles = collect_rss(feed_url)

    inserted_count = 0

    for article in articles:
        was_inserted = save_article(
            source_name=article["source"],
            feed_url=feed_url,
            title=article["title"],
            article_url=article["url"],
            published_at=parse_published(
                article.get("published")
            ),
        )

        if was_inserted:
            inserted_count += 1

    print(f"Articles fetched: {len(articles)}")
    print(f"New articles saved: {inserted_count}")
    print(f"Duplicates skipped: {len(articles) - inserted_count}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--feed",
        required=True,
        help="Permitted RSS or Atom feed URL",
    )

    args = parser.parse_args()
    run_pipeline(args.feed)


if __name__ == "__main__":
    main()
