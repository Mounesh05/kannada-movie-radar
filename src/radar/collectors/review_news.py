
import argparse
from datetime import datetime, timezone

from radar.database.connection import get_connection
from radar.services.news_categorizer import categorize_news
from radar.services.verification_policy import source_host


def list_pending() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    n.id,
                    a.id,
                    n.category,
                    a.title,
                    mc.id,
                    mc.verification_status
                FROM news_events n
                JOIN articles a ON a.id = n.article_id
                LEFT JOIN movie_candidates mc
                    ON mc.article_id = a.id
                WHERE n.review_status = 'pending'
                ORDER BY a.published_at DESC NULLS LAST
                LIMIT 100
            """)

            for row in cur.fetchall():
                print(
                    f"Event={row[0]} Article={row[1]} "
                    f"Category={row[2]} Candidate={row[4]} "
                    f"CandidateStatus={row[5]}\n"
                    f"  {row[3]}"
                )


def review(
    event_id: int,
    decision: str,
    reviewer: str,
    note: str,
    candidate_id: int | None = None,
    supporting_url: str | None = None,
    duplicate_of: int | None = None,
) -> None:
    if event_id <= 0:
        raise ValueError("Invalid event ID")

    if not reviewer.strip() or not note.strip():
        raise ValueError("Reviewer and note are required")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    n.review_status,
                    n.category,
                    a.id,
                    a.url,
                    a.title
                FROM news_events n
                JOIN articles a ON a.id = n.article_id
                WHERE n.id = %s
                FOR UPDATE OF n
            """, (event_id,))

            event = cur.fetchone()

            if event is None:
                raise ValueError("News event not found")

            status, category, article_id, article_url, title = event

            if status != "pending":
                raise ValueError("Event already reviewed")

            if decision == "approve":
                if not candidate_id or not supporting_url:
                    raise ValueError(
                        "Approval requires candidate ID and supporting URL"
                    )

                if category == "other":
                    raise ValueError("Other content cannot be approved")

                if categorize_news(title).category != category:
                    raise ValueError(
                        "Article category no longer passes news rules"
                    )

                if source_host(article_url) == source_host(supporting_url):
                    raise ValueError(
                        "Supporting evidence must be independent"
                    )

                cur.execute("""
                    SELECT verification_status, is_kannada_film
                    FROM movie_candidates
                    WHERE id = %s AND article_id = %s
                """, (candidate_id, article_id))

                candidate = cur.fetchone()

                if candidate != ("verified", "yes"):
                    raise ValueError(
                        "Candidate must be independently verified "
                        "as a Kannada film"
                    )

                cur.execute("""
                    UPDATE news_events
                    SET review_status = 'approved',
                        evidence_label = 'verified',
                        movie_candidate_id = %s,
                        supporting_url = %s,
                        reviewer = %s,
                        review_note = %s,
                        reviewed_at = %s
                    WHERE id = %s
                """, (
                    candidate_id,
                    supporting_url,
                    reviewer,
                    note,
                    datetime.now(timezone.utc),
                    event_id,
                ))

            elif decision == "duplicate":
                if not duplicate_of or duplicate_of == event_id:
                    raise ValueError("Specify another event")

                cur.execute("""
                    SELECT review_status
                    FROM news_events
                    WHERE id = %s
                """, (duplicate_of,))

                target = cur.fetchone()

                if target != ("approved",):
                    raise ValueError(
                        "Duplicate target must be an approved event"
                    )

                cur.execute("""
                    UPDATE news_events
                    SET review_status = 'duplicate',
                        duplicate_of_event_id = %s,
                        reviewer = %s,
                        review_note = %s,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (duplicate_of, reviewer, note, event_id))

            elif decision == "reject":
                cur.execute("""
                    UPDATE news_events
                    SET review_status = 'rejected',
                        reviewer = %s,
                        review_note = %s,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (reviewer, note, event_id))

            else:
                raise ValueError("Unsupported decision")

    print(f"PASS: Event {event_id} -> {decision}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")

    for action in ("approve", "reject", "duplicate"):
        command = sub.add_parser(action)
        command.add_argument("--event", type=int, required=True)
        command.add_argument("--reviewer", required=True)
        command.add_argument("--note", required=True)

        if action == "approve":
            command.add_argument("--candidate", type=int, required=True)
            command.add_argument("--source", required=True)

        if action == "duplicate":
            command.add_argument("--duplicate-of", type=int, required=True)

    args = parser.parse_args()

    if args.command == "list":
        list_pending()
    else:
        review(
            event_id=args.event,
            decision=args.command,
            reviewer=args.reviewer,
            note=args.note,
            candidate_id=getattr(args, "candidate", None),
            supporting_url=getattr(args, "source", None),
            duplicate_of=getattr(args, "duplicate_of", None),
        )


if __name__ == "__main__":
    main()
