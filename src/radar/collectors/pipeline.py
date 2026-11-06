
import argparse

from radar.collectors.rss_collector import collect_rss
from radar.database.articles import save_article
from radar.services.article_classifier import classify_article


def run_pipeline(feed_url: str) -> None:
    """Collect, classify, and store RSS articles."""

    print("\nKannada Movie Radar")
    print("Starting RSS collection pipeline...\n")

    articles = collect_rss(feed_url)

    counts = {
        "relevant": 0,
        "needs_review": 0,
        "not_relevant": 0,
    }

    inserted_count = 0

    for article in articles:
        classification = classify_article(article["title"])

        counts[classification.status] += 1

        was_inserted = save_article(
            source_name=article["source"],
            feed_url=feed_url,
            title=article["title"],
            article_url=article["url"],
            published_at=article.get("published_at"),
            classification_status=classification.status,
            classification_reason=classification.reason,
        )

        if was_inserted:
            inserted_count += 1

        print("\n----------------------------------")
        print(f"Title: {article['title']}")
        print(f"Classification: {classification.status}")
        print(f"Reason: {classification.reason}")
        print(f"Published: {article.get('published_at')}")
        print(
            "Database: "
            + ("Inserted" if was_inserted else "Duplicate")
        )

    print("\n==================================")
    print("RSS COLLECTION SUMMARY")
    print("==================================")
    print(f"Articles fetched: {len(articles)}")
    print(f"New articles saved: {inserted_count}")
    print(f"Duplicates: {len(articles) - inserted_count}")

    print("\nClassification results:")

    for status, count in counts.items():
        print(f"{status}: {count}")

    print("\nPipeline completed successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kannada Movie Radar RSS pipeline"
    )

    parser.add_argument(
        "--feed",
        required=True,
        help="Permitted RSS or Atom feed URL",
    )

    args = parser.parse_args()
    run_pipeline(args.feed)


if __name__ == "__main__":
    main()
