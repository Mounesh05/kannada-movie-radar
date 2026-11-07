
from radar.database.connection import get_connection
from radar.services.claim_conflicts import (
    ConflictReport,
    ReleaseClaim,
    detect_release_conflicts,
)


def get_release_conflict_report(
    movie_id: int,
) -> tuple[str, ConflictReport]:
    """Read source claims and generate a conflict report."""

    if movie_id <= 0:
        raise ValueError("Movie ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT primary_title
                FROM movies
                WHERE id = %s
                """,
                (movie_id,),
            )

            movie = cursor.fetchone()

            if movie is None:
                raise ValueError("Catalogue movie not found")

            cursor.execute(
                """
                SELECT
                    id,
                    claim_value,
                    date_precision,
                    source_name,
                    source_url
                FROM movie_claims
                WHERE movie_id = %s
                  AND claim_type = 'release_date'
                  AND claim_status <> 'rejected'
                ORDER BY id
                """,
                (movie_id,),
            )

            rows = cursor.fetchall()

    claims = [
        ReleaseClaim(
            claim_id=row[0],
            value=row[1],
            precision=row[2],
            source_name=row[3],
            source_url=row[4],
        )
        for row in rows
    ]

    return movie[0], detect_release_conflicts(claims)
