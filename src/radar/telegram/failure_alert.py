
"""Telegram failure alerts for Kannada Movie Radar."""

import argparse
import os
import sys

import httpx


def build_message() -> str:
    workflow = os.getenv(
        "GITHUB_WORKFLOW", "Manual test"
    )
    repository = os.getenv(
        "GITHUB_REPOSITORY", "Mounesh05/kannada-movie-radar"
    )
    run_id = os.getenv("GITHUB_RUN_ID", "")
    server = os.getenv(
        "GITHUB_SERVER_URL", "https://github.com"
    )

    lines = [
        "🚨 Kannada Movie Radar — Workflow Failure",
        "",
        f"Workflow: {workflow}",
        f"Repository: {repository}",
    ]

    if run_id:
        lines.append(
            f"Run: {server}/{repository}/actions/runs/{run_id}"
        )

    lines.extend([
        "",
        "Check GitHub Actions logs for details.",
    ])

    return "\n".join(lines)


def send_alert(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        raise RuntimeError("Telegram credentials are missing")

    if any(char.isspace() for char in token):
        raise ValueError("Invalid Telegram token")

    if not chat_id.lstrip("-").isdigit():
        raise ValueError("Invalid Telegram chat ID")

    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )

        response.raise_for_status()

        if not response.json().get("ok"):
            raise RuntimeError("Telegram rejected alert")

    except Exception as exc:
        print(
            f"Alert failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    print("PASS: Failure alert delivered")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    message = build_message()

    if args.send:
        send_alert(message)
    else:
        print("ALERT PREVIEW")
        print(message)


if __name__ == "__main__":
    main()
