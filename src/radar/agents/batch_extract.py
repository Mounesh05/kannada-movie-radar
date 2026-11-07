
import argparse
import os
from collections import Counter

from dotenv import load_dotenv

from radar.agents.movie_extractor import extract_movie
from radar.database.extraction_attempts import (
    get_pending_articles,
    save_extraction_attempt,
)
from radar.database.movie_candidates import (
    get_candidate_for_article,
    save_movie_candidate,
)

load_dotenv()


def run_batch(
    limit: int = 3,
    execute: bool = False,
    retry_failed: bool = False,
) -> Counter:
    """Preview or process a bounded batch of articles."""

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    articles = get_pending_articles(
        limit=limit,
        retry_failed=retry_failed,
    )

    counts = Counter()

    print("\nKannada Movie Radar — Batch Extraction")
    print("Mode:", "RUN" if execute else "PREVIEW")
    print(f"Model: {model_name}")
    print(f"Articles selected: {len(articles)}")

    if not execute:
        for article_id, title in articles:
            print(f"\nArticle ID: {article_id}")
            print(f"Title: {title}")

        print("\nNo Gemini requests were made.")
        print("No database records were modified.")
        return counts

    for article_id, title in articles:
        print(f"\nProcessing article {article_id}")

        try:
            existing = get_candidate_for_article(article_id)

            if existing is not None:
                print("Skipped: candidate already exists")
                counts["skipped"] += 1
                continue

            extraction = extract_movie(title)

            if (
                not extraction.movie_title
                or not extraction.movie_title.strip()
                or not extraction.evidence
            ):
                save_extraction_attempt(
                    article_id=article_id,
                    model_name=model_name,
                    status="no_candidate",
                )
                print("No usable movie candidate")
                counts["no_candidate"] += 1
                continue

            candidate_id, inserted = save_movie_candidate(
                article_id=article_id,
                extraction=extraction,
                input_title=title,
                model_name=model_name,
            )

            status = "saved" if inserted else "duplicate"

            save_extraction_attempt(
                article_id=article_id,
                candidate_id=candidate_id,
                model_name=model_name,
                status=status,
            )

            counts[status] += 1

            print(f"Candidate ID: {candidate_id}")
            print(f"Result: {status}")
            print("Verification: UNVERIFIED")

        except Exception as exc:
            error_type = type(exc).__name__
            counts["failed"] += 1

            print(f"Article {article_id} failed: {error_type}")

            try:
                save_extraction_attempt(
                    article_id=article_id,
                    model_name=model_name,
                    status="failed",
                    error_type=error_type,
                )
            except Exception:
                print(
                    "Warning: failure could not "
                    "be recorded in PostgreSQL"
                )

    print("\n========== BATCH SUMMARY ==========")
    print(f"Selected: {len(articles)}")

    for status in (
        "saved",
        "duplicate",
        "no_candidate",
        "skipped",
        "failed",
    ):
        print(f"{status}: {counts[status]}")

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch movie extraction using Gemini"
    )

    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")

    args = parser.parse_args()

    if not 1 <= args.limit <= 10:
        parser.error("--limit must be between 1 and 10")

    run_batch(
        limit=args.limit,
        execute=args.run,
        retry_failed=args.retry_failed,
    )


if __name__ == "__main__":
    main()
