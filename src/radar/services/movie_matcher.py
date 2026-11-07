
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class MatchSuggestion:
    movie_id: int
    movie_title: str
    score: float
    match_type: str


def normalize_title(title: str) -> str:
    """Normalize text without transliterating Kannada."""

    text = unicodedata.normalize("NFKC", title)
    text = text.casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def suggest_matches(
    candidate_title: str,
    catalogue: list[tuple[int, str]],
    min_score: float = 0.65,
) -> list[MatchSuggestion]:
    """Rank potential identities without linking records."""

    normalized = normalize_title(candidate_title)

    if len(normalized) < 3:
        return []

    suggestions = []

    for movie_id, movie_title in catalogue:
        target = normalize_title(movie_title)

        if len(target) < 3:
            continue

        if normalized == target:
            score = 1.0
            match_type = "exact_title"
        else:
            score = SequenceMatcher(
                None,
                normalized,
                target,
            ).ratio()
            match_type = "similar_title"

        if score >= min_score:
            suggestions.append(
                MatchSuggestion(
                    movie_id=movie_id,
                    movie_title=movie_title,
                    score=round(score, 3),
                    match_type=match_type,
                )
            )

    return sorted(
        suggestions,
        key=lambda item: (-item.score, item.movie_id),
    )
