
from radar.database.connection import get_connection
from radar.services.movie_matcher import suggest_matches


def find_candidate_matches(candidate_id: int) -> dict:
    """Find suggestions without writing to the database."""

    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT movie_title,
                       is_kannada_film,
                       verification_status
                FROM movie_candidates
                WHERE id = %s
                """,
                (candidate_id,),
            )
            candidate = cursor.fetchone()

            if candidate is None:
                raise ValueError("Candidate not found")

            title, language_flag, status = candidate

            cursor.execute(
                """
                SELECT movie_id
                FROM movie_candidate_links
                WHERE candidate_id = %s
                """,
                (candidate_id,),
            )
            existing_link = cursor.fetchone()

            if status == "rejected" or language_flag == "no":
                return {
                    "title": title,
                    "reason": "Candidate excluded from Kannada matching",
                    "suggestions": [],
                }

            if existing_link is not None:
                return {
                    "title": title,
                    "reason": "Candidate already linked",
                    "suggestions": [],
                }

            cursor.execute(
                """
                SELECT id, primary_title
                FROM movies
                WHERE original_language = 'kn'
                   OR original_language IS NULL
                ORDER BY id
                """
            )
            catalogue = cursor.fetchall()

    return {
        "title": title,
        "reason": "Suggestions only; human review required",
        "suggestions": suggest_matches(title, catalogue),
    }


def review_movie_match(
    candidate_id: int,
    movie_id: int,
    decision: str,
    reviewer: str,
    note: str,
) -> None:
    """Review a match atomically, without changing movie facts."""

    if candidate_id <= 0 or movie_id <= 0:
        raise ValueError("IDs must be positive")

    if decision not in {"approved", "rejected"}:
        raise ValueError("Invalid match decision")

    if not reviewer.strip() or not note.strip():
        raise ValueError("Reviewer and note are required")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Lock the candidate to serialize decisions for it.
            cursor.execute(
                """
                SELECT movie_title, is_kannada_film,
                       verification_status
                FROM movie_candidates
                WHERE id = %s
                FOR UPDATE
                """,
                (candidate_id,),
            )
            candidate = cursor.fetchone()

            if candidate is None:
                raise ValueError("Candidate not found")

            title, language_flag, status = candidate

            if status == "rejected" or language_flag == "no":
                raise ValueError("Candidate is not eligible for matching")

            cursor.execute(
                """
                SELECT id, primary_title, original_language
                FROM movies
                WHERE id = %s
                """,
                (movie_id,),
            )
            movie = cursor.fetchone()

            if movie is None:
                raise ValueError("Catalogue movie not found")

            if movie[2] not in ("kn", None):
                raise ValueError("Catalogue movie is not Kannada")

            cursor.execute(
                """
                SELECT movie_id
                FROM movie_candidate_links
                WHERE candidate_id = %s
                """,
                (candidate_id,),
            )
            if cursor.fetchone() is not None:
                raise ValueError("Candidate already linked")

            if decision == "approved":
                cursor.execute(
                    """
                    INSERT INTO movie_candidate_links (
                        candidate_id,
                        movie_id,
                        reviewer,
                        review_note
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        candidate_id,
                        movie_id,
                        reviewer.strip(),
                        note.strip(),
                    ),
                )

            cursor.execute(
                """
                INSERT INTO movie_match_reviews (
                    candidate_id,
                    movie_id,
                    decision,
                    reviewer,
                    review_note
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    candidate_id,
                    movie_id,
                    decision,
                    reviewer.strip(),
                    note.strip(),
                ),
            )
