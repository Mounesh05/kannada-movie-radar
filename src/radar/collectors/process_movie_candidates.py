
import argparse

from radar.agents.movie_graph import build_movie_graph
from radar.database.connection import get_connection


def get_pending_news(
    limit: int = 8,
    retry_no_candidate: bool = False,
) -> list[tuple[int, str]]:
    """Find pending news events eligible for movie extraction.

    By default, articles with any previous extraction attempt
    are skipped.

    When retry_no_candidate=True, only previous no_candidate
    outcomes become eligible again. Articles with successful
    candidates or failed extraction attempts remain excluded.
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
                        AND ea.status IN (
                            'saved',
                            'duplicate',
                            'failed'
                        )
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

                ORDER BY
                    a.published_at DESC NULLS LAST,
                    a.id ASC
                LIMIT %s
                """,
                (retry_no_candidate, limit),
            )

            return cur.fetchall()


def run(
    limit: int = 8,
    execute: bool = False,
    retry_no_candidate: bool = False,
) -> None:
    """Preview or execute movie candidate extraction."""

    articles = get_pending_news(
        limit=limit,
        retry_no_candidate=retry_no_candidate,
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

    for article_id, title in articles:
        print(f"\nProcessing article {article_id}: {title}")

        try:
            result = graph.invoke(
                {"article_id": article_id}
            )

            outcome = result.get("outcome", "unknown")
            candidate_id = result.get("candidate_id")
            reason = result.get("reason")

            print(f"Outcome: {outcome}")
            print(f"Candidate: {candidate_id}")

            if reason:
                print(f"Reason: {reason}")

        except Exception as exc:
            print(
                f"Article {article_id} failed: "
                f"{type(exc).__name__}: {exc}"
            )

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
        help="Maximum number of articles to process (1-20)",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Call Gemini and save extraction results",
    )

    parser.add_argument(
        "--retry-no-candidate",
        action="store_true",
        help=(
            "Allow explicit retry of articles with "
            "previous no_candidate outcomes"
        ),
    )

    args = parser.parse_args()

    run(
        limit=args.limit,
        execute=args.execute,
        retry_no_candidate=args.retry_no_candidate,
    )


if __name__ == "__main__":
    main()
