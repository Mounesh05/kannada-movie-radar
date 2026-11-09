
from datetime import datetime

from radar.database.connection import get_connection
from radar.services.article_classifier import Status


def save_article(
    source_name: str,
    feed_url: str,
    title: str,
    article_url: str,
    published_at: datetime | None = None,
    classification_status: Status = "needs_review",
    classification_reason: str | None = None,
) -> bool:
    """Save an article and its classification in PostgreSQL.

    Returns:
        True if a new article was inserted.
        False if its URL already exists.
    """

    if not all(
        [
            source_name.strip(),
            feed_url.strip(),
            title.strip(),
            article_url.strip(),
        ]
    ):
        raise ValueError(
            "Required article fields cannot be empty"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:

            # Create the source if it does not exist.
            # Otherwise update its displayed name.
            cursor.execute(
                """
                INSERT INTO sources (
                    name,
                    feed_url
                )
                VALUES (%s, %s)
                ON CONFLICT (feed_url)
                DO UPDATE SET
                    name = EXCLUDED.name
                RETURNING id
                """,
                (
                    source_name,
                    feed_url,
                ),
            )

            source_id = cursor.fetchone()[0]

            # Insert the article with classification.
            # The unique URL prevents duplicates.
            cursor.execute(
                """
                INSERT INTO articles (
                    source_id,
                    title,
                    url,
                    published_at,
                    classification_status,
                    classification_reason
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (url)
                DO NOTHING
                RETURNING id
                """,
                (
                    source_id,
                    title,
                    article_url,
                    published_at,
                    classification_status,
                    classification_reason,
                ),
            )


            inserted_article = cursor.fetchone()

            if inserted_article is None:
                # URL already exists; do not generate a duplicate event.
                return False

            article_id = inserted_article[0]

            # Store the raw-article event in the same transaction.
            # The consumer will perform deeper relevance checks.
            cursor.execute(
                """
                INSERT INTO event_outbox (
                    event_type,
                    aggregate_id,
                    topic,
                    payload,
                    status,
                    attempts
                )
                VALUES (
                    'article.collected.v1',
                    %s,
                    'radar.articles.collected.v1',
                    jsonb_build_object(
                        'schema_version', 1,
                        'article_id', %s
                    ),
                    'pending',
                    0
                )
                ON CONFLICT (event_type, aggregate_id)
                DO NOTHING
                """,
                (article_id, article_id),
            )

            return True





def get_recent_articles(
    limit: int = 10,
) -> list[tuple]:
    """Retrieve recently collected articles."""

    if not 1 <= limit <= 100:
        raise ValueError(
            "Limit must be between 1 and 100"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    s.name AS source_name,
                    a.classification_status,
                    a.classification_reason,
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


def get_articles_by_classification(
    status: Status,
    limit: int = 20,
) -> list[tuple]:
    """Retrieve articles with a specific classification."""

    if not 1 <= limit <= 100:
        raise ValueError(
            "Limit must be between 1 and 100"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    s.name AS source_name,
                    a.classification_reason,
                    a.collected_at
                FROM articles AS a
                JOIN sources AS s
                    ON a.source_id = s.id
                WHERE a.classification_status = %s
                ORDER BY
                    a.collected_at DESC,
                    a.id DESC
                LIMIT %s
                """,
                (
                    status,
                    limit,
                ),
            )

            return cursor.fetchall()
