
import argparse

from radar.database.claim_review import (
    add_source_claim,
    review_source_claim,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add and review movie source claims"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    add = commands.add_parser("add")
    add.add_argument("--movie-id", type=int, required=True)
    add.add_argument(
        "--type",
        choices=["release_date", "release_window"],
        required=True,
    )
    add.add_argument("--value", required=True)
    add.add_argument(
        "--precision",
        choices=["day", "month", "year", "quarter", "unknown"],
    )
    add.add_argument("--source-name", required=True)
    add.add_argument("--source-url", required=True)
    add.add_argument("--excerpt", required=True)
    add.add_argument("--release-kind")
    add.add_argument("--territory")

    review = commands.add_parser("review")
    review.add_argument("--claim-id", type=int, required=True)
    review.add_argument(
        "--decision",
        choices=["supported", "disputed", "rejected"],
        required=True,
    )
    review.add_argument("--reviewer", required=True)
    review.add_argument("--note", required=True)
    review.add_argument(
        "--sources-checked",
        action="store_true",
    )

    args = parser.parse_args()

    if args.command == "add":
        claim_id, created = add_source_claim(
            movie_id=args.movie_id,
            claim_type=args.type,
            value=args.value,
            precision=args.precision,
            source_name=args.source_name,
            source_url=args.source_url,
            excerpt=args.excerpt,
            release_kind=args.release_kind,
            territory=args.territory,
        )

        print(f"Claim ID: {claim_id}")
        print(f"Created: {created}")
        print("No claim was automatically verified.")
        return

    review_source_claim(
        claim_id=args.claim_id,
        decision=args.decision,
        reviewer=args.reviewer,
        note=args.note,
        sources_checked=args.sources_checked,
    )

    print(f"Claim review recorded: {args.decision}")
    print("Canonical movie facts were not changed.")


if __name__ == "__main__":
    main()
