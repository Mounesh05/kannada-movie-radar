
import argparse

from radar.database.movie_matching import (
    find_candidate_matches,
    review_movie_match,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review movie identity matches"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    suggest = commands.add_parser("suggest")
    suggest.add_argument("--candidate-id", type=int, required=True)

    review = commands.add_parser("review")
    review.add_argument("--candidate-id", type=int, required=True)
    review.add_argument("--movie-id", type=int, required=True)
    review.add_argument(
        "--decision",
        choices=["approved", "rejected"],
        required=True,
    )
    review.add_argument("--reviewer", required=True)
    review.add_argument("--note", required=True)

    args = parser.parse_args()

    if args.command == "suggest":
        report = find_candidate_matches(args.candidate_id)

        print("\nCandidate:", report["title"])
        print("Result:", report["reason"])

        for item in report["suggestions"]:
            print(
                f"Movie ID: {item.movie_id} | "
                f"{item.movie_title} | "
                f"score={item.score:.3f} | "
                f"{item.match_type}"
            )
        return

    review_movie_match(
        candidate_id=args.candidate_id,
        movie_id=args.movie_id,
        decision=args.decision,
        reviewer=args.reviewer,
        note=args.note,
    )

    print(f"Match decision recorded: {args.decision}")
    print("No movie metadata or verification status changed.")


if __name__ == "__main__":
    main()
