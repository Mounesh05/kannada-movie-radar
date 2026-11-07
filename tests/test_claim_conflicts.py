
from radar.services.claim_conflicts import (
    ReleaseClaim,
    detect_release_conflicts,
)


def claim(
    claim_id: int,
    value: str,
    precision: str = "day",
) -> ReleaseClaim:
    return ReleaseClaim(
        claim_id=claim_id,
        value=value,
        precision=precision,
        source_name=f"Source {claim_id}",
        source_url=f"https://source{claim_id}.example/movie",
    )


def test_no_evidence():
    result = detect_release_conflicts([])

    assert result.status == "no_evidence"


def test_single_source():
    result = detect_release_conflicts(
        [claim(1, "2025-01-01", "unknown")]
    )

    assert result.status == "single_source"


def test_matching_dates():
    result = detect_release_conflicts(
        [
            claim(1, "2026-04-30"),
            claim(2, "2026-04-30"),
        ]
    )

    assert result.status == "consistent_values"


def test_different_exact_dates():
    result = detect_release_conflicts(
        [
            claim(1, "2026-04-30"),
            claim(2, "2026-05-15"),
        ]
    )

    assert result.status == "possible_conflict"


def test_unknown_precision():
    result = detect_release_conflicts(
        [
            claim(1, "2025-01-01", "unknown"),
            claim(2, "2027-10-01", "day"),
        ]
    )

    assert result.status == "needs_precision_review"


def test_invalid_date():
    result = detect_release_conflicts(
        [
            claim(1, "not-a-date"),
            claim(2, "2026-04-30"),
        ]
    )

    assert result.status == "needs_precision_review"
