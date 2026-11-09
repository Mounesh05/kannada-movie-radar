
import argparse

from radar.collectors.rss_collector import collect_rss
from radar.database.articles import save_article
from radar.services.article_classifier import classify_article
from radar.services.article_freshness import check_freshness


def run_pipeline(
    feed_url: str,
    dry_run: bool = False,
) -> None:
    """Collect recent RSS articles and classify them conservatively."""

    print("\nKannada Movie Radar")
    print("Starting RSS collection pipeline...\n")

    articles = collect_rss(feed_url)

    counts = {
        "relevant": 0,
        "needs_review": 0,
        "not_relevant": 0,
        "stale": 0,
        "inserted": 0,
        "duplicate": 0,
        "dry_run": 0,
    }

    for article in articles:
        title = article["title"]

        freshness = check_freshness(
            article.get("published_at"),
        )

        print("\n" + "-" * 60)
        print(f"Title: {title}")
        print(f"Published: {article.get('published_at')}")
        print(f"Freshness: {freshness.status}")

        if freshness.status == "stale":
            counts["stale"] += 1
            print("Action: Skipped — older than 7 days")
            continue

        classification = classify_article(title)

        # An uncertain publication date must not be
        # treated as automatically publishable news.
        if freshness.status == "needs_review":
            status = "needs_review"
            reason = freshness.reason
        else:
            status = classification.status
            reason = classification.reason

        counts[status] += 1

        print(f"Relevance: {status}")
        print(f"Reason: {reason}")

        if dry_run:
            counts["dry_run"] += 1
            print("Database: Preview only")
            continue

        inserted = save_article(
            source_name=article["source"],
            feed_url=feed_url,
            title=title,
            article_url=article["url"],
            published_at=article.get("published_at"),
            classification_status=status,
            classification_reason=reason,
        )

        if inserted:
            counts["inserted"] += 1
            print("Database: Inserted")
        else:
            counts["duplicate"] += 1
            print("Database: Duplicate")

    print("\n" + "=" * 60)
    print("RSS COLLECTION SUMMARY")
    print(f"Fetched: {len(articles)}")

    for name, count in counts.items():
        print(f"{name}: {count}")

    print("\nPipeline completed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kannada Movie Radar RSS pipeline",
    )

    parser.add_argument(
        "--feed",
        required=True,
        help="Permitted RSS or Atom feed URL",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without database writes",
    )

    args = parser.parse_args()

    run_pipeline(
        feed_url=args.feed,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
