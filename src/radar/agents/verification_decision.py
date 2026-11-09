
"""Evidence-backed movie verification readiness decisions.

Read-only decision support. Never automatically approves,
rejects, or changes a movie candidate.
"""

import argparse
from dataclasses import dataclass

from radar.database.movie_verification import get_verification_report


@dataclass(frozen=True)
class VerificationDecision:
    status: str
    reasons: tuple[str, ...]
    independent_hosts: int
    evidence_count: int


def evaluate_candidate(report: dict) -> VerificationDecision:
    """Evaluate readiness using existing verification policy."""

    status = report["verification_status"]
    language = report["is_kannada_film"]
    evidence = report["sources"]
    eligibility = report["eligibility"]

    reasons: list[str] = []

    if status != "unverified":
        return VerificationDecision(
            status="ALREADY_REVIEWED",
            reasons=(f"Existing verification status: {status}",),
            independent_hosts=eligibility.independent_hosts,
            evidence_count=len(evidence),
        )

    if language != "yes":
        reasons.append(
            "Kannada film identity is not confirmed "
            f"(current value: {language})."
        )

    if not eligibility.eligible:
        reasons.extend(eligibility.reasons)

    if reasons:
        return VerificationDecision(
            status="NEEDS_MORE_EVIDENCE",
            reasons=tuple(reasons),
            independent_hosts=eligibility.independent_hosts,
            evidence_count=len(evidence),
        )

    return VerificationDecision(
        status="READY_FOR_HUMAN_REVIEW",
        reasons=(
            "Minimum independent-source coverage satisfied.",
            "The supporting pages and factual claims must "
            "still be inspected by a human reviewer.",
        ),
        independent_hosts=eligibility.independent_hosts,
        evidence_count=len(evidence),
    )


def run(candidate_id: int) -> None:
    if candidate_id <= 0:
        raise ValueError("Candidate ID must be positive")

    report = get_verification_report(candidate_id)
    decision = evaluate_candidate(report)

    print("\nKANNADA MOVIE RADAR")
    print("PHASE 4.10G — VERIFICATION DECISION")
    print("=" * 55)

    print("Candidate ID:", candidate_id)
    print("Movie:", report["movie_title"])
    print("Kannada identity:", report["is_kannada_film"])
    print("Current status:", report["verification_status"])
    print("Evidence records:", decision.evidence_count)
    print("External source hosts:", decision.independent_hosts)

    print("\nDECISION:", decision.status)

    for reason in decision.reasons:
        print("-", reason)

    if decision.status == "READY_FOR_HUMAN_REVIEW":
        print(
            "\nThis is only a readiness assessment. "
            "It does not verify the factual claims."
        )

    print("\nNo database records were modified.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess movie verification readiness"
    )

    parser.add_argument(
        "--candidate-id",
        type=int,
        required=True,
    )

    args = parser.parse_args()
    run(args.candidate_id)


if __name__ == "__main__":
    main()
