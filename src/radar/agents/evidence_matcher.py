
"""Conservative cross-publisher movie evidence matching.

This module:
- Matches movie titles against stored article headlines.
- Supports explicitly supplied alternate titles.
- Excludes the original publisher and original article.
- Never creates evidence records or verifies claims.
"""

import argparse
import re
import unicodedata
from dataclasses import dataclass

from radar.database.connection import get_connection
from radar.services.verification_policy import source_host


@dataclass(frozen=True)
class MovieCandidate:
    id: int
    movie_title: str
    original_url: str


@dataclass(frozen=True)
class Article:
    id: int
    title: str
    url: str


@dataclass(frozen=True)
class EvidenceMatch:
    article_id: int
    title: str
    url: str
    publisher: str
    matched_alias: str


def normalize_text(value: str) -> str:
    """Normalize text while preserving Kannada script marks."""

    value = unicodedata.normalize(
        "NFKC", value
    ).casefold()

    value = "".join(
        char
        if unicodedata.category(char)[0] in {"L", "N", "M"}
        else " "
        for char in value
    )

    return re.sub(r"\s+", " ", value).strip()


def title_matches(headline: str, alias: str) -> bool:
    """Match a complete normalized title phrase."""

    normalized_alias = normalize_text(alias)
    normalized_headline = normalize_text(headline)

    if len(normalized_alias.replace(" ", "")) < 4:
        return False

    # Spaces prevent matching an alias inside a longer
    # normalized word or phrase.
    padded_headline = f" {normalized_headline} "
    padded_alias = f" {normalized_alias} "

    return padded_alias in padded_headline


def match_evidence(
    candidate: MovieCandidate,
    articles: list[Article],
    aliases: list[str] | None = None,
) -> list[EvidenceMatch]:
    """Find independent article headlines mentioning the movie."""

    original_host = source_host(candidate.original_url)

    titles = [candidate.movie_title]

    if aliases:
        titles.extend(aliases)

    # Remove duplicate aliases after normalization.
    unique_titles = list({
        normalize_text(title): title
        for title in titles
        if normalize_text(title)
    }.values())

    results = []
    seen_urls = set()

    for article in articles:
        if article.url == candidate.original_url:
            continue

        try:
            host = source_host(article.url)
        except ValueError:
            continue

        if host == original_host:
            continue

        if article.url in seen_urls:
            continue

        matched = next(
            (
                alias
                for alias in unique_titles
                if title_matches(article.title, alias)
            ),
            None,
        )

        if matched is None:
            continue

        seen_urls.add(article.url)

        results.append(
            EvidenceMatch(
                article_id=article.id,
                title=article.title,
                url=article.url,
                publisher=host,
                matched_alias=matched,
            )
        )

    return results


def load_candidate(candidate_id: int) -> MovieCandidate:
    """Read an unverified movie candidate from PostgreSQL."""

    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT mc.id, mc.movie_title, a.url
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
            "Candidate not found or already reviewed"
        )

    return MovieCandidate(*row)


def load_articles(limit: int = 5000) -> list[Article]:
    """Load known article headlines for comparison."""

    if not 1 <= limit <= 5000:
        raise ValueError("Article limit must be 1-5000")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, url
                FROM articles
                WHERE title IS NOT NULL
                  AND url IS NOT NULL
                ORDER BY published_at DESC NULLS LAST, id DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cur.fetchall()

    return [Article(*row) for row in rows]


def run(candidate_id: int, aliases: list[str]) -> None:
    candidate = load_candidate(candidate_id)
    articles = load_articles()

    matches = match_evidence(
        candidate,
        articles,
        aliases=aliases,
    )

    print("\nKANNADA MOVIE RADAR")
    print("PHASE 4.10E — EVIDENCE MATCHING")
    print("=" * 55)

    print("Candidate:", candidate.id)
    print("Movie:", candidate.movie_title)
    print("Articles searched:", len(articles))
    print("Independent headline matches:", len(matches))

    if not matches:
        print(
            "\nNo independent matches found in stored articles."
        )
        print(
            "This does not establish that the movie "
            "or news claim is false."
        )

    for index, item in enumerate(matches, start=1):
        print("\n" + "-" * 55)
        print(f"{index}. {item.title}")
        print("Publisher:", item.publisher)
        print("Matched title:", item.matched_alias)
        print("URL:", item.url)
        print("Status: UNVERIFIED EVIDENCE LEAD")

    print("\nNo database records were modified.")
    print("No movie was automatically verified.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Match movie mentions across stored publishers"
    )

    parser.add_argument(
        "--candidate-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        help="Manually confirmed alternate movie title",
    )

    args = parser.parse_args()

    run(
        candidate_id=args.candidate_id,
        aliases=args.alias,
    )


if __name__ == "__main__":
    main()
