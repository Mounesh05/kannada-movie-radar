
import re
from dataclasses import dataclass
from typing import Literal

from radar.services.text_cleaner import clean_text

Status = Literal["relevant", "needs_review", "not_relevant"]


@dataclass(frozen=True)
class Classification:
    status: Status
    reason: str


KANNADA_TERMS = (
    "ಕನ್ನಡ ಸಿನಿಮಾ",
    "ಕನ್ನಡ ಚಿತ್ರ",
    "ಕನ್ನಡ ಚಲನಚಿತ್ರ",
    "ಕನ್ನಡ ಸಿನೆಮಾ",
    "ಸ್ಯಾಂಡಲ್‌ವುಡ್",
    "ಸ್ಯಾಂಡಲ್ ವುಡ್",
    "kannada film",
    "kannada movie",
    "kannada cinema",
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

# Only explicit film-related developments.
FILM_UPDATE_TERMS = (
    "release date",
    "releasing on",
    "theatrical release",
    "movie release",
    "film release",
    "trailer",
    "teaser",
    "first look",
    "motion poster",
    "official poster",
    "ott",
    "streaming",
    "digital premiere",
    "shooting begins",
    "filming begins",
    "shooting completed",
    "film announced",
    "movie announced",
    "film announcement",
    "movie announcement",
    "new movie",
    "new film",
    "joins cast",
    "cast announced",
    "box office",
    "postponed",
    "ಬಿಡುಗಡೆ",
    "ಬಿಡುಗಡೆ ದಿನಾಂಕ",
    "ಟ್ರೇಲರ್",
    "ಟೀಸರ್",
    "ಚಿತ್ರೀಕರಣ",
    "ಹೊಸ ಚಿತ್ರ",
    "ಘೋಷಣೆ",
    "ಒಟಿಟಿ",
    "ಫಸ್ಟ್ ಲುಕ್",
)

# Explicitly off-topic personal/celebrity headlines.
PERSONAL_NEWS_TERMS = (
    "birthday",
    "wedding",
    "marriage",
    "divorce",
    "dating",
    "relationship",
    "girlfriend",
    "boyfriend",
    "personal life",
    "family vacation",
    "celebrates birthday",
    "ಹುಟ್ಟುಹಬ್ಬ",
    "ಮದುವೆ",
    "ವಿಚ್ಛೇದನ",
    "ಪ್ರೇಮ ಸಂಬಂಧ",
)

# These are contextual signals, not automatic proof.
GENERAL_CINEMA_TERMS = (
    "cinema",
    "movie",
    "film",
    "festival",
    "actor",
    "actress",
    "director",
    "ಸಿನಿಮಾ",
    "ಸಿನೆಮಾ",
    "ಚಿತ್ರ",
    "ನಟ",
    "ನಟಿ",
    "ನಿರ್ದೇಶಕ",
    "ಬಿಫೆಸ್",
)


def contains_term(text: str, term: str) -> bool:
    """Match terms without false English substring matches."""
    pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
    return re.search(pattern, text) is not None


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(contains_term(text, term) for term in terms)


def classify_article(title: str) -> Classification:
    """Conservative title-only Kannada film relevance gate.

    'relevant' means potentially eligible for deeper processing,
    not factually verified or Telegram-publishable.
    """

    text = clean_text(title).casefold()

    if not text:
        return Classification(
            "needs_review",
            "Empty title",
        )

    kannada = has_any(text, KANNADA_TERMS)
    other_language = has_any(text, OTHER_LANGUAGE_TERMS)
    film_update = has_any(text, FILM_UPDATE_TERMS)
    personal_news = has_any(text, PERSONAL_NEWS_TERMS)
    cinema_context = has_any(text, GENERAL_CINEMA_TERMS)

    if personal_news:
        return Classification(
            "not_relevant",
            "Celebrity personal-life content is excluded",
        )

    if kannada and other_language:
        return Classification(
            "needs_review",
            "Mixed-language cinema context",
        )

    if other_language and not kannada:
        return Classification(
            "not_relevant",
            "Other-language film without Kannada evidence",
        )

    if kannada and film_update:
        return Classification(
            "relevant",
            "Explicit Kannada cinema update indicator",
        )

    if kannada:
        return Classification(
            "needs_review",
            "Kannada cinema context, but no clear film update",
        )

    if film_update or cinema_context:
        return Classification(
            "needs_review",
            "Film-related headline; Kannada identity unconfirmed",
        )

    return Classification(
        "needs_review",
        "Insufficient context to establish film relevance",
    )
