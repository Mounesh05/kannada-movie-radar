
"""Conservative validation of independently supplied source evidence.

This module never downloads publisher articles, writes to the
database, or automatically verifies a movie or news event.

It checks:
- Source URL validity and different publisher hostname.
- Evidence excerpt presence in supplied source text.
- Movie title presence in the supplied source.
- Whether an explicit source excerpt is usable for review.

Passing checks establish provenance consistency, not factual truth.
"""

import argparse
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from radar.agents.evidence_matcher import title_matches
from radar.database.connection import get_connection
from radar.services.verification_policy import source_host


@dataclass(frozen=True)
class ValidationResult:
    eligible_for_review: bool
    checks: tuple[str, ...]
    issues: tuple[str, ...]


def normalize_excerpt(text: str) -> str:
    """Normalize Unicode and whitespace without changing words."""

    normalized = unicodedata.normalize(
        "NFKC", text
    ).casefold()

    return " ".join(normalized.split())


def validate_source(
    movie_title: str,
    original_url: str,
    supporting_url: str,
    source_text: str,
    excerpt: str,
    aliases: list[str] | None = None,
) -> ValidationResult:
    """Check provenance consistency before human evidence review."""

    checks = []
    issues = []

    if not movie_title.strip():
        issues.append("Movie title is missing")

    try:
        original_host = source_host(original_url)
        supporting_host = source_host(supporting_url)

        if original_host == supporting_host:
            issues.append(
                "Supporting source uses the original publisher"
            )
        else:
            checks.append(
                "Different publisher hostname"
            )

    except ValueError:
        issues.append("Invalid HTTPS source URL")

    normalized_text = normalize_excerpt(source_text)
    normalized_excerpt = normalize_excerpt(excerpt)

    if not normalized_text:
        issues.append("Source text is empty")

    if not normalized_excerpt:
        issues.append("Evidence excerpt is empty")

    elif len(normalized_excerpt) < 20:
        issues.append("Evidence excerpt is too short")

    elif normalized_excerpt not in normalized_text:
        issues.append(
            "Evidence excerpt is not present in supplied source text"
        )

    else:
        checks.append(
            "Evidence excerpt found in supplied source text"
        )

    titles = [movie_title, *(aliases or [])]

    if normalized_text and any(
        title_matches(source_text, title)
        for title in titles
        if title.strip()
    ):
        checks.append("Movie title or supplied alias found")
    else:
        issues.append(
            "Movie title or supplied alias not found in source text"
        )

    if not issues:
        checks.append(
            "Eligible for human source and claim review"
        )

    return ValidationResult(
        eligible_for_review=not issues,
        checks=tuple(checks),
        issues=tuple(issues),
    )


def load_movie(candidate_id: int) -> tuple[str, str]:
    """Retrieve an unverified movie and its original article URL."""

    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT mc.movie_title, a.url
                FROM movie_candidates AS mc
                JOIN articles AS a
                  ON a.id = mc.article_id
                WHERE mc.id = %s
                  AND mc.verification_status = 'unverified'
                """,
                (candidate_id,),
            )

            row = cur.fetchone()

    if row is None:
        raise ValueError(
            "Candidate does not exist or is already reviewed"
        )

    return row


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate supplied independent source evidence"
    )

    parser.add_argument(
        "--candidate-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--source-url",
        required=True,
        help="Original HTTPS URL of the independent source",
    )

    parser.add_argument(
        "--source-file",
        type=Path,
        required=True,
        help="Local UTF-8 source text provided for inspection",
    )

    parser.add_argument(
        "--excerpt",
        required=True,
        help="Exact supporting passage from that source",
    )

    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        help="Previously confirmed alternate movie title",
    )

    args = parser.parse_args()

    movie_title, original_url = load_movie(
        args.candidate_id
    )

    source_text = args.source_file.read_text(
        encoding="utf-8"
    )

    result = validate_source(
        movie_title=movie_title,
        original_url=original_url,
        supporting_url=args.source_url,
        source_text=source_text,
        excerpt=args.excerpt,
        aliases=args.alias,
    )

    print("\nKANNADA MOVIE RADAR")
    print("PHASE 4.10F — EVIDENCE VALIDATION")
    print("=" * 55)
    print("Candidate:", args.candidate_id)
    print("Movie:", movie_title)

    for check in result.checks:
        print("PASS:", check)

    for issue in result.issues:
        print("ISSUE:", issue)

    if result.eligible_for_review:
        print("\nRESULT: ELIGIBLE FOR HUMAN REVIEW")
    else:
        print("\nRESULT: INSUFFICIENT EVIDENCE")

    print("No verification decisions or database changes made.")


if __name__ == "__main__":
    main()
