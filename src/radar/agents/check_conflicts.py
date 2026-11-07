
import argparse

from radar.database.claim_conflicts import (
    get_release_conflict_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect conflicting movie release dates"
    )

    parser.add_argument(
        "--movie-id",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    if args.movie_id <= 0:
        parser.error("--movie-id must be positive")

    title, report = get_release_conflict_report(
        args.movie_id
    )

    print("\n========== RELEASE CLAIM REPORT ==========")
    print(f"Movie ID: {args.movie_id}")
    print(f"Movie: {title}")
    print(f"Status: {report.status}")
    print(f"Reason: {report.reason}")

    for claim in report.claims:
        print(f"\nClaim ID: {claim.claim_id}")
        print(f"Date value: {claim.value}")
        print(f"Precision: {claim.precision or 'unknown'}")
        print(f"Source: {claim.source_name}")
        print(f"URL: {claim.source_url}")

    print("\nRead-only report. No database changes.")


if __name__ == "__main__":
    main()
