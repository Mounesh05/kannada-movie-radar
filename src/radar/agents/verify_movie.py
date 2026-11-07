
import argparse

from radar.database.movie_verification import (
    add_movie_evidence,
    get_verification_report,
    review_movie_candidate,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review evidence for movie candidates"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    report = commands.add_parser("report")
    report.add_argument("--candidate-id", type=int, required=True)

    add = commands.add_parser("add")
    add.add_argument("--candidate-id", type=int, required=True)
    add.add_argument("--url", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--excerpt", required=True)
    add.add_argument(
        "--claim",
        choices=["identity", "language", "release"],
        required=True,
    )

    review = commands.add_parser("review")
    review.add_argument("--candidate-id", type=int, required=True)
    review.add_argument(
        "--decision",
        choices=["verified", "rejected"],
        required=True,
    )
    review.add_argument("--reviewer", required=True)
    review.add_argument("--note", required=True)
    review.add_argument(
        "--sources-checked",
        action="store_true",
        help="Confirm that the supporting pages were inspected",
    )

    args = parser.parse_args()

    if args.command == "add":
        evidence_id = add_movie_evidence(
            candidate_id=args.candidate_id,
            source_url=args.url,
            source_title=args.title,
            excerpt=args.excerpt,
            claim_type=args.claim,
        )

        print(
            f"Evidence ID: {evidence_id}"
            if evidence_id is not None
            else "Evidence already exists"
        )
        return

    if args.command == "review":
        review_movie_candidate(
            candidate_id=args.candidate_id,
            decision=args.decision,
            reviewer=args.reviewer,
            note=args.note,
            sources_checked=args.sources_checked,
        )

        print(f"Decision recorded: {args.decision}")
        return

    result = get_verification_report(args.candidate_id)

    print(f"\nMovie: {result['movie_title']}")
    print(f"Kannada: {result['is_kannada_film']}")
    print(f"Status: {result['verification_status']}")
    print(f"Original source: {result['original_url']}")

    print("\nSupporting evidence:")
    for url, claim, title, excerpt in result["sources"]:
        print(f"\nClaim: {claim}")
        print(f"Source: {title}")
        print(f"URL: {url}")
        print(f"Excerpt: {excerpt}")

    eligibility = result["eligibility"]

    print("\nEligible for human review:", eligibility.eligible)
    print("External source hosts:", eligibility.independent_hosts)

    for reason in eligibility.reasons:
        print(f"- {reason}")

    if eligibility.eligible:
        print(
            "Eligibility does not mean that claims are verified. "
            "Inspect all source pages before approval."
        )


if __name__ == "__main__":
    main()
