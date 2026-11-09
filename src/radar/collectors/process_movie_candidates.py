
import argparse

from radar.agents.movie_graph import build_movie_graph
from radar.database.connection import get_connection

MAX_ATTEMPTS = 3


def get_pending_news(
    limit: int = 8,
    retry_no_candidate: bool = False,
    retry_failed: bool = False,
) -> list[tuple[int, str]]:
    """Find pending news eligible for movie extraction.

    Rules:
    - Skip articles with existing movie candidates.
    - Skip successful or duplicate extraction attempts.
    - Retry no_candidate only when explicitly requested.
    - Retry failed only when explicitly requested.
    - Never exceed MAX_ATTEMPTS recorded attempts.
    """

    if not 1 <= limit <= 20:
        raise ValueError("Limit must be between 1 and 20")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.title
                FROM news_events AS n
                JOIN articles AS a
                    ON a.id = n.article_id

                WHERE n.review_status = 'pending'
                  AND n.category <> 'other'

                  AND NOT EXISTS (
                      SELECT 1
                      FROM movie_candidates AS mc
                      WHERE mc.article_id = a.id
                  )

                  AND NOT EXISTS (
                      SELECT 1
                      FROM extraction_attempts AS ea
                      WHERE ea.article_id = a.id
                        AND ea.status IN ('saved', 'duplicate')
                  )

                  AND (
                      %s
                      OR NOT EXISTS (
                          SELECT 1
                          FROM extraction_attempts AS ea
                          WHERE ea.article_id = a.id
                            AND ea.status = 'no_candidate'
                      )
                  )

                  AND (
                      %s
                      OR NOT EXISTS (
                          SELECT 1
                          FROM extraction_attempts AS ea
                          WHERE ea.article_id = a.id
                            AND ea.status = 'failed'
                      )
                  )

                  AND (
                      SELECT COUNT(*)
                      FROM extraction_attempts AS ea
                      WHERE ea.article_id = a.id
                  ) < %s

                ORDER BY
                    a.published_at DESC NULLS LAST,
                    a.id ASC

                LIMIT %s
                """,
                (
                    retry_no_candidate,
                    retry_failed,
                    MAX_ATTEMPTS,
                    limit,
                ),
            )

            return cur.fetchall()


def run(
    limit: int = 8,
    execute: bool = False,
    retry_no_candidate: bool = False,
    retry_failed: bool = False,
) -> None:
    """Preview or execute movie candidate extraction."""

    articles = get_pending_news(
        limit=limit,
        retry_no_candidate=retry_no_candidate,
        retry_failed=retry_failed,
    )

    print("\nKannada Movie Radar")
    print("Movie Candidate Extraction")
    print("=" * 50)
    print(f"Pending articles: {len(articles)}")

    if not execute:
        for article_id, title in articles:
            print(f"[PREVIEW] {article_id}: {title}")

        print("\nNo Gemini requests or database writes made.")
        return

    if not articles:
        print("No eligible articles to process.")
        return

    graph = build_movie_graph()

    counts = {
        "saved": 0,
        "existing": 0,
        "no_candidate": 0,
        "failed": 0,
        "other": 0,
    }

    for article_id, title in articles:
        print(f"\nProcessing article {article_id}: {title}")

        try:
            result = graph.invoke(
                {"article_id": article_id}
            )

            outcome = result.get("outcome", "unknown")
            candidate_id = result.get("candidate_id")
            reason = result.get("reason")
            error_type = result.get("error_type")

            print(f"Outcome: {outcome}")
            print(f"Candidate: {candidate_id}")

            if error_type:
                print(f"Error type: {error_type}")

            if reason:
                print(f"Classification/review reason: {reason}")

            if outcome in counts:
                counts[outcome] += 1
            else:
                counts["other"] += 1

        except Exception as exc:
            counts["failed"] += 1
            print(
                f"Article {article_id} failed: "
                f"{type(exc).__name__}: {exc}"
            )

    print("\n" + "=" * 50)
    print("EXTRACTION SUMMARY")
    print("=" * 50)

    for name, count in counts.items():
        print(f"{name}: {count}")

    print("\nExtraction run completed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Kannada movie candidates "
            "from pending news events"
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Maximum articles to process (1-20)",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Call Gemini and store extraction results",
    )

    parser.add_argument(
        "--retry-no-candidate",
        action="store_true",
        help="Allow retry of no_candidate extraction attempts",
    )

    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Allow retry of failed extraction attempts",
    )

    args = parser.parse_args()

    run(
        limit=args.limit,
        execute=args.execute,
        retry_no_candidate=args.retry_no_candidate,
        retry_failed=args.retry_failed,
    )


if __name__ == "__main__":
    main()
