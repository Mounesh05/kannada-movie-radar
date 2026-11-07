
from radar.services.movie_matcher import (
    normalize_title,
    suggest_matches,
)


def test_title_normalization():
    assert normalize_title("  KD: THE DEVIL! ") == "kd the devil"


def test_exact_title_match():
    results = suggest_matches(
        "KD: The Devil",
        [
            (1, "KD: The Devil"),
            (2, "Shyloo"),
        ],
    )

    assert results[0].movie_id == 1
    assert results[0].score == 1.0
    assert results[0].match_type == "exact_title"


def test_completely_different_title():
    results = suggest_matches(
        "Sparsha",
        [(1, "Mahavatar Narsimha")],
    )

    assert results == []


def test_empty_title():
    assert suggest_matches("", [(1, "Shyloo")]) == []


def test_same_name_does_not_merge_movies():
    results = suggest_matches(
        "Example Film",
        [
            (1, "Example Film"),
            (2, "Example Film"),
        ],
    )

    assert len(results) == 2
    assert results[0].score == 1.0
    assert results[1].score == 1.0


def test_suggestions_sorted_by_score():
    results = suggest_matches(
        "KD The Devil",
        [
            (2, "KD The Devill"),
            (1, "KD The Devil"),
        ],
    )

    assert results[0].movie_id == 1
    assert results[0].score == 1.0
