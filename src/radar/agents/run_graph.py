
import argparse

from radar.agents.movie_graph import build_movie_graph
from radar.database.connection import get_connection


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Kannada Movie Radar LangGraph workflow"
    )

    parser.add_argument(
        "--article-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute Gemini extraction and database writes",
    )

    args = parser.parse_args()

    if args.article_id <= 0:
        parser.error("--article-id must be positive")

    if not args.run:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT title, classification_status
                    FROM articles
                    WHERE id = %s
                    """,
                    (args.article_id,),
                )
                article = cursor.fetchone()

        if article is None:
            raise SystemExit("Article not found")

        print("\nMode: PREVIEW")
        print(f"Article ID: {args.article_id}")
        print(f"Title: {article[0]}")
        print(f"Stored classification: {article[1]}")
        print("No Gemini requests or database changes.")
        return

    workflow = build_movie_graph()

    result = workflow.invoke(
        {"article_id": args.article_id}
    )

    print("\n========== GRAPH RESULT ==========")
    print(f"Article ID: {result['article_id']}")
    print(f"Classification: {result['classification']}")
    print(f"Outcome: {result.get('outcome', 'skipped')}")
    print(f"Reason: {result.get('reason', 'N/A')}")

    if result.get("candidate_id") is not None:
        print(f"Candidate ID: {result['candidate_id']}")
        print("Verification: NOT AUTOMATICALLY VERIFIED")

    if result.get("error_type"):
        print(f"Error type: {result['error_type']}")


if __name__ == "__main__":
    main()
