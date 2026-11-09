
import argparse
import os
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx

from radar.database.connection import get_connection

IST = ZoneInfo("Asia/Kolkata")
MAX_MESSAGE_LENGTH = 3900


def last_completed_week(now=None):
    """Return the last completed Sunday-Saturday week in IST."""
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(IST)

    days_since_sunday = (local.weekday() + 1) % 7
    this_sunday = local.date() - timedelta(
        days=days_since_sunday
    )

    end = datetime.combine(this_sunday, time.min, IST)
    start = end - timedelta(days=7)

    return start, end


def get_approved_news(start, end):
    """Get only approved, verified Kannada film news."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    n.id,
                    a.title,
                    a.url,
                    n.category,
                    mc.movie_title
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
                ORDER BY a.published_at DESC, n.id DESC
                """,
                (start, end),
            )
            return cur.fetchall()


def format_digest(start, end, articles):
    """Build a Telegram-safe plain-text weekly digest."""
    last_day = (end - timedelta(days=1)).date()

    lines = [
        "🎬 Kannada Movie Radar",
        "Weekly Kannada Film News",
        f"{start.date()} to {last_day} (IST)",
        "",
    ]

    if not articles:
        return "\n".join(
            lines + ["No verified Kannada film updates this week."]
        )

    included = 0

    for event_id, title, url, category, movie in articles:
        item = (
            f"{included + 1}. [{category.upper()}] {movie}\n"
            f"{title}\n"
            f"{url}\n"
        )

        candidate = "\n".join(
            lines + [item, "Only reviewed, verified news."]
        )

        if len(candidate) > MAX_MESSAGE_LENGTH:
            break

        lines.append(item)
        included += 1

    omitted = len(articles) - included

    if omitted:
        lines.append(f"{omitted} additional items omitted.")

    lines.append("Only reviewed, verified news.")

    message = "\n".join(lines)

    if len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError("Digest exceeds Telegram length limit")

    return message


def send_digest(start, end, message):
    """Send a digest and track delivery in Neon PostgreSQL."""

    # Remove accidental whitespace/newlines from GitHub secrets.
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is missing")

    # Reject malformed secret values before claiming the delivery.
    if any(char.isspace() for char in token):
        raise ValueError(
            "TELEGRAM_BOT_TOKEN contains internal whitespace"
        )

    if not chat_id.lstrip("-").isdigit():
        raise ValueError("TELEGRAM_CHAT_ID must be numeric")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telegram_digest_deliveries (
                    chat_id,
                    week_start_ist,
                    week_end_ist,
                    status
                )
                VALUES (%s, %s, %s, 'sending')
                ON CONFLICT (chat_id, week_start_ist)
                DO NOTHING
                RETURNING id
                """,
                (
                    chat_id,
                    start.date(),
                    end.date(),
                ),
            )
            row = cur.fetchone()

    if row is None:
        print(
            "Delivery already claimed or completed. "
            "Skipping duplicate send."
        )
        return

    delivery_id = row[0]

    # No automatic retry after an ambiguous network failure.
    # Telegram might have accepted the message already.
    response = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            "Telegram rejected the digest message"
        )

    message_id = data["result"]["message_id"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE telegram_digest_deliveries
                SET status = 'sent',
                    sent_at = CURRENT_TIMESTAMP,
                    telegram_message_id = %s
                WHERE id = %s
                  AND status = 'sending'
                """,
                (message_id, delivery_id),
            )

    print("PASS: Sunday digest sent")


def main():
    parser = argparse.ArgumentParser(
        description="Kannada Movie Radar Sunday Telegram Digest"
    )

    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the digest to Telegram",
    )

    args = parser.parse_args()

    start, end = last_completed_week()
    articles = get_approved_news(start, end)
    message = format_digest(start, end, articles)

    print("Eligible verified events:", len(articles))
    print("Week:", start.date(), "to", end.date())

    print("\nDIGEST PREVIEW\n")
    print(message)

    if not args.send:
        print("\nPreview only. No Telegram message sent.")
        return

    if not articles:
        print("No verified events. Nothing sent.")
        return

    send_digest(start, end, message)


if __name__ == "__main__":
    main()
