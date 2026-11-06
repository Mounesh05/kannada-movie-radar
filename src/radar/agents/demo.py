
import argparse

from radar.agents.movie_extractor import extract_movie
from radar.database.connection import get_connection


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test Gemini movie extraction"
    )
    parser.add_argument("--article-id", type=int, required=True)
    args = parser.parse_args()

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
            row = cursor.fetchone()

    if row is None:
        raise SystemExit("Article not found")

    title, url = row

    print(f"Article: {title}")
    print(f"Source: {url}")

    result = extract_movie(title)

    print("\nGemini extraction:")
    print(result.model_dump_json(indent=2))

    print("\nStatus: UNVERIFIED")
    print("No database records were modified.")


if __name__ == "__main__":
    main()
