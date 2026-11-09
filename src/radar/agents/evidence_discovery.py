
"""Discover potential independent movie coverage using GDELT.

Search results are leads, NOT verified evidence.
No database writes or review decisions occur here.
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
    """Read unverified movie candidates from Neon."""

    if not 1 <= limit <= 6:
        raise ValueError("limit must be between 1 and 6")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT mc.id, mc.movie_title, a.url
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

            return [
                Candidate(*row)
                for row in cur.fetchall()
            ]


def select_independent_leads(
    articles: list[dict],
    original_url: str,
    max_results: int,
) -> list[SearchLead]:
    """Filter invalid, duplicate and same-publisher URLs."""

    original_host = source_host(original_url)
    seen_urls = set()
    leads = []

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

        if host == original_host or url in seen_urls:
            continue

        seen_urls.add(url)

        leads.append(
            SearchLead(
                title=title,
                url=url,
                host=host,
                seen_date=str(
                    article.get("seendate") or ""
                ),
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
    """Search news metadata for an exact movie-title phrase."""

    if not 1 <= max_results <= 25:
        raise ValueError("max_results must be 1-25")

    movie_title = movie_title.strip()

    if not movie_title:
        raise ValueError("Movie title is missing")

    # Search for the title in quotation marks.
    # No automatic transliteration is performed.
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
        response.raise_for_status()

        # GDELT may return a text response instead of JSON
        # for a rejected query or temporary service issue.
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Unexpected GDELT response")

    articles = payload.get("articles", [])

    if not isinstance(articles, list):
        raise ValueError("Unexpected GDELT articles format")

    return select_independent_leads(
        articles,
        original_url,
        max_results,
    )


def discover(
    candidates: list[Candidate],
    max_results: int,
) -> None:
    """Print possible supporting sources without saving them."""

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
                candidate.title,
                candidate.original_url,
                max_results=max_results,
            )

        except (httpx.HTTPError, ValueError) as exc:
            print(
                "Search failed:",
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
            "\nThese links must be inspected before "
            "being accepted as supporting evidence."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover possible independent movie sources"
    )

    parser.add_argument(
        "--candidate-id",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Maximum number of candidates (1-6)",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum search results per candidate (1-25)",
    )

    args = parser.parse_args()

    # Avoid accidentally making a burst of requests
    # when the provider recommends a low request rate.
    if args.limit != 1:
        parser.error(
            "This initial version supports one candidate "
            "per execution to avoid rapid API requests."
        )

    candidates = load_candidates(
        limit=args.limit,
        candidate_id=args.candidate_id,
    )

    if not candidates:
        print("No matching unverified candidates.")
        return

    discover(
        candidates,
        max_results=args.max_results,
    )


if __name__ == "__main__":
    main()
