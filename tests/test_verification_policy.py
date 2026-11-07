
import pytest

from radar.services.verification_policy import (
    evaluate_evidence,
    source_host,
)

ORIGINAL = "https://news.example.com/original-film-story"


def test_source_hostname():
    assert source_host("https://www.example.org/movie") == "example.org"


def test_reject_http_source():
    with pytest.raises(ValueError):
        source_host("http://example.org/movie")


def test_reject_local_hostname():
    with pytest.raises(ValueError):
        source_host("https://localhost/movie")


def test_missing_independent_sources():
    result = evaluate_evidence(
        ORIGINAL,
        [
            (
                "https://source-one.example.org/film",
                "identity",
            ),
        ],
    )

    assert result.eligible is False
    assert result.independent_hosts == 1


def test_missing_language_claim():
    result = evaluate_evidence(
        ORIGINAL,
        [
            ("https://source-one.example.org/film", "identity"),
            ("https://source-two.example.net/film", "identity"),
        ],
    )

    assert result.eligible is False
    assert "Film language evidence missing" in result.reasons


def test_complete_evidence_package():
    result = evaluate_evidence(
        ORIGINAL,
        [
            ("https://source-one.example.org/film", "identity"),
            ("https://source-two.example.net/film", "language"),
        ],
    )

    assert result.eligible is True
    assert result.independent_hosts == 2


def test_original_source_not_counted():
    result = evaluate_evidence(
        ORIGINAL,
        [
            ("https://news.example.com/another-story", "identity"),
            ("https://source-two.example.net/film", "language"),
        ],
    )

    assert result.eligible is False
    assert result.independent_hosts == 1
