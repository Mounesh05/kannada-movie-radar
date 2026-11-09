
"""Preview potential independent movie coverage from Bing News RSS.

This module does not verify claims or write to the database.
"""

import argparse
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit, urlunsplit

import feedparser
import httpx

from radar.database.connection import get_connection
from radar.services.verification_policy import source_host

BING_NEWS_URL = "https://www.bing.com/news/search"


@dataclass(frozen=True)
class MovieCandidate:
    id: int
    movie_title: str
    original_url: str


@dataclass(frozen=True)
class EvidenceLead:
    title: str
    url: str
    publisher_host: str
    published: str


def load_candidate(candidate_id: int) -> MovieCandidate:
    """Load one unverified movie candidate from PostgreSQL."""

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

    return MovieCandidate(
        id=row[0],
        movie_title=row[1],
        original_url=row[2],
    )


def publisher_url(raw_url: str) -> str | None:
    """Extract the publisher URL from a Bing News link."""

    try:
        parsed = urlsplit(raw_url.strip())

        if (
            parsed.scheme != "https"
            or not parsed.hostname
        ):
            return None

        host = parsed.hostname.casefold()

        if host in {"bing.com", "www.bing.com"}:
            if parsed.path != "/news/apiclick.aspx":
                return None

            values = parse_qs(parsed.query).get("url")

            if not values:
                return None

            destination = values[0].strip()

        else:
            destination = raw_url.strip()

        # Strip the fragment for more consistent deduplication.
        parts = urlsplit(destination)

        if parts.scheme != "https":
            return None

        if not parts.hostname:
            return None

        source_host(destination)

        if parts.hostname.casefold() in {
            "bing.com",
            "www.bing.com",
        }:
            return None

        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                parts.query,
                "",
            )
        )

    except ValueError:
        return None


def select_leads(
    entries: list,
    original_url: str,
    max_results: int = 10,
) -> list[EvidenceLead]:
    """Keep unique potential independent publisher links."""

    original_host = source_host(original_url)
    seen = set()
    leads = []

    for entry in entries:
        title = str(entry.get("title", "")).strip()
        raw_link = str(entry.get("link", "")).strip()

        if not title or not raw_link:
            continue

        destination = publisher_url(raw_link)

        if destination is None:
            continue

        host = source_host(destination)

        if host == original_host:
            continue

        if destination in seen:
            continue

        seen.add(destination)

        leads.append(
            EvidenceLead(
                title=title,
                url=destination,
                publisher_host=host,
                published=str(
                    entry.get("published", "")
                ),
            )
        )

        if len(leads) >= max_results:
            break

    return leads


def search_bing_news(
    candidate: MovieCandidate,
    max_results: int = 10,
) -> list[EvidenceLead]:
    """Retrieve news-search metadata from Bing's RSS endpoint."""

    if not 1 <= max_results <= 20:
        raise ValueError("max_results must be 1-20")

    title = candidate.movie_title.strip()

    if not title:
        raise ValueError("Movie title is empty")

    params = {
        "q": f'"{title}"',
        "format": "rss",
        "setmkt": "en-IN",
    }

    with httpx.Client(
        timeout=20,
        follow_redirects=False,
        headers={
            "User-Agent": (
                "KannadaMovieRadar/0.1 "
                "(news evidence research)"
            ),
        },
    ) as client:
        response = client.get(
            BING_NEWS_URL,
            params=params,
        )
        response.raise_for_status()

        feed = feedparser.parse(response.content)

    if feed.bozo:
        raise ValueError("Malformed RSS response")

    if not feed.get("version"):
        raise ValueError("Response is not a recognized RSS feed")

    return select_leads(
        feed.entries,
        candidate.original_url,
        max_results,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview independent Bing News source leads"
    )

    parser.add_argument(
        "--candidate-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    candidate = load_candidate(args.candidate_id)

    print("\nKANNADA MOVIE RADAR")
    print("BING NEWS EVIDENCE DISCOVERY")
    print("=" * 55)

    print("Candidate ID:", candidate.id)
    print("Movie:", candidate.movie_title)
    print("Original source:", candidate.original_url)

    try:
        leads = search_bing_news(
            candidate,
            max_results=args.max_results,
        )

    except httpx.HTTPStatusError as exc:
        print(
            "Bing HTTP status:",
            exc.response.status_code,
        )
        print("Search unsuccessful. No evidence verified.")
        return

    except (httpx.RequestError, ValueError) as exc:
        print("Search error:", type(exc).__name__)
        print("No evidence verified.")
        return

    if not leads:
        print("\nNo independent source leads found.")
        print("Movie remains unverified.")
        return

    print("\nPotential source leads:", len(leads))

    for index, lead in enumerate(leads, start=1):
        print("\n" + "-" * 55)
        print(f"{index}. {lead.title}")
        print("Publisher:", lead.publisher_host)
        print("Published:", lead.published)
        print("URL:", lead.url)
        print("Status: UNCHECKED SEARCH RESULT")

    print("\nNo evidence records were saved.")
    print("Movie remains unverified.")
    print(
        "All sources require content inspection and "
        "claim validation before acceptance."
    )


if __name__ == "__main__":
    main()
