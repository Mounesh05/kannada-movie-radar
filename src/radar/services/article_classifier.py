
from dataclasses import dataclass
from typing import Literal

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


def classify_article(title: str) -> Classification:
    """Classify a title using explicit language indicators."""

    normalized = " ".join(title.casefold().split())

    kannada = [
        term for term in KANNADA_TERMS
        if term in normalized
    ]
    other = [
        term for term in OTHER_LANGUAGE_TERMS
        if term in normalized
    ]

    if kannada and other:
        return Classification(
            "needs_review",
            "Conflicting film-language indicators",
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
