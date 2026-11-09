
"""List movie candidates needing independent evidence."""

import argparse
from urllib.parse import quote

from radar.database.connection import get_connection


def list_evidence_queue(limit: int = 20) -> None:
    """Display unverified movies and their evidence coverage."""

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    mc.id,
                    mc.movie_title,
                    mc.is_kannada_film,
                    a.title,
                    a.url,
                    COUNT(DISTINCT me.id) AS evidence_count

                FROM movie_candidates AS mc

                JOIN articles AS a
                    ON a.id = mc.article_id

                LEFT JOIN movie_evidence AS me
                    ON me.candidate_id = mc.id

                WHERE mc.verification_status = 'unverified'

                GROUP BY
                    mc.id,
                    mc.movie_title,
                    mc.is_kannada_film,
                    a.title,
                    a.url

                ORDER BY mc.id ASC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cur.fetchall()

    print("\nKANNADA MOVIE RADAR")
    print("PHASE 4.10 — EVIDENCE DISCOVERY QUEUE")
    print("=" * 60)

    if not rows:
        print("No unverified movie candidates.")
        return

    for (
        candidate_id,
        movie_title,
        language_flag,
        article_title,
        article_url,
        evidence_count,
    ) in rows:
        search_query = quote(
            f'"{movie_title}" Kannada film'
        )

        search_url = (
            "https://www.google.com/search?q="
            + search_query
        )

        print("\n" + "-" * 60)
        print(f"Candidate ID: {candidate_id}")
        print(f"Movie: {movie_title}")
        print(f"Kannada status: {language_flag}")
        print(f"Original headline: {article_title}")
        print(f"Original article: {article_url}")
        print(f"Evidence records: {evidence_count}")
        print(f"Research URL: {search_url}")
        print("Decision: REQUIRES EVIDENCE REVIEW")

    print("\nTotal candidates:", len(rows))
    print("No candidate verification statuses were changed.")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
    )

    args = parser.parse_args()

    list_evidence_queue(limit=args.limit)


if __name__ == "__main__":
    main()
