
import argparse

from radar.collectors.wikidata_collector import (
    collect_wikidata_movies,
)
from radar.database.catalogue_importer import save_wikidata_movies


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Kannada film metadata from Wikidata"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--from-year",
        type=int,
        default=2025,
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Write records to PostgreSQL",
    )

    args = parser.parse_args()

    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")

    if not 1900 <= args.from_year <= 2100:
        parser.error("--from-year must be between 1900 and 2100")

    movies = collect_wikidata_movies(
        limit=args.limit,
        from_year=args.from_year,
    )

    print("\n========== WIKIDATA MOVIE IMPORT ==========")
    print(f"Movies retrieved: {len(movies)}")
    print(f"Starting year: {args.from_year}")

    for movie in movies:
        print(
            f"\n{movie['wikidata_id']} "
            f"{movie['title']}"
        )
        print(
            "Source-reported release:",
            movie["reported_release_date"] or "Unknown",
        )

    if not args.save:
        print("\nPREVIEW ONLY — No database changes.")
        return

    stats = save_wikidata_movies(movies)

    print("\n========== IMPORT SUMMARY ==========")
    print(f"New movies: {stats['new_movies']}")
    print(f"Existing movies: {stats['existing_movies']}")
    print(f"New claims: {stats['new_claims']}")
    print("Release verification: NOT AUTOMATIC")


if __name__ == "__main__":
    main()
