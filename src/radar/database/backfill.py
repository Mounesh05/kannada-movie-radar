
import argparse

from radar.collectors.rss_collector import collect_rss
from radar.database.connection import get_connection
from radar.services.article_backfill import (
    plan_article_backfill,
)


def run_backfill(feed_url: str, apply: bool = False) -> None:
    """Refresh existing articles from their original RSS feed."""

    print("\nKannada Movie Radar — Historical Backfill")
    print("Mode:", "APPLY" if apply else "DRY RUN")

    articles = collect_rss(feed_url)

    matched = 0
    updated = 0
    unchanged = 0
    not_found = 0

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for article in articles:
                article_url = article["url"]

                # Lock matching records during a real update.
                lock_clause = "FOR UPDATE OF a" if apply else ""

                cursor.execute(
                    f"""
                    SELECT a.id, a.title, a.published_at
                    FROM articles AS a
                    JOIN sources AS s
                        ON s.id = a.source_id
                    WHERE a.url = %s
                      AND s.feed_url = %s
                    {lock_clause}
                    """,
                    (article_url, feed_url),
                )

                existing = cursor.fetchone()

                if existing is None:
                    not_found += 1
                    continue

                matched += 1
                article_id, old_title, old_date = existing

                changes = plan_article_backfill(
                    current_title=old_title,
                    current_published_at=old_date,
                    feed_title=article["title"],
                    feed_published_at=article.get(
                        "published_at"
                    ),
                )

                if not (
                    changes.title_changed or changes.date_added
                ):
                    unchanged += 1
                    continue

                print(f"\nArticle ID: {article_id}")
                print(f"Old title: {old_title}")
                print(f"New title: {changes.title}")
                print(f"Old date: {old_date}")
                print(f"New date: {changes.published_at}")

                if apply:
                    cursor.execute(
                        """
                        UPDATE articles
                        SET title = %s,
                            published_at = %s
                        WHERE id = %s
                        """,
                        (
                            changes.title,
                            changes.published_at,
                            article_id,
                        ),
                    )

                updated += 1

    print("\n========== SUMMARY ==========")
    print(f"Feed articles: {len(articles)}")
    print(f"Matched existing records: {matched}")
    print(f"Changes {'applied' if apply else 'proposed'}: {updated}")
    print(f"Already up to date: {unchanged}")
    print(f"Not in database: {not_found}")

    if not apply:
        print("\nNo database records were modified.")
        print("Run with --apply after reviewing the changes.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely backfill historical RSS metadata"
    )

    parser.add_argument(
        "--feed",
        required=True,
        help="Original RSS feed URL",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply updates instead of previewing",
    )

    args = parser.parse_args()

    run_backfill(
        feed_url=args.feed,
        apply=args.apply,
    )


if __name__ == "__main__":
    main()
