
from datetime import datetime

from radar.database.connection import get_connection


def save_article(
    source_name: str,
    feed_url: str,
    title: str,
    article_url: str,
    published_at: datetime | None = None,
) -> bool:
    """Save an article and its source.

    Returns True when a new article was inserted,
    or False when its URL already exists.
    """
    if not all([
        source_name.strip(),
        feed_url.strip(),
        title.strip(),
        article_url.strip(),
    ]):
        raise ValueError("Required article fields are missing")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sources (name, feed_url)
                VALUES (%s, %s)
                ON CONFLICT (feed_url)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                (source_name, feed_url),
            )

            source_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO articles (
                    source_id,
                    title,
                    url,
                    published_at
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING id
                """,
                (
                    source_id,
                    title,
                    article_url,
                    published_at,
                ),
            )

            return cursor.fetchone() is not None


def get_recent_articles(limit: int = 10) -> list[tuple]:
    """Retrieve recently collected articles."""

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    s.name,
                    a.collected_at
                FROM articles AS a
                JOIN sources AS s
                    ON a.source_id = s.id
                ORDER BY
                    a.collected_at DESC,
                    a.id DESC
                LIMIT %s
                """,
                (limit,),
            )

            return cursor.fetchall()
