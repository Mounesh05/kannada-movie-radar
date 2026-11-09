
"""Discover independent movie coverage using the GDELT DOC API.

Search results are leads, NOT verified evidence.

This module:
- Reads unverified movie candidates from PostgreSQL.
- Searches GDELT for possible independent coverage.
- Filters duplicate and same-publisher URLs.
- Reports HTTP status codes for failed searches.
- Never modifies verification decisions or database records.
"""

import argparse
from dataclasses import dataclass

import httpx

from radar.database.connection import get_connection
from radar.services.verification_policy import source_host

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


@dataclass(frozen=True)
class Candidate:
    id: int
    title: str
    original_url: str


@dataclass(frozen=True)
class SearchLead:
    title: str
    url: str
    host: str
    seen_date: str


def load_candidates(
    limit: int = 1,
    candidate_id: int | None = None,
) -> list[Candidate]:
    """Load unverified movie candidates from PostgreSQL."""

    if not 1 <= limit <= 6:
        raise ValueError("limit must be between 1 and 6")

    if candidate_id is not None and candidate_id <= 0:
        raise ValueError("candidate_id must be positive")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    mc.id,
                    mc.movie_title,
                    a.url
                FROM movie_candidates AS mc
                JOIN articles AS a
                    ON a.id = mc.article_id
                WHERE mc.verification_status = 'unverified'
                  AND mc.movie_title IS NOT NULL
                  AND TRIM(mc.movie_title) <> ''
                  AND (%s IS NULL OR mc.id = %s)
                ORDER BY mc.id
                LIMIT %s
                """,
                (candidate_id, candidate_id, limit),
            )

            rows = cur.fetchall()

    return [
        Candidate(
            id=row[0],
            title=row[1],
            original_url=row[2],
        )
        for row in rows
    ]


def select_independent_leads(
    articles: list[dict],
    original_url: str,
    max_results: int,
) -> list[SearchLead]:
    """Filter invalid, duplicate and same-publisher URLs."""

    original_host = source_host(original_url)

    seen_urls: set[str] = set()
    leads: list[SearchLead] = []

    for article in articles:
        if not isinstance(article, dict):
            continue

        url = str(article.get("url") or "").strip()
        title = str(article.get("title") or "").strip()

        if not url or not title:
            continue

        try:
            host = source_host(url)
        except ValueError:
            continue

        if host == original_host:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        leads.append(
            SearchLead(
                title=title,
                url=url,
                host=host,
                seen_date=str(article.get("seendate") or ""),
            )
        )

        if len(leads) >= max_results:
            break

    return leads


def search_gdelt(
    movie_title: str,
    original_url: str,
    max_results: int = 10,
) -> list[SearchLead]:
    """Search GDELT for exact-phrase movie-title coverage."""

    if not 1 <= max_results <= 25:
        raise ValueError("max_results must be between 1 and 25")

    movie_title = movie_title.strip()

    if not movie_title:
        raise ValueError("Movie title cannot be empty")

    # Quoted title prevents unnecessarily broad matching.
    # Kannada titles are not automatically transliterated.
    query = f'"{movie_title}"'

    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_results,
        "timespan": "3m",
    }

    with httpx.Client(
        timeout=30,
        follow_redirects=False,
    ) as client:
        response = client.get(
            GDELT_URL,
            params=params,
        )

        # Allows discover() to identify the actual HTTP status.
        response.raise_for_status()

        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Unexpected GDELT JSON response")

    articles = payload.get("articles", [])

    if not isinstance(articles, list):
        raise ValueError("Unexpected GDELT articles format")

    return select_independent_leads(
        articles=articles,
        original_url=original_url,
        max_results=max_results,
    )


def explain_http_error(status_code: int) -> str:
    """Return a safe explanation for common API errors."""

    explanations = {
        400: (
            "Bad request. The search query or API parameters "
            "may have been rejected."
        ),
        403: (
            "Forbidden. GDELT may be blocking this request."
        ),
        404: (
            "GDELT endpoint not found."
        ),
        429: (
            "Rate limited. Avoid repeated requests and "
            "retry after the server permits."
        ),
        500: (
            "GDELT internal server error."
        ),
        502: (
            "GDELT gateway error."
        ),
        503: (
            "GDELT service temporarily unavailable."
        ),
        504: (
            "GDELT gateway timeout."
        ),
    }

    return explanations.get(
        status_code,
        "Unexpected GDELT HTTP response.",
    )


def discover(
    candidates: list[Candidate],
    max_results: int,
) -> None:
    """Print potential external sources without modifying data."""

    print("\nKANNADA MOVIE RADAR")
    print("PHASE 4.10B — EVIDENCE DISCOVERY")
    print("=" * 60)

    for candidate in candidates:
        print("\n" + "-" * 60)
        print(f"Candidate ID: {candidate.id}")
        print(f"Movie: {candidate.title}")
        print(f"Original: {candidate.original_url}")

        try:
            leads = search_gdelt(
                movie_title=candidate.title,
                original_url=candidate.original_url,
                max_results=max_results,
            )

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            print(f"GDELT HTTP status: {status_code}")
            print(explain_http_error(status_code))
            print("Candidate remains unverified.")
            continue

        except httpx.TimeoutException:
            print("GDELT request timed out.")
            print("Candidate remains unverified.")
            continue

        except httpx.RequestError as exc:
            print(
                "GDELT request failed:",
                type(exc).__name__,
            )
            print("Candidate remains unverified.")
            continue

        except ValueError as exc:
            print(
                "GDELT response could not be processed:",
                type(exc).__name__,
            )
            print("Candidate remains unverified.")
            continue

        if not leads:
            print("No independent source leads found.")
            print("Candidate remains unverified.")
            continue

        print(f"Independent source leads: {len(leads)}")

        for index, lead in enumerate(leads, start=1):
            print(f"\n{index}. {lead.title}")
            print(f"   Host: {lead.host}")
            print(f"   URL: {lead.url}")
            print(f"   Seen: {lead.seen_date}")
            print("   Status: UNCHECKED SEARCH RESULT")

        print(
            "\nThese search results must be inspected "
            "before they can be accepted as evidence."
        )

        print("Candidate remains unverified.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Discover potential independent sources "
            "for Kannada movie candidates"
        )
    )

    parser.add_argument(
        "--candidate-id",
        type=int,
        default=None,
        help="Specific movie candidate ID",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of candidates to process",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum external search leads",
    )

    args = parser.parse_args()

    # Initial version uses one candidate per execution.
    # Avoid rapid requests to the public search service.
    if args.limit != 1:
        parser.error(
            "Only one candidate per execution is supported."
        )

    candidates = load_candidates(
        limit=args.limit,
        candidate_id=args.candidate_id,
    )

    if not candidates:
        print("No matching unverified movie candidates.")
        return

    discover(
        candidates=candidates,
        max_results=args.max_results,
    )


if __name__ == "__main__":
    main()
