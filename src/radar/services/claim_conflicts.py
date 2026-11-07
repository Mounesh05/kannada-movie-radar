
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ReleaseClaim:
    claim_id: int
    value: str
    precision: str | None
    source_name: str
    source_url: str


@dataclass(frozen=True)
class ConflictReport:
    status: str
    reason: str
    claims: list[ReleaseClaim]


def normalized_date(value: str) -> str | None:
    """Extract a valid ISO calendar date without inferring precision."""

    try:
        parsed = date.fromisoformat(value[:10])
    except ValueError:
        return None

    return parsed.isoformat()


def detect_release_conflicts(
    claims: list[ReleaseClaim],
) -> ConflictReport:
    """Compare claims without automatically resolving them."""

    if not claims:
        return ConflictReport(
            status="no_evidence",
            reason="No release-date claims available",
            claims=[],
        )

    if len(claims) == 1:
        return ConflictReport(
            status="single_source",
            reason="Only one release-date claim recorded",
            claims=claims,
        )

    values = {
        normalized_date(claim.value)
        for claim in claims
    }

    # Malformed values must never count as agreement.
    if None in values:
        return ConflictReport(
            status="needs_precision_review",
            reason="At least one date is not a valid ISO date",
            claims=claims,
        )

    if len(values) == 1:
        return ConflictReport(
            status="consistent_values",
            reason=(
                "Reported date values agree; "
                "release type and source reliability remain unchecked"
            ),
            claims=claims,
        )

    if any(claim.precision != "day" for claim in claims):
        return ConflictReport(
            status="needs_precision_review",
            reason=(
                "Different dates reported, but at least one "
                "claim lacks confirmed day precision"
            ),
            claims=claims,
        )

    return ConflictReport(
        status="possible_conflict",
        reason=(
            "Different exact dates reported; verify release "
            "type, territory and publication chronology"
        ),
        claims=claims,
    )
