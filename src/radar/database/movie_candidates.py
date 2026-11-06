
from psycopg.types.json import Jsonb

from radar.agents.movie_schema import MovieExtraction
from radar.database.connection import get_connection


def get_candidate_for_article(
    article_id: int,
) -> tuple | None:
    """Return an existing candidate for an article."""

    if article_id <= 0:
        raise ValueError("Article ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, movie_title, verification_status
                FROM movie_candidates
                WHERE article_id = %s
                """,
                (article_id,),
            )
            return cursor.fetchone()


def save_movie_candidate(
    article_id: int,
    extraction: MovieExtraction,
    input_title: str,
    model_name: str,
) -> tuple[int, bool]:
    """Insert a candidate once.

    Returns (candidate_id, was_inserted).
    """

    if article_id <= 0:
        raise ValueError("Article ID must be positive")

    if not extraction.movie_title or not extraction.movie_title.strip():
        raise ValueError("Cannot save a candidate without a movie title")

    if not input_title.strip():
        raise ValueError("Input article title is required")

    if not model_name.strip():
        raise ValueError("Model name is required")

    if not extraction.evidence:
        raise ValueError("Evidence is required to save a candidate")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO movie_candidates (
                    article_id,
                    movie_title,
                    film_language,
                    is_kannada_film,
                    release_date_text,
                    mentioned_people,
                    evidence,
                    ai_needs_review,
                    input_title,
                    model_name
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (article_id)
                DO NOTHING
                RETURNING id
                """,
                (
                    article_id,
                    extraction.movie_title.strip(),
                    extraction.film_language,
                    extraction.is_kannada_film,
                    extraction.release_date,
                    Jsonb(extraction.mentioned_people),
                    Jsonb(extraction.evidence),
                    extraction.needs_review,
                    input_title,
                    model_name,
                ),
            )

            inserted = cursor.fetchone()

            if inserted is not None:
                return inserted[0], True

            # An existing candidate is never overwritten.
            cursor.execute(
                """
                SELECT id
                FROM movie_candidates
                WHERE article_id = %s
                """,
                (article_id,),
            )

            existing = cursor.fetchone()

            if existing is None:
                raise RuntimeError(
                    "Candidate conflict occurred but no row was found"
                )

            return existing[0], False
