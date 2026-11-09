
from datetime import date

from radar.services.verification_policy import source_host

ALLOWED_PRECISIONS = {
    "day",
    "month",
    "year",
    "quarter",
    "unknown",
}

ALLOWED_CLAIM_TYPES = {
    "release_date",
    "release_window",
}

ALLOWED_REVIEW_STATUSES = {
    "supported",
    "disputed",
    "rejected",
}

ALLOWED_TRANSITIONS = {
    "unverified": ALLOWED_REVIEW_STATUSES,
    "supported": {"disputed", "rejected"},
    "disputed": {"supported", "rejected"},
    "rejected": set(),
}


def validate_claim(
    claim_type: str,
    value: str,
    precision: str | None,
    source_url: str,
    excerpt: str,
) -> None:
    """Validate evidence metadata without verifying its truth."""

    if claim_type not in ALLOWED_CLAIM_TYPES:
        raise ValueError("Unsupported claim type")

    if not value.strip():
        raise ValueError("Claim value is required")

    if not excerpt.strip():
        raise ValueError("Supporting source excerpt is required")

    source_host(source_url)

    if claim_type == "release_date":
        if precision not in ALLOWED_PRECISIONS:
            raise ValueError("Release-date precision is required")

        if precision == "day":
            try:
                parsed = date.fromisoformat(value.strip())
            except ValueError as exc:
                raise ValueError(
                    "Day-precision date must be YYYY-MM-DD"
                ) from exc

            if parsed.isoformat() != value.strip():
                raise ValueError(
                    "Day-precision date must be YYYY-MM-DD"
                )

    elif precision is not None:
        raise ValueError(
            "Release windows must not use date_precision"
        )


def validate_review(
    current_status: str,
    new_status: str,
    reviewer: str,
    note: str,
    sources_checked: bool,
) -> None:
    """Require a conscious, auditable review decision."""

    if not reviewer.strip() or not note.strip():
        raise ValueError("Reviewer and reason are required")

    if not sources_checked:
        raise ValueError(
            "Reviewer must confirm source inspection"
        )

    allowed = ALLOWED_TRANSITIONS.get(current_status)

    if allowed is None or new_status not in allowed:
        raise ValueError(
            "Invalid claim-status transition"
        )
