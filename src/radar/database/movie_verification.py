
from radar.database.connection import get_connection
from radar.services.verification_policy import (
    evaluate_evidence,
    source_host,
)


def add_movie_evidence(
    candidate_id: int,
    source_url: str,
    source_title: str,
    excerpt: str,
    claim_type: str,
) -> int | None:
    """Attach manually checked source evidence."""

    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    source_host(source_url)

    if claim_type not in {"identity", "language", "release"}:
        raise ValueError("Invalid claim type")

    if not source_title.strip() or not excerpt.strip():
        raise ValueError("Source title and excerpt are required")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT a.url, mc.verification_status
                FROM movie_candidates AS mc
                JOIN articles AS a
                    ON a.id = mc.article_id
                WHERE mc.id = %s
                """,
                (candidate_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise ValueError("Movie candidate not found")

            original_url, status = row

            if status != "unverified":
                raise ValueError("Candidate review is already final")

            if source_host(original_url) == source_host(source_url):
                raise ValueError(
                    "Evidence must come from another source host"
                )

            cursor.execute(
                """
                INSERT INTO movie_evidence (
                    candidate_id,
                    source_url,
                    source_title,
                    evidence_excerpt,
                    claim_type
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (
                    candidate_id, source_url, claim_type
                )
                DO NOTHING
                RETURNING id
                """,
                (
                    candidate_id,
                    source_url.strip(),
                    source_title.strip(),
                    excerpt.strip(),
                    claim_type,
                ),
            )

            inserted = cursor.fetchone()
            return inserted[0] if inserted else None


def get_verification_report(candidate_id: int) -> dict:
    """Read a candidate and its submitted source evidence."""

    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    mc.movie_title,
                    mc.is_kannada_film,
                    mc.verification_status,
                    a.url
                FROM movie_candidates AS mc
                JOIN articles AS a
                    ON a.id = mc.article_id
                WHERE mc.id = %s
                """,
                (candidate_id,),
            )
            candidate = cursor.fetchone()

            if candidate is None:
                raise ValueError("Movie candidate not found")

            cursor.execute(
                """
                SELECT source_url, claim_type,
                       source_title, evidence_excerpt
                FROM movie_evidence
                WHERE candidate_id = %s
                ORDER BY id
                """,
                (candidate_id,),
            )
            sources = cursor.fetchall()

    title, language_flag, status, original_url = candidate

    eligibility = evaluate_evidence(
        original_url,
        [(item[0], item[1]) for item in sources],
    )

    return {
        "movie_title": title,
        "is_kannada_film": language_flag,
        "verification_status": status,
        "original_url": original_url,
        "sources": sources,
        "eligibility": eligibility,
    }


def review_movie_candidate(
    candidate_id: int,
    decision: str,
    reviewer: str,
    note: str,
    sources_checked: bool = False,
) -> None:
    """Commit an explicit human review and audit entry."""

    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    if decision not in {"verified", "rejected"}:
        raise ValueError("Invalid verification decision")

    if not reviewer.strip() or not note.strip():
        raise ValueError("Reviewer and review note are required")

    if decision == "verified" and not sources_checked:
        raise ValueError(
            "Reviewer must explicitly confirm source inspection"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    mc.is_kannada_film,
                    mc.verification_status,
                    a.url
                FROM movie_candidates AS mc
                JOIN articles AS a
                    ON a.id = mc.article_id
                WHERE mc.id = %s
                FOR UPDATE OF mc
                """,
                (candidate_id,),
            )

            candidate = cursor.fetchone()

            if candidate is None:
                raise ValueError("Movie candidate not found")

            language_flag, status, original_url = candidate

            if status != "unverified":
                raise ValueError(
                    "Candidate already has a final decision"
                )

            if decision == "verified":
                if language_flag != "yes":
                    raise ValueError(
                        "Only Kannada candidates may be verified"
                    )

                cursor.execute(
                    """
                    SELECT source_url, claim_type
                    FROM movie_evidence
                    WHERE candidate_id = %s
                    """,
                    (candidate_id,),
                )

                eligibility = evaluate_evidence(
                    original_url,
                    cursor.fetchall(),
                )

                if not eligibility.eligible:
                    raise ValueError(
                        "; ".join(eligibility.reasons)
                    )

            cursor.execute(
                """
                UPDATE movie_candidates
                SET verification_status = %s
                WHERE id = %s
                """,
                (decision, candidate_id),
            )

            cursor.execute(
                """
                INSERT INTO movie_verification_reviews (
                    candidate_id,
                    reviewer,
                    decision,
                    review_note
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    candidate_id,
                    reviewer.strip(),
                    decision,
                    note.strip(),
                ),
            )
