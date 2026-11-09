
"""Publish PostgreSQL outbox events to Kafka.

Run:
    python -m radar.kafka.outbox_publisher --limit 10

Delivery guarantee: at least once.
Consumers must be idempotent.
"""

import argparse
import json
import os

from kafka import KafkaProducer

from radar.database.connection import get_connection

EVENT_TYPE = "article.collected.v1"
TOPIC = "radar.articles.collected.v1"


def create_producer() -> KafkaProducer:
    """Create a Kafka producer that waits for broker acknowledgements."""
    bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "127.0.0.1:9092",
    )

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(","),
        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False,
        ).encode("utf-8"),
        key_serializer=lambda key: str(key).encode("utf-8"),
        acks="all",
        retries=0,
        max_block_ms=5000,
        request_timeout_ms=15000,
    )


def publish_one(producer: KafkaProducer) -> str:
    """Publish one pending event with PostgreSQL row locking.

    Returns 'published', 'failed', or 'empty'.
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    aggregate_id,
                    topic,
                    payload
                FROM event_outbox
                WHERE status = 'pending'
                  AND event_type = %s
                  AND topic = %s
                ORDER BY id
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """,
                (EVENT_TYPE, TOPIC),
            )

            row = cursor.fetchone()

            if row is None:
                return "empty"

            event_id, article_id, topic, payload = row

            # Defensive validation: never publish a malformed
            # event or an event pointing to a different article.
            if (
                not isinstance(payload, dict)
                or payload.get("article_id") != article_id
            ):
                cursor.execute(
                    """
                    UPDATE event_outbox
                    SET attempts = attempts + 1
                    WHERE id = %s
                    """,
                    (event_id,),
                )
                print(f"Invalid payload for event {event_id}")
                return "failed"

            try:
                future = producer.send(
                    topic,
                    key=article_id,
                    value={
                        **payload,
                        "outbox_event_id": event_id,
                        "event_type": EVENT_TYPE,
                    },
                )

                # Waiting for acknowledgement is essential.
                metadata = future.get(timeout=20)

            except Exception as exc:
                # Keep status pending so this event can be retried.
                cursor.execute(
                    """
                    UPDATE event_outbox
                    SET attempts = attempts + 1
                    WHERE id = %s
                    """,
                    (event_id,),
                )

                print(
                    f"Kafka delivery failed for event "
                    f"{event_id}: {exc}"
                )
                return "failed"

            cursor.execute(
                """
                UPDATE event_outbox
                SET
                    status = 'published',
                    attempts = attempts + 1,
                    published_at = NOW()
                WHERE id = %s
                """,
                (event_id,),
            )

            print(
                f"Published event {event_id} "
                f"to {metadata.topic}, "
                f"partition={metadata.partition}, "
                f"offset={metadata.offset}"
            )

            return "published"


def run_publisher(limit: int = 10) -> None:
    """Publish a bounded number of pending events."""

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    producer = create_producer()

    published = 0
    failed = 0

    try:
        for _ in range(limit):
            result = publish_one(producer)

            if result == "empty":
                break

            if result == "published":
                published += 1
            else:
                failed += 1

                # Avoid retrying the same failed event
                # repeatedly within this invocation.
                break

    finally:
        producer.close(timeout=5)

    print("\nOUTBOX PUBLISHER SUMMARY")
    print(f"Published: {published}")
    print(f"Failed: {failed}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish PostgreSQL outbox events to Kafka",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum events per invocation (1-100)",
    )

    args = parser.parse_args()

    run_publisher(limit=args.limit)


if __name__ == "__main__":
    main()
