
from radar.database.connection import get_connection
from radar.services.news_categorizer import categorize_news


def backfill_news_events(
    limit: int = 100,
    save: bool = False,
) -> dict:
    """Backfill eligible articles into the event/outbox tables.

    Preview is the default. Writes are atomic per invocation.
    """

    if not 1 <= limit <= 1000:
        raise ValueError("Limit must be between 1 and 1000")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.classification_status
                FROM articles AS a
              WHERE a.classification_status = 'relevant'
  AND a.url <> 'https://example.com/movie-news'
                AND NOT EXISTS (
                    SELECT 1
                    FROM news_events AS n
                    WHERE n.article_id = a.id
                )
                ORDER BY a.id
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()
            created = 0
            preview = []

            for article_id, title, relevance in rows:
                result = categorize_news(title)

                label = (
                    "unconfirmed"
                    if relevance == "relevant"
                    else "under_review"
                )

                preview.append(
                    {
                        "article_id": article_id,
                        "title": title,
                        "category": result.category,
                        "evidence_label": label,
                    }
                )

                if not save:
                    continue

                cursor.execute(
                    """
                    INSERT INTO news_events (
                        article_id,
                        category,
                        evidence_label,
                        category_method,
                        first_seen_at
                    )
                    SELECT
                        id, %s, %s, 'rules_v1', collected_at
                    FROM articles
                    WHERE id = %s
                    ON CONFLICT (article_id)
                    DO NOTHING
                    RETURNING id
                    """,
                    (
                        result.category,
                        label,
                        article_id,
                    ),
                )

                inserted = cursor.fetchone()

                if inserted is None:
                    continue

                event_id = inserted[0]

                cursor.execute(
                    """
                    INSERT INTO event_outbox (
                        event_type,
                        aggregate_id,
                        topic,
                        payload
                    )
                    VALUES (
                        'news.collected.v1',
                        %s,
                        'radar.news.collected.v1',
                        jsonb_build_object(
                            'schema_version', 1,
                            'event_id', %s,
                            'article_id', %s,
                            'category', %s,
                            'evidence_label', %s
                        )
                    )
                    ON CONFLICT (
                        event_type, aggregate_id
                    )
                    DO NOTHING
                    """,
                    (
                        event_id,
                        event_id,
                        article_id,
                        result.category,
                        label,
                    ),
                )

                created += 1

    return {
        "eligible": len(rows),
        "created": created,
        "preview": preview,
        "saved": save,
    }
