
import argparse

from radar.database.connection import get_connection
from radar.services.news_categorizer import categorize_news


def run_triage(limit: int = 100, save: bool = False) -> dict:
    """Categorize unprocessed articles without claiming verification."""

    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")

    counts = {
        "scanned": 0,
        "eligible": 0,
        "excluded": 0,
        "saved": 0,
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.title, a.classification_status
                FROM articles AS a
                WHERE a.classification_status IN (
                    'relevant', 'needs_review'
                )
                AND a.published_at IS NOT NULL
                AND a.published_at <= CURRENT_TIMESTAMP
                AND a.published_at >= CURRENT_TIMESTAMP
                    - INTERVAL '7 days'
                AND NOT EXISTS (
                    SELECT 1
                    FROM news_events AS n
                    WHERE n.article_id = a.id
                )
                ORDER BY a.published_at DESC, a.id DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cur.fetchall()

            for article_id, title, relevance in rows:
                counts["scanned"] += 1
                result = categorize_news(title)

                if result.category == "other":
                    counts["excluded"] += 1
                    print(f"EXCLUDED [{article_id}]: {title}")
                    continue

                counts["eligible"] += 1
                print(
                    f"{result.category} | under_review | "
                    f"{title}"
                )

                if not save:
                    continue

                cur.execute(
                    """
                    INSERT INTO news_events (
                        article_id,
                        category,
                        evidence_label,
                        category_method,
                        first_seen_at
                    )
                    SELECT
                        id,
                        %s,
                        'under_review',
                        'rules_v1',
                        collected_at
                    FROM articles
                    WHERE id = %s
                    ON CONFLICT (article_id)
                    DO NOTHING
                    RETURNING id
                    """,
                    (result.category, article_id),
                )

                if cur.fetchone():
                    counts["saved"] += 1

            if not save:
                conn.rollback()

    print("\nNEWS TRIAGE SUMMARY")
    for key, value in counts.items():
        print(f"{key}: {value}")

    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    run_triage(limit=args.limit, save=args.save)


if __name__ == "__main__":
    main()
