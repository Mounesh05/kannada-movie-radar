
from unittest.mock import MagicMock, patch

import pytest

from radar.agents.movie_schema import MovieExtraction
from radar.database.movie_candidates import (
    get_candidate_for_article,
    save_movie_candidate,
)


def sample_extraction(
    movie_title: str | None = "ಕಾಥಲ್",
    evidence: list[str] | None = None,
) -> MovieExtraction:
    return MovieExtraction(
        movie_title=movie_title,
        film_language="Malayalam",
        is_kannada_film="no",
        release_date=None,
        mentioned_people=["ಮುಮ್ಮಟ್ಟಿ"],
        evidence=(
            ["ಮಲಯಾಳಂ ಸಿನಿಮಾ"]
            if evidence is None
            else evidence
        ),
        needs_review=False,
    )


def fake_database():
    connection = MagicMock()
    cursor = MagicMock()

    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    return connection, cursor


def test_save_new_candidate():
    connection, cursor = fake_database()
    cursor.fetchone.return_value = (42,)

    with patch(
        "radar.database.movie_candidates.get_connection",
        return_value=connection,
    ):
        candidate_id, inserted = save_movie_candidate(
            article_id=7,
            extraction=sample_extraction(),
            input_title="ಮಲಯಾಳಂ ಸಿನಿಮಾ ಕಾಥಲ್",
            model_name="gemini-test-model",
        )

    assert candidate_id == 42
    assert inserted is True
    assert cursor.execute.call_count == 1


def test_duplicate_candidate_not_overwritten():
    connection, cursor = fake_database()

    cursor.fetchone.side_effect = [
        None,  # INSERT ... RETURNING id
        (42,),  # SELECT existing candidate
    ]

    with patch(
        "radar.database.movie_candidates.get_connection",
        return_value=connection,
    ):
        candidate_id, inserted = save_movie_candidate(
            article_id=7,
            extraction=sample_extraction(),
            input_title="ಮಲಯಾಳಂ ಸಿನಿಮಾ ಕಾಥಲ್",
            model_name="gemini-test-model",
        )

    assert candidate_id == 42
    assert inserted is False
    assert cursor.execute.call_count == 2


def test_missing_movie_title_is_rejected():
    with pytest.raises(ValueError):
        save_movie_candidate(
            article_id=7,
            extraction=sample_extraction(movie_title=None),
            input_title="Unknown article",
            model_name="gemini-test-model",
        )


def test_missing_evidence_is_rejected():
    with pytest.raises(ValueError):
        save_movie_candidate(
            article_id=7,
            extraction=sample_extraction(evidence=[]),
            input_title="Movie article",
            model_name="gemini-test-model",
        )


def test_get_existing_candidate():
    connection, cursor = fake_database()
    cursor.fetchone.return_value = (
        42, "ಕಾಥಲ್", "unverified"
    )

    with patch(
        "radar.database.movie_candidates.get_connection",
        return_value=connection,
    ):
        result = get_candidate_for_article(7)

    assert result == (42, "ಕಾಥಲ್", "unverified")


def test_invalid_article_id():
    with pytest.raises(ValueError):
        get_candidate_for_article(0)
