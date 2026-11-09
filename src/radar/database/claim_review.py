
from radar.database.connection import get_connection
from radar.services.claim_review_policy import (
    validate_claim,
    validate_review,
)


def add_source_claim(
    movie_id: int,
    claim_type: str,
    value: str,
    precision: str | None,
    source_name: str,
    source_url: str,
    excerpt: str,
    release_kind: str | None = None,
    territory: str | None = None,
) -> tuple[int, bool]:
    """Insert an unverified claim; never modify canonical facts."""

    if movie_id <= 0:
        raise ValueError("Movie ID must be positive")

    if not source_name.strip():
        raise ValueError("Source name is required")

    validate_claim(
        claim_type,
        value,
        precision,
        source_url,
        excerpt,
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM movies WHERE id = %s
                """,
                (movie_id,),
            )

            if cursor.fetchone() is None:
                raise ValueError("Movie not found")

            cursor.execute(
                """
                INSERT INTO movie_claims (
                    movie_id,
                    claim_type,
                    claim_value,
                    date_precision,
                    source_name,
                    source_url,
                    source_excerpt,
                    release_kind,
                    release_territory
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (
                    movie_id,
                    claim_type,
                    claim_value,
                    source_url
                )
                DO NOTHING
                RETURNING id
                """,
                (
                    movie_id,
                    claim_type,
                    value.strip(),
                    precision,
                    source_name.strip(),
                    source_url.strip(),
                    excerpt.strip(),
                    release_kind.strip()
                    if release_kind else None,
                    territory.strip()
                    if territory else None,
                ),
            )

            result = cursor.fetchone()

            if result is not None:
                return result[0], True

            cursor.execute(
                """
                SELECT id
                FROM movie_claims
                WHERE movie_id = %s
                  AND claim_type = %s
                  AND claim_value = %s
                  AND source_url = %s
                """,
                (
                    movie_id,
                    claim_type,
                    value.strip(),
                    source_url.strip(),
                ),
            )

            return cursor.fetchone()[0], False


def review_source_claim(
    claim_id: int,
    decision: str,
    reviewer: str,
    note: str,
    sources_checked: bool,
) -> None:
    """Review claim and write an audit record atomically."""

    if claim_id <= 0:
        raise ValueError("Claim ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT claim_status
                FROM movie_claims
                WHERE id = %s
                FOR UPDATE
                """,
                (claim_id,),
            )

            row = cursor.fetchone()

            if row is None:
                raise ValueError("Claim not found")

            previous_status = row[0]

            validate_review(
                previous_status,
                decision,
                reviewer,
                note,
                sources_checked,
            )

            cursor.execute(
                """
                UPDATE movie_claims
                SET claim_status = %s,
                    reviewer_note = %s
                WHERE id = %s
                """,
                (
                    decision,
                    note.strip(),
                    claim_id,
                ),
            )

            cursor.execute(
                """
                INSERT INTO movie_claim_reviews (
                    claim_id,
                    previous_status,
                    new_status,
                    reviewer,
                    review_note,
                    sources_checked
                )
                VALUES (%s, %s, %s, %s, %s, TRUE)
                """,
                (
                    claim_id,
                    previous_status,
                    decision,
                    reviewer.strip(),
                    note.strip(),
                ),
            )
