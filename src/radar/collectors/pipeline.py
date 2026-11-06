
import argparse

from radar.collectors.rss_collector import collect_rss
from radar.database.articles import save_article
from radar.services.article_classifier import classify_article


def run_pipeline(feed_url: str) -> None:
    """Collect, classify and store RSS articles."""

    print("\nKannada Movie Radar")
    print("Starting RSS collection pipeline...\n")

    # Step 1: Collect articles from the RSS feed.
    articles = collect_rss(feed_url)

    print(f"Articles fetched: {len(articles)}")

    # Step 2: Initialize classification counters.
    classification_counts = {
        "relevant": 0,
        "needs_review": 0,
        "not_relevant": 0,
    }

    inserted_count = 0

    # Step 3: Process each article.
    for article in articles:

        title = article["title"]
        article_url = article["url"]
        source_name = article["source"]

        # Classify based on article title.
        classification = classify_article(title)

        classification_counts[
            classification.status
        ] += 1

        # Step 4: Store article in PostgreSQL.
        was_inserted = save_article(
            source_name=source_name,
            feed_url=feed_url,
            title=title,
            article_url=article_url,
            classification_status=classification.status,
            classification_reason=classification.reason,
        )

        if was_inserted:
            inserted_count += 1

        # Display processing information.
        print("\n----------------------------------")
        print(f"Title: {title}")
        print(f"Classification: {classification.status}")
        print(f"Reason: {classification.reason}")
        print(
            f"Database: "
            f"{'Inserted' if was_inserted else 'Duplicate'}"
        )

    # Step 5: Display the collection summary.
    print("\n==================================")
    print("RSS COLLECTION SUMMARY")
    print("==================================")

    print(f"Total fetched: {len(articles)}")
    print(f"New articles inserted: {inserted_count}")
    print(
        f"Duplicates skipped: "
        f"{len(articles) - inserted_count}"
    )

    print("\nClassification results:")

    for status, count in classification_counts.items():
        print(f"{status}: {count}")

    print("\nPipeline completed successfully!")


def main() -> None:
    """CLI entry point for RSS collection."""

    parser = argparse.ArgumentParser(
        description=(
            "Kannada Movie Radar RSS collection pipeline"
        )
    )

    parser.add_argument(
        "--feed",
        required=True,
        help="RSS or Atom feed URL",
    )

    args = parser.parse_args()

    run_pipeline(args.feed)


if __name__ == "__main__":
    main()
