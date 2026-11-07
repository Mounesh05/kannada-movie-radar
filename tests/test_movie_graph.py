
from unittest.mock import MagicMock, patch

from radar.agents.movie_graph import build_movie_graph
from radar.agents.movie_schema import MovieExtraction


def fake_article_database(title):
    connection = MagicMock()
    cursor = MagicMock()

    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = (
        title,
        "https://example.com/movie",
    )

    return connection


def sample_extraction():
    return MovieExtraction(
        movie_title="Example Film",
        film_language="Kannada",
        is_kannada_film="yes",
        release_date=None,
        mentioned_people=[],
        evidence=["Kannada movie"],
        needs_review=False,
    )


def test_non_kannada_article_skips_gemini():
    connection = fake_article_database(
        "New Tamil movie announced"
    )

    with (
        patch(
            "radar.agents.movie_graph.get_connection",
            return_value=connection,
        ),
        patch(
            "radar.agents.movie_graph.extract_movie"
        ) as extractor,
    ):
        result = build_movie_graph().invoke(
            {"article_id": 1}
        )

    assert result["classification"] == "not_relevant"
    extractor.assert_not_called()


def test_existing_candidate_skips_gemini():
    connection = fake_article_database(
        "New Kannada movie announced"
    )

    with (
        patch(
            "radar.agents.movie_graph.get_connection",
            return_value=connection,
        ),
        patch(
            "radar.agents.movie_graph.get_candidate_for_article",
            return_value=(5, "Example Film", "unverified"),
        ),
        patch(
            "radar.agents.movie_graph.extract_movie"
        ) as extractor,
    ):
        result = build_movie_graph().invoke(
            {"article_id": 2}
        )

    assert result["outcome"] == "existing"
    assert result["candidate_id"] == 5
    extractor.assert_not_called()


def test_successful_movie_extraction():
    connection = fake_article_database(
        "Kannada movie Example Film announced"
    )

    with (
        patch(
            "radar.agents.movie_graph.get_connection",
            return_value=connection,
        ),
        patch(
            "radar.agents.movie_graph.get_candidate_for_article",
            return_value=None,
        ),
        patch(
            "radar.agents.movie_graph.extract_movie",
            return_value=sample_extraction(),
        ),
        patch(
            "radar.agents.movie_graph.save_movie_candidate",
            return_value=(20, True),
        ) as save_candidate,
        patch(
            "radar.agents.movie_graph.save_extraction_attempt"
        ) as log_attempt,
    ):
        result = build_movie_graph().invoke(
            {"article_id": 3}
        )

    assert result["outcome"] == "saved"
    assert result["candidate_id"] == 20
    save_candidate.assert_called_once()
    assert log_attempt.call_args.kwargs["status"] == "saved"


def test_unsupported_evidence_is_not_saved():
    connection = fake_article_database(
        "Kannada movie announced"
    )

    extraction = sample_extraction()
    extraction.evidence = ["Evidence not in headline"]

    with (
        patch(
            "radar.agents.movie_graph.get_connection",
            return_value=connection,
        ),
        patch(
            "radar.agents.movie_graph.get_candidate_for_article",
            return_value=None,
        ),
        patch(
            "radar.agents.movie_graph.extract_movie",
            return_value=extraction,
        ),
        patch(
            "radar.agents.movie_graph.save_movie_candidate"
        ) as save_candidate,
        patch(
            "radar.agents.movie_graph.save_extraction_attempt"
        ) as log_attempt,
    ):
        result = build_movie_graph().invoke(
            {"article_id": 4}
        )

    assert result["outcome"] == "no_candidate"
    save_candidate.assert_not_called()
    assert (
        log_attempt.call_args.kwargs["status"]
        == "no_candidate"
    )


def test_gemini_error_is_logged():
    connection = fake_article_database(
        "Kannada movie announced"
    )

    with (
        patch(
            "radar.agents.movie_graph.get_connection",
            return_value=connection,
        ),
        patch(
            "radar.agents.movie_graph.get_candidate_for_article",
            return_value=None,
        ),
        patch(
            "radar.agents.movie_graph.extract_movie",
            side_effect=RuntimeError("Temporary API error"),
        ),
        patch(
            "radar.agents.movie_graph.save_extraction_attempt"
        ) as log_attempt,
    ):
        result = build_movie_graph().invoke(
            {"article_id": 5}
        )

    assert result["outcome"] == "failed"
    assert result["error_type"] == "RuntimeError"
    assert log_attempt.call_args.kwargs["status"] == "failed"
