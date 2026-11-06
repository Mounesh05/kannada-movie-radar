
import argparse
import os

from dotenv import load_dotenv

from radar.agents.movie_extractor import extract_movie
from radar.database.connection import get_connection
from radar.database.movie_candidates import (
    get_candidate_for_article,
    save_movie_candidate,
)

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract and optionally store a movie candidate"
    )

    parser.add_argument(
        "--article-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the extracted candidate in PostgreSQL",
    )

    args = parser.parse_args()

    if args.article_id <= 0:
        parser.error("--article-id must be positive")

    # Avoid a duplicate Gemini request.
    existing = get_candidate_for_article(args.article_id)

    if existing is not None:
        candidate_id, movie_title, status = existing

        print("Candidate already stored.")
        print(f"Candidate ID: {candidate_id}")
        print(f"Movie: {movie_title}")
        print(f"Verification: {status}")
        print("No Gemini request or database update performed.")
        return

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT title, url
                FROM articles
                WHERE id = %s
                """,
                (args.article_id,),
            )

            article = cursor.fetchone()

    if article is None:
        raise SystemExit("Article not found")

    title, url = article

    print(f"\nArticle: {title}")
    print(f"Source: {url}")

    print("\nSending article title to Gemini...")

    extraction = extract_movie(title)

    print("\nAI extraction:")
    print(extraction.model_dump_json(indent=2))

    print("\nVerification: UNVERIFIED")

    if not extraction.movie_title:
        print("\nNo identifiable movie title.")
        print("Candidate not saved.")
        return

    if not extraction.evidence:
        print("\nNo source evidence returned.")
        print("Candidate not saved.")
        return

    if not args.save:
        print("\nPreview only. No database records modified.")
        print("Run with --save to persist this candidate.")
        return

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    candidate_id, inserted = save_movie_candidate(
        article_id=args.article_id,
        extraction=extraction,
        input_title=title,
        model_name=model_name,
    )

    print("\n========== DATABASE RESULT ==========")
    print(f"Candidate ID: {candidate_id}")
    print(f"Inserted: {inserted}")
    print("Verification: UNVERIFIED")


if __name__ == "__main__":
    main()
