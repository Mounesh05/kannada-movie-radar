
import pytest

from radar.services.claim_review_policy import (
    validate_claim,
    validate_review,
)


def test_valid_release_date():
    validate_claim(
        "release_date",
        "2026-12-18",
        "day",
        "https://example.com/announcement",
        "Officially announced theatrical date",
    )


def test_unknown_precision_allowed():
    validate_claim(
        "release_date",
        "2025-01-01T00:00:00Z",
        "unknown",
        "https://www.wikidata.org/wiki/Q133062777",
        "Source-reported date; precision not established",
    )


def test_invalid_day_date():
    with pytest.raises(ValueError):
        validate_claim(
            "release_date",
            "2026-02-30",
            "day",
            "https://example.com/movie",
            "Date reported",
        )


def test_missing_excerpt():
    with pytest.raises(ValueError):
        validate_claim(
            "release_date",
            "2026-12-18",
            "day",
            "https://example.com/movie",
            "",
        )


def test_valid_release_window():
    validate_claim(
        "release_window",
        "Q4 2027",
        None,
        "https://example.com/news",
        "Film reportedly targeting late 2027",
    )


def test_release_window_rejects_precision():
    with pytest.raises(ValueError):
        validate_claim(
            "release_window",
            "Q4 2027",
            "day",
            "https://example.com/news",
            "Reported target window",
        )


def test_valid_review():
    validate_review(
        "unverified",
        "supported",
        "local-developer",
        "Checked original source and movie identity",
        True,
    )


def test_review_requires_source_inspection():
    with pytest.raises(ValueError):
        validate_review(
            "unverified",
            "supported",
            "local-developer",
            "Not actually checked",
            False,
        )


def test_cannot_reapprove_rejected_claim():
    with pytest.raises(ValueError):
        validate_review(
            "rejected",
            "supported",
            "local-developer",
            "Attempted reversal",
            True,
        )


def test_cannot_repeat_same_status():
    with pytest.raises(ValueError):
        validate_review(
            "supported",
            "supported",
            "local-developer",
            "No actual change",
            True,
        )
