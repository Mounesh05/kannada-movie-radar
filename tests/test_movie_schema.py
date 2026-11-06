
import pytest
from pydantic import ValidationError

from radar.agents.movie_schema import MovieExtraction


def test_valid_movie_extraction():
    result = MovieExtraction(
        movie_title=None,
        film_language=None,
        is_kannada_film="unknown",
        release_date=None,
        mentioned_people=[],
        evidence=[],
        needs_review=True,
    )

    assert result.is_kannada_film == "unknown"


def test_invalid_movie_language_status():
    with pytest.raises(ValidationError):
        MovieExtraction(
            movie_title=None,
            film_language=None,
            is_kannada_film="maybe",
            release_date=None,
            mentioned_people=[],
            evidence=[],
            needs_review=True,
        )
