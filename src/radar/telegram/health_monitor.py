
"""Read-only health monitoring for Kannada Movie Radar."""

import argparse
import os
from datetime import datetime, timezone

from radar.database.connection import get_connection
from radar.telegram.failure_alert import send_alert
from radar.telegram.sunday_digest import last_completed_week


def check_health() -> tuple[list[str], list[str]]:
    """Return informational metrics and actionable alerts."""
    metrics = []
    alerts = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT CURRENT_TIMESTAMP")
            now = cur.fetchone()[0]

            # Pending news awaiting human approval.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM news_events
                WHERE review_status = 'pending'
                """
            )
            pending = cur.fetchone()[0]
            metrics.append(f"Pending news reviews: {pending}")

            # Old reviews deserve attention, not auto-approval.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM news_events
                WHERE review_status = 'pending'
                  AND first_seen_at < %s
                """,
                (now.replace(tzinfo=timezone.utc)
                 if now.tzinfo is None else now,),
            )
            # The query above only checks pending status and
            # existing timestamps. Age is checked below instead.
            # Re-query using database interval arithmetic.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM news_events
                WHERE review_status = 'pending'
                  AND first_seen_at <
                      CURRENT_TIMESTAMP - INTERVAL '48 hours'
                """
            )
            old_pending = cur.fetchone()[0]

            if old_pending:
                alerts.append(
                    f"{old_pending} news events pending "
                    "review for over 48 hours"
                )

            # Unverified movie candidates.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM movie_candidates
                WHERE verification_status = 'unverified'
                """
            )
            unverified = cur.fetchone()[0]
            metrics.append(
                f"Unverified movie candidates: {unverified}"
            )

            # Failed extraction attempts are informational;
            # historical failures alone should not break a run.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM extraction_attempts
                WHERE status = 'failed'
                """
            )
            failed = cur.fetchone()[0]
            metrics.append(
                f"Recorded failed extraction attempts: {failed}"
            )

            # Detect old Telegram delivery claims.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM telegram_digest_deliveries
                WHERE status = 'sending'
                  AND claimed_at <
                      CURRENT_TIMESTAMP - INTERVAL '1 hour'
                """
            )
            stuck = cur.fetchone()[0]
            metrics.append(f"Stuck Telegram deliveries: {stuck}")

            if stuck:
                alerts.append(
                    f"{stuck} Telegram digest deliveries "
                    "stuck in 'sending' for over 1 hour"
                )

            # Confirm last completed week's digest was sent.
            # Only alert if there was at least one eligible
            # verified event and Sunday delivery was enabled.
            if os.getenv("DIGEST_ENABLED", "").lower() == "true":
                start, end = last_completed_week(
                    datetime.now(timezone.utc)
                )

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM news_events AS n
                    JOIN articles AS a
                      ON a.id = n.article_id
                    JOIN movie_candidates AS mc
                      ON mc.id = n.movie_candidate_id
                     AND mc.article_id = a.id
                    WHERE n.review_status = 'approved'
                      AND n.evidence_label = 'verified'
                      AND n.duplicate_of_event_id IS NULL
                      AND n.category <> 'other'
                      AND n.supporting_url IS NOT NULL
                      AND mc.verification_status = 'verified'
                      AND mc.is_kannada_film = 'yes'
                      AND a.published_at >= %s
                      AND a.published_at < %s
                    """,
                    (start, end),
                )
                eligible = cur.fetchone()[0]
                metrics.append(
                    f"Last completed week eligible events: {eligible}"
                )

                if eligible:
                    chat_id = os.getenv(
                        "TELEGRAM_CHAT_ID", ""
                    ).strip()

                    if chat_id:
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM telegram_digest_deliveries
                            WHERE chat_id = %s
                              AND week_start_ist = %s
                              AND status = 'sent'
                            """,
                            (chat_id, start.date()),
                        )
                        sent = cur.fetchone()[0]

                        if not sent:
                            alerts.append(
                                "No confirmed Telegram delivery "
                                f"for week starting {start.date()}"
                            )

    return metrics, alerts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send Telegram only when problems are detected",
    )
    args = parser.parse_args()

    metrics, alerts = check_health()

    print("KANNADA MOVIE RADAR HEALTH REPORT")
    for metric in metrics:
        print(metric)

    if not alerts:
        print("PASS: No actionable health alerts")
        return

    print("\nATTENTION REQUIRED")
    for item in alerts:
        print(f"- {item}")

    if not args.send:
        print("\nPreview mode: no Telegram alert sent")
        return

    message = "\n".join(
        [
            "⚠️ Kannada Movie Radar — Health Alert",
            "",
            *[f"• {item}" for item in alerts],
            "",
            "Check Neon and GitHub Actions.",
        ]
    )

    send_alert(message)


if __name__ == "__main__":
    main()
