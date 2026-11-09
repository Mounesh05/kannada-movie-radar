
from dataclasses import dataclass
from typing import Literal

from radar.services.text_cleaner import clean_text

NewsCategory = Literal[
    "announcement",
    "release",
    "trailer",
    "ott",
    "cast_crew",
    "production",
    "box_office",
    "music",
    "booking",
    "other",
]


@dataclass(frozen=True)
class NewsCategoryResult:
    category: NewsCategory
    reason: str


# Review and television content is outside the update digest.
# These indicators are provisional; a separate relevance worker
# remains responsible for final exclusion decisions.
EXCLUDED_CONTENT_TERMS = (
    "movie review",
    "film review",
    "ಚಿತ್ರವಿಮರ್ಶೆ",
    "ಚಿತ್ರ ವಿಮರ್ಶೆ",
    "tv serial",
    "television serial",
    "ಸೀರಿಯಲ್",
    "ಧಾರಾವಾಹಿ",
)


# Order matters: specific events must precede generic releases.
# Example: "first song released" is MUSIC, not theatrical RELEASE.
CATEGORY_TERMS: tuple[
    tuple[NewsCategory, tuple[str, ...]], ...
] = (
    (
        "booking",
        (
            "advance booking",
            "advance bookings",
            "ticket booking",
            "bookings open",
            "ಅಡ್ವಾನ್ಸ್ ಬುಕಿಂಗ್",
            "ಮುಂಗಡ ಬುಕಿಂಗ್",
            "ಟಿಕೆಟ್ ಬುಕಿಂಗ್",
        ),
    ),
    (
        "music",
        (
            "first song",
            "new song",
            "song released",
            "song release",
            "audio release",
            "audio launch",
            "soundtrack",
            "lyrical video",
            "ಮೊದಲ ಹಾಡು",
            "ಹೊಸ ಹಾಡು",
            "ಹಾಡು ಬಿಡುಗಡೆ",
            "ಹಾಡಿನ ಬಿಡುಗಡೆ",
            "ಹಾಡಿನಲ್ಲಿ",
            "ಆಡಿಯೋ ಬಿಡುಗಡೆ",
            "ಸಂಗೀತ ಬಿಡುಗಡೆ",
            "ಲಿರಿಕಲ್ ವಿಡಿಯೋ",
        ),
    ),
    (
        "ott",
        (
            "ott",
            "streaming",
            "digital premiere",
            "prime video",
            "netflix",
            "zee5",
            "sun nxt",
            "ಜಿಯೋಹಾಟ್‌ಸ್ಟಾರ್",
            "ಒಟಿಟಿ",
        ),
    ),
    (
        "trailer",
        (
            "trailer",
            "teaser",
            "first look",
            "motion poster",
            "ಟ್ರೇಲರ್",
            "ಟೀಸರ್",
            "ಫಸ್ಟ್ ಲುಕ್",
        ),
    ),
    (
        "box_office",
        (
            "box office",
            "collection report",
            "ಬಾಕ್ಸ್ ಆಫೀಸ್",
        ),
    ),
    (
        "release",
        (
            "release date",
            "releasing on",
            "theatrical release",
            "film release",
            "movie release",
            "ಬಿಡುಗಡೆ ದಿನಾಂಕ",
            "ಚಿತ್ರ ಬಿಡುಗಡೆ",
            "ಚಿತ್ರದ ಬಿಡುಗಡೆ",
        ),
    ),
    (
        "cast_crew",
        (
            "joins cast",
            "cast announced",
            "new director",
            "ಹೊಸ ನಿರ್ದೇಶಕ",
            "ತಾರಾಗಣ",
            "ನಟನಾಗಿ ಆಯ್ಕೆ",
        ),
    ),
    (
        "production",
        (
            "shooting",
            "filming",
            "production begins",
            "shooting begins",
            "film launched",
            "movie launched",
            "film muhurat",
            "ಮುಹೂರ್ತ",
            "ಮುಹೂರ್ತ ನೆರವೇರಿತು",
            "ಚಿತ್ರಕ್ಕೆ ಚಾಲನೆ",
            "ಚಿತ್ರೀಕರಣ",
            "ಶೂಟಿಂಗ್",
        ),
    ),
    (
        "announcement",
        (
            "announced",
            "announcement",
            "new film",
            "new movie",
            "ಹೊಸ ಚಿತ್ರ ಘೋಷಣೆ",
            "ಹೊಸ ಸಿನಿಮಾ ಘೋಷಣೆ",
            "ಚಿತ್ರ ಘೋಷಣೆ",
        ),
    ),
)


def categorize_news(title: str) -> NewsCategoryResult:
    """Assign a provisional event category using headline signals.

    Category detection does not establish Kannada film identity,
    factual verification, freshness, or digest eligibility.
    """
    normalized = clean_text(title).casefold()

    if not normalized:
        return NewsCategoryResult(
            category="other",
            reason="Empty article title",
        )

    for term in EXCLUDED_CONTENT_TERMS:
        if term in normalized:
            return NewsCategoryResult(
                category="other",
                reason="Review or television content indicator",
            )

    for category, terms in CATEGORY_TERMS:
        if any(term in normalized for term in terms):
            return NewsCategoryResult(
                category=category,
                reason=f"Matched {category} event indicator",
            )

    return NewsCategoryResult(
        category="other",
        reason="No recognized film-update event indicator",
    )
