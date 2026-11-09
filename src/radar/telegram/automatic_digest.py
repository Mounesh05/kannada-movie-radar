
"""Automatic weekly RSS news digest for Kannada Movie Radar.

No manual verification or approval is required.
Stories are clearly presented as source-reported headlines.
"""

import argparse
from datetime import timedelta

from radar.database.connection import get_connection
from radar.telegram.sunday_digest import (
    MAX_MESSAGE_LENGTH,
    last_completed_week,
    send_digest,
)


def get_weekly_articles(start, end):
    """Read collected, potentially relevant RSS headlines."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.title,
                    a.url,
                    s.name
                FROM articles AS a
                JOIN sources AS s
                  ON s.id = a.source_id
                WHERE a.published_at >= %s
                  AND a.published_at < %s
                  AND a.classification_status IN (
                      'relevant',
                      'needs_review'
                  )
                ORDER BY a.published_at DESC, a.id DESC
                LIMIT 200
                """,
                (start, end),
            )
            return cur.fetchall()


def format_weekly_digest(start, end, articles):
    """Build a plain-text Telegram digest within message limits."""

    end_date = (end - timedelta(days=1)).date()

    lines = [
        "🎬 Kannada Movie Radar",
        "Weekly Kannada Cinema Updates",
        f"{start.date()} to {end_date} (IST)",
        "",
    ]

    footer = (
        "Source-reported headlines, not independently "
        "verified. Open the original links for details."
    )

    if not articles:
        lines.append("No new collected cinema headlines this week.")
        lines.append("")
        lines.append(footer)
        return "\n".join(lines)

    included = 0

    for title, url, source in articles:
        item = (
            f"{included + 1}. {title}\n"
            f"Source: {source}\n"
            f"{url}\n"
        )

        proposed = "\n".join(
            [*lines, item, footer]
        )

        if len(proposed) > MAX_MESSAGE_LENGTH:
            break

        lines.append(item)
        included += 1

    omitted = len(articles) - included

    if omitted:
        note = f"{omitted} additional headlines omitted."
        if len("\n".join([*lines, note, footer])) <= MAX_MESSAGE_LENGTH:
            lines.append(note)

    lines.append(footer)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Automatic weekly Kannada movie news digest"
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the digest to Telegram",
    )
    args = parser.parse_args()

    start, end = last_completed_week()
    articles = get_weekly_articles(start, end)

    message = format_weekly_digest(
        start,
        end,
        articles,
    )

    print("Week:", start.date(), "to", end.date())
    print("Matching collected headlines:", len(articles))
    print("\n" + message)

    if args.send:
        # Reuses the existing delivery ledger to prevent
        # duplicate sends for the same completed week.
        send_digest(start, end, message)
    else:
        print("\nPreview only. No Telegram message sent.")


if __name__ == "__main__":
    main()
