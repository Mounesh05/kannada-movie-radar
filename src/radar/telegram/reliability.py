
"""Collection heartbeat monitoring and recovery diagnostics."""

import argparse
import os
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from radar.database.connection import get_connection
from radar.telegram.failure_alert import send_alert

IST = ZoneInfo("Asia/Kolkata")


def record_success() -> None:
    """Record a completed cloud collection run."""

    run_id = os.getenv("GITHUB_RUN_ID", "").strip()
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1").strip()

    if not run_id or not run_id.isdigit():
        raise RuntimeError(
            "A valid GITHUB_RUN_ID is required."
        )

    if not attempt.isdigit():
        raise RuntimeError(
            "Invalid GITHUB_RUN_ATTEMPT."
        )

    run_key = f"{run_id}:{attempt}"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collector_runs (github_run_key)
                VALUES (%s)
                ON CONFLICT (github_run_key)
                DO NOTHING
                RETURNING id
                """,
                (run_key,),
            )

            inserted = cur.fetchone() is not None

    if inserted:
        print("PASS: Collection heartbeat recorded.")
    else:
        print("Collection heartbeat already recorded.")


def check_collection() -> list[str]:
    """Detect missing successful collection on the current IST day."""

    if os.getenv("COLLECTION_ENABLED", "").lower() != "true":
        print("Daily collection monitoring disabled.")
        return []

    now = datetime.now(timezone.utc).astimezone(IST)

    today_start = datetime.combine(
        now.date(),
        time.min,
        tzinfo=IST,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT MAX(completed_at)
                FROM collector_runs
                """
            )
            latest = cur.fetchone()[0]

    if latest:
        print(
            "Last successful collection:",
            latest.astimezone(IST).isoformat(),
        )
    else:
        print("No successful collection heartbeat recorded.")

    if latest and latest >= today_start:
        print("PASS: Collection completed today (IST).")
        return []

    return [
        "No successful daily collection recorded "
        f"for {now.date()} (IST). "
        "Check the collector workflow in GitHub Actions."
    ]


def inspect_deliveries() -> None:
    """Display uncertain Telegram deliveries without modifying them."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, week_start_ist, claimed_at
                FROM telegram_digest_deliveries
                WHERE status = 'sending'
                ORDER BY claimed_at
                """
            )
            rows = cur.fetchall()

    if not rows:
        print("PASS: No uncertain Telegram deliveries.")
        return

    print("UNCERTAIN TELEGRAM DELIVERIES")

    for delivery_id, week_start, claimed_at in rows:
        print(
            f"ID={delivery_id} "
            f"week={week_start} "
            f"claimed={claimed_at}"
        )

    print(
        "Do not automatically retry these deliveries. "
        "Check the Telegram chat and GitHub logs first."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kannada Movie Radar reliability checks"
    )

    parser.add_argument(
        "command",
        choices=["record", "check", "deliveries"],
    )

    parser.add_argument(
        "--send",
        action="store_true",
        help="Send collection alerts to Telegram",
    )

    args = parser.parse_args()

    if args.command == "record":
        record_success()
        return

    if args.command == "deliveries":
        inspect_deliveries()
        return

    alerts = check_collection()

    if not alerts:
        return

    for alert in alerts:
        print("WARNING:", alert)

    if args.send:
        message = "\n".join(
            [
                "⚠️ Kannada Movie Radar",
                "Missed Daily Collection",
                "",
                *alerts,
            ]
        )
        send_alert(message)
        print("PASS: Collection alert delivered.")
    else:
        print("Preview only. No alert sent.")


if __name__ == "__main__":
    main()
