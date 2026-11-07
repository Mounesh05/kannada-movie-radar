
import re
from typing import TypedDict

import httpx

ENDPOINT = "https://query.wikidata.org/sparql"

HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": (
        "KannadaMovieRadar/0.1 "
        "(https://github.com/Mounesh05/kannada-movie-radar)"
    ),
}


class WikidataMovie(TypedDict):
    wikidata_id: str
    title: str
    original_language: str
    source_url: str
    reported_release_date: str | None


def build_query(
    limit: int = 20,
    from_year: int = 2025,
) -> str:
    """Query dated Kannada film records."""

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    if not 1900 <= from_year <= 2100:
        raise ValueError("Invalid starting year")

    return f"""
    SELECT ?film ?filmLabel
           (MAX(?date) AS ?releaseDate)
    WHERE {{
      ?film wdt:P31 wd:Q11424 ;
            wdt:P364 wd:Q33673 ;
            wdt:P577 ?date .

      FILTER(
        ?date >= "{from_year}-01-01T00:00:00Z"^^xsd:dateTime
      )

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en,kn".
      }}
    }}
    GROUP BY ?film ?filmLabel
    ORDER BY DESC(?releaseDate)
    LIMIT {limit}
    """


def parse_movies(data: dict) -> list[WikidataMovie]:
    """Normalize Wikidata SPARQL JSON bindings."""

    rows = data["results"]["bindings"]
    movies = []
    seen = set()

    for row in rows:
        entity_url = row["film"]["value"]
        wikidata_id = entity_url.rsplit("/", 1)[-1]

        if not re.fullmatch(r"Q[1-9][0-9]*", wikidata_id):
            continue

        if wikidata_id in seen:
            continue

        title = row.get("filmLabel", {}).get(
            "value", ""
        ).strip()

        if not title or title == wikidata_id:
            continue

        release = row.get(
            "releaseDate", {}
        ).get("value")

        movies.append(
            {
                "wikidata_id": wikidata_id,
                "title": title,
                "original_language": "kn",
                "source_url": (
                    f"https://www.wikidata.org/wiki/{wikidata_id}"
                ),
                "reported_release_date": release,
            }
        )

        seen.add(wikidata_id)

    return movies


def collect_wikidata_movies(
    limit: int = 20,
    from_year: int = 2025,
) -> list[WikidataMovie]:
    """Retrieve film metadata; do not verify release claims."""

    response = httpx.get(
        ENDPOINT,
        params={
            "query": build_query(limit, from_year),
            "format": "json",
        },
        headers=HEADERS,
        timeout=45,
    )

    response.raise_for_status()

    return parse_movies(response.json())
