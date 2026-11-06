
import html
import unicodedata


def clean_text(value: str | None) -> str:
    """Clean RSS metadata while preserving Unicode text."""
    if not value:
        return ""

    decoded = html.unescape(value)
    normalized = unicodedata.normalize("NFC", decoded)

    return " ".join(normalized.split())
