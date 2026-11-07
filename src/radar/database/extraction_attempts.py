
from radar.database.connection import get_connection

VALID_STATUSES = {
    "saved",
    "duplicate",
    "no_candidate",
    "failed",
}


def get_pending_articles(
    limit: int = 3,
    retry_failed: bool = False,
) -> list[tuple[int, str]]:
    """Retrieve articles eligible for extraction."""

    if not 1 <= limit <= 10:
        raise ValueError("Limit must be between 1 and 10")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT a.id, a.title
                FROM articles AS a
                WHERE a.classification_status <> 'not_relevant'
                  AND NOT EXISTS (
                      SELECT 1 FROM movie_candidates AS mc
                      WHERE mc.article_id = a.id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM extraction_attempts AS ea
                      WHERE ea.article_id = a.id
                        AND (
                            ea.status <> 'failed'
                            OR NOT %s
                        )
                  )
                ORDER BY a.published_at DESC NULLS LAST,
                         a.id ASC
                LIMIT %s
                """,
                (retry_failed, limit),
            )
            return cursor.fetchall()


def save_extraction_attempt(
    article_id: int,
    model_name: str,
    status: str,
    candidate_id: int | None = None,
    error_type: str | None = None,
) -> int:
    """Save the result of one extraction attempt."""

    if article_id <= 0:
        raise ValueError("Article ID must be positive")

    if not model_name.strip():
        raise ValueError("Model name is required")

    if status not in VALID_STATUSES:
        raise ValueError("Invalid extraction status")

    if status == "failed" and not error_type:
        raise ValueError("Failed attempts need an error type")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO extraction_attempts (
                    article_id,
                    candidate_id,
                    model_name,
                    status,
                    error_type
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    article_id,
                    candidate_id,
                    model_name,
                    status,
                    error_type,
                ),
            )
            return cursor.fetchone()[0]
