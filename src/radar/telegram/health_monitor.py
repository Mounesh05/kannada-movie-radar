
"""Database health monitoring for Kannada Movie Radar."""

import argparse
import os

from radar.database.connection import get_connection
from radar.telegram.failure_alert import send_alert
from radar.telegram.sunday_digest import last_completed_week


def check_health() -> tuple[list[str], list[str]]:
    """Check database health without modifying any records."""

    metrics: list[str] = []
    alerts: list[str] = []

    with get_connection() as conn:
        with conn.cursor() as cur:

            # 1. Count pending news reviews.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM news_events
                WHERE review_status = 'pending'
                """
            )
            pending = cur.fetchone()[0]

            metrics.append(
                f"Pending news reviews: {pending}"
            )

            # 2. Find reviews pending for more than 48 hours.
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

            metrics.append(
                f"Reviews older than 48 hours: {old_pending}"
            )

            if old_pending > 0:
                alerts.append(
                    f"{old_pending} news events have been "
                    "pending review for over 48 hours."
                )

            # 3. Count unverified movie candidates.
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

            # These need evidence review.
            # Never automatically mark them verified.

            # 4. Count failed movie extraction attempts.
            cur.execute(
                """
                SELECT COUNT(*)
                FROM extraction_attempts
                WHERE status = 'failed'
                """
            )
            failed = cur.fetchone()[0]

            metrics.append(
                f"Recorded failed extractions: {failed}"
            )

            # Historical extraction failures alone
            # do not trigger repeated alerts.

            # 5. Detect stuck Telegram deliveries.
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

            metrics.append(
                f"Stuck Telegram deliveries: {stuck}"
            )

            if stuck > 0:
                alerts.append(
                    f"{stuck} Telegram deliveries have "
                    "been stuck in 'sending' for over 1 hour."
                )

            # 6. Check previous week's Sunday digest.
            digest_enabled = (
                os.getenv("DIGEST_ENABLED", "")
                .strip()
                .lower()
                == "true"
            )

            if digest_enabled:
                start, end = last_completed_week()

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
                    "Eligible events in last completed "
                    f"week: {eligible}"
                )

                # Empty weeks are intentionally not sent.
                if eligible > 0:
                    chat_id = os.getenv(
                        "TELEGRAM_CHAT_ID", ""
                    ).strip()

                    if not chat_id:
                        alerts.append(
                            "TELEGRAM_CHAT_ID is missing."
                        )
                    else:
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

                        if sent == 0:
                            alerts.append(
                                "No confirmed Telegram digest "
                                "delivery for the week starting "
                                f"{start.date()}."
                            )

            else:
                metrics.append(
                    "Sunday digest monitoring disabled."
                )

    return metrics, alerts


def build_health_alert(alerts: list[str]) -> str:
    """Format health issues for Telegram."""

    lines = [
        "⚠️ Kannada Movie Radar — Health Alert",
        "",
    ]

    for item in alerts:
        lines.append(f"• {item}")

    lines.extend(
        [
            "",
            "Check Neon PostgreSQL and GitHub Actions.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kannada Movie Radar Health Monitor"
    )

    parser.add_argument(
        "--send",
        action="store_true",
        help="Send health alerts through Telegram",
    )

    args = parser.parse_args()

    metrics, alerts = check_health()

    print("=" * 50)
    print("KANNADA MOVIE RADAR")
    print("DATABASE HEALTH REPORT")
    print("=" * 50)

    for metric in metrics:
        print(metric)

    print("-" * 50)

    if not alerts:
        print("PASS: No actionable health alerts.")
        return

    print("ATTENTION REQUIRED")

    for item in alerts:
        print(f"- {item}")

    if not args.send:
        print(
            "\nPreview mode: "
            "No Telegram alerts sent."
        )
        return

    message = build_health_alert(alerts)
    send_alert(message)

    print("PASS: Health alert sent to Telegram.")


if __name__ == "__main__":
    main()
