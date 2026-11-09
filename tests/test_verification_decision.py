
"""Tests for evidence-backed verification readiness."""

from types import SimpleNamespace

from radar.agents.verification_decision import evaluate_candidate


def make_report(
    language="unknown",
    status="unverified",
    eligible=False,
    hosts=0,
    reasons=None,
    sources=None,
):
    if reasons is None:
        reasons = ["Insufficient independent evidence"]

    if sources is None:
        sources = []

    return {
        "verification_status": status,
        "is_kannada_film": language,
        "sources": sources,
        "eligibility": SimpleNamespace(
            eligible=eligible,
            independent_hosts=hosts,
            reasons=reasons,
        ),
    }


def test_unknown_language_needs_more_evidence():
    decision = evaluate_candidate(make_report())

    assert decision.status == "NEEDS_MORE_EVIDENCE"


def test_missing_independent_sources():
    decision = evaluate_candidate(
        make_report(
            language="yes",
            eligible=False,
            hosts=1,
        )
    )

    assert decision.status == "NEEDS_MORE_EVIDENCE"


def test_valid_coverage_is_review_ready():
    decision = evaluate_candidate(
        make_report(
            language="yes",
            eligible=True,
            hosts=2,
            reasons=[],
            sources=[
                ("https://source-a.com", "identity"),
                ("https://source-b.com", "language"),
            ],
        )
    )

    assert decision.status == "READY_FOR_HUMAN_REVIEW"
    assert decision.independent_hosts == 2


def test_reviewed_candidate_is_not_reprocessed():
    decision = evaluate_candidate(
        make_report(
            language="yes",
            status="verified",
            eligible=True,
            hosts=2,
            reasons=[],
        )
    )

    assert decision.status == "ALREADY_REVIEWED"


def test_rejected_candidate_is_final():
    decision = evaluate_candidate(
        make_report(status="rejected")
    )

    assert decision.status == "ALREADY_REVIEWED"


def test_language_not_confirmed_blocks_readiness():
    decision = evaluate_candidate(
        make_report(
            language="unknown",
            eligible=True,
            hosts=2,
            reasons=[],
        )
    )

    assert decision.status == "NEEDS_MORE_EVIDENCE"
