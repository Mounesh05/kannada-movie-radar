
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class FreshnessResult:
    status: str
    reason: str


def check_freshness(
    published_at: datetime | None,
    now: datetime | None = None,
    max_age_days: int = 7,
) -> FreshnessResult:
    """Check article age using timezone-aware timestamps."""

    if max_age_days < 1:
        raise ValueError("max_age_days must be positive")

    current = now or datetime.now(timezone.utc)

    if current.tzinfo is None:
        raise ValueError("Current time must be timezone-aware")

    if published_at is None:
        return FreshnessResult(
            "needs_review",
            "Publication date missing",
        )

    if published_at.tzinfo is None:
        return FreshnessResult(
            "needs_review",
            "Publication timezone missing",
        )

    age = current - published_at

    if age < timedelta(minutes=-10):
        return FreshnessResult(
            "needs_review",
            "Publication timestamp is in the future",
        )

    if age > timedelta(days=max_age_days):
        return FreshnessResult(
            "stale",
            "Article is outside the freshness window",
        )

    return FreshnessResult(
        "fresh",
        "Article is within the freshness window",
    )
