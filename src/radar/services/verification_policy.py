
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class VerificationEligibility:
    eligible: bool
    reasons: list[str]
    independent_hosts: int


def source_host(url: str) -> str:
    """Extract a public HTTPS source hostname."""

    parsed = urlsplit(url.strip())

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("A public HTTPS source URL is required")

    host = parsed.hostname.casefold().removeprefix("www.")

    if "." not in host or host.endswith(".local"):
        raise ValueError("A public hostname is required")

    return host


def evaluate_evidence(
    original_url: str,
    evidence: list[tuple[str, str]],
) -> VerificationEligibility:
    """Check evidence coverage, not factual correctness."""

    original_host = source_host(original_url)
    hosts = set()
    claims = set()
    reasons = []

    for url, claim_type in evidence:
        try:
            host = source_host(url)
        except ValueError:
            reasons.append("Invalid source URL")
            continue

        if host == original_host:
            continue

        hosts.add(host)
        claims.add(claim_type)

    if len(hosts) < 2:
        reasons.append(
            "At least two distinct external source hosts required"
        )

    if "identity" not in claims:
        reasons.append("Movie identity evidence missing")

    if "language" not in claims:
        reasons.append("Film language evidence missing")

    return VerificationEligibility(
        eligible=not reasons,
        reasons=reasons,
        independent_hosts=len(hosts),
    )
