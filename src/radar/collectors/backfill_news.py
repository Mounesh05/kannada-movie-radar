
import argparse

from radar.database.news_events import backfill_news_events


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill categorized movie news events"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Write events and outbox entries to PostgreSQL",
    )

    args = parser.parse_args()

    report = backfill_news_events(
        limit=args.limit,
        save=args.save,
    )

    for item in report["preview"]:
        print(
            f"{item['article_id']} | "
            f"{item['category']} | "
            f"{item['evidence_label']} | "
            f"{item['title']}"
        )

    print("\nEligible:", report["eligible"])
    print("Created:", report["created"])

    if args.save:
        print("Database event and outbox records saved.")
    else:
        print("PREVIEW ONLY — No database changes.")


if __name__ == "__main__":
    main()
