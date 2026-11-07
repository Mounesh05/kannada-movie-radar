
import pytest

from radar.collectors.wikidata_collector import (
    build_query,
    parse_movies,
)


def make_row(
    qid: str,
    title: str,
    release: str | None = None,
) -> dict:
    row = {
        "film": {
            "value": f"http://www.wikidata.org/entity/{qid}",
        },
        "filmLabel": {
            "value": title,
        },
    }

    if release is not None:
        row["releaseDate"] = {
            "value": release,
        }

    return row


def test_query_filters_kannada_movies():
    query = build_query(limit=20, from_year=2025)

    assert "wd:Q33673" in query
    assert "wdt:P364" in query
    assert "2025-01-01" in query
    assert "LIMIT 20" in query


def test_invalid_limit():
    with pytest.raises(ValueError):
        build_query(limit=0)


def test_parse_movie_record():
    data = {
        "results": {
            "bindings": [
                make_row(
                    "Q12345",
                    "Example Film",
                    "2025-01-01T00:00:00Z",
                ),
            ],
        },
    }

    movies = parse_movies(data)

    assert len(movies) == 1
    assert movies[0]["wikidata_id"] == "Q12345"
    assert movies[0]["title"] == "Example Film"
    assert movies[0]["original_language"] == "kn"
    assert (
        movies[0]["reported_release_date"]
        == "2025-01-01T00:00:00Z"
    )


def test_duplicate_wikidata_id_removed():
    data = {
        "results": {
            "bindings": [
                make_row("Q12345", "Example Film"),
                make_row("Q12345", "Example Film"),
            ],
        },
    }

    movies = parse_movies(data)

    assert len(movies) == 1


def test_invalid_wikidata_id_skipped():
    data = {
        "results": {
            "bindings": [
                make_row("INVALID", "Unknown Film"),
            ],
        },
    }

    assert parse_movies(data) == []


def test_missing_title_skipped():
    data = {
        "results": {
            "bindings": [
                make_row("Q12345", "Q12345"),
            ],
        },
    }

    assert parse_movies(data) == []
