
import re
from dataclasses import dataclass
from typing import Literal

from radar.services.text_cleaner import clean_text

Status = Literal[
    "relevant",
    "needs_review",
    "not_relevant",
]

KANNADA_TERMS = (
    "ಕನ್ನಡ ಸಿನಿಮಾ",
    "ಕನ್ನಡ ಚಿತ್ರ",
    "ಕನ್ನಡ ಚಲನಚಿತ್ರ",
    "ಸ್ಯಾಂಡಲ್‌ವುಡ್",
    "ಸ್ಯಾಂಡಲ್ ವುಡ್",
    "kannada film",
    "kannada movie",
    "sandalwood",
)

OTHER_LANGUAGE_TERMS = (
    "ಮಲಯಾಳಂ ಸಿನಿಮಾ",
    "ಮಲಯಾಳಂ ಚಿತ್ರ",
    "ತಮಿಳು ಸಿನಿಮಾ",
    "ತಮಿಳು ಚಿತ್ರ",
    "ತೆಲುಗು ಸಿನಿಮಾ",
    "ತೆಲುಗು ಚಿತ್ರ",
    "ಹಿಂದಿ ಸಿನಿಮಾ",
    "ಹಿಂದಿ ಚಿತ್ರ",
    "malayalam film",
    "malayalam movie",
    "tamil film",
    "tamil movie",
    "telugu film",
    "telugu movie",
    "hindi film",
    "hindi movie",
)


@dataclass(frozen=True)
class Classification:
    status: Status
    reason: str


def contains_term(text: str, term: str) -> bool:
    """Find a complete term rather than an English substring."""
    pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
    return re.search(pattern, text) is not None


def classify_article(title: str) -> Classification:
    """Conservatively classify a movie-news title."""

    normalized = clean_text(title).casefold()

    if not normalized:
        return Classification(
            "needs_review",
            "Empty article title",
        )

    kannada = [
        term for term in KANNADA_TERMS
        if contains_term(normalized, term)
    ]

    other = [
        term for term in OTHER_LANGUAGE_TERMS
        if contains_term(normalized, term)
    ]

    if kannada and other:
        return Classification(
            "needs_review",
            "Multiple film-language indicators detected",
        )

    if kannada:
        return Classification(
            "relevant",
            f"Kannada cinema indicator: {kannada[0]}",
        )

    if other:
        return Classification(
            "not_relevant",
            f"Other-language indicator: {other[0]}",
        )

    return Classification(
        "needs_review",
        "Insufficient evidence in article title",
    )
