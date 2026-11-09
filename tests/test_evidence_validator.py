
"""Tests for conservative supporting-source validation."""

from radar.agents.evidence_validator import validate_source

ORIGINAL = "https://www.cinisuddi.com/film-news/"
INDEPENDENT = "https://example-news.com/film-news/"

MOVIE = "ಲಾರ್ಡ್ ಗಾಗ"

SOURCE_TEXT = (
    "ಕನ್ನಡ ಚಿತ್ರ ಲಾರ್ಡ್ ಗಾಗ ಚಿತ್ರದ ಟೀಸರ್ ಇಂದು ಬಿಡುಗಡೆಯಾಗಿದೆ. "
    "ಚಿತ್ರದ ನಿರ್ದೇಶಕರು ಕಾರ್ಯಕ್ರಮದಲ್ಲಿ ಭಾಗವಹಿಸಿದ್ದರು."
)

EXCERPT = "ಕನ್ನಡ ಚಿತ್ರ ಲಾರ್ಡ್ ಗಾಗ ಚಿತ್ರದ ಟೀಸರ್ ಇಂದು ಬಿಡುಗಡೆಯಾಗಿದೆ."


def validate(**overrides):
    values = {
        "movie_title": MOVIE,
        "original_url": ORIGINAL,
        "supporting_url": INDEPENDENT,
        "source_text": SOURCE_TEXT,
        "excerpt": EXCERPT,
    }
    values.update(overrides)
    return validate_source(**values)


def test_valid_provenance_is_review_eligible():
    result = validate()
    assert result.eligible_for_review
    assert not result.issues


def test_same_publisher_rejected():
    result = validate(
        supporting_url="https://cinisuddi.com/other/"
    )
    assert not result.eligible_for_review


def test_excerpt_must_exist_in_source():
    result = validate(
        excerpt="This unrelated film was released last month."
    )
    assert not result.eligible_for_review


def test_movie_title_must_appear():
    result = validate(
        source_text=(
            "ಬೇರೆ ಚಿತ್ರದ ಟೀಸರ್ ಇಂದು ಬಿಡುಗಡೆಯಾಗಿದೆ. "
            "ಚಿತ್ರದ ನಿರ್ದೇಶಕರು ಕಾರ್ಯಕ್ರಮದಲ್ಲಿ ಭಾಗವಹಿಸಿದ್ದರು."
        )
    )
    assert not result.eligible_for_review


def test_empty_source_text_is_rejected():
    result = validate(source_text="")
    assert not result.eligible_for_review


def test_invalid_http_url_is_rejected():
    result = validate(
        supporting_url="http://example-news.com/story/"
    )
    assert not result.eligible_for_review


def test_confirmed_alias_accepted():
    result = validate(
        source_text=(
            "Lord Gaga movie teaser launched at the event. "
            "The film team attended the launch."
        ),
        excerpt="Lord Gaga movie teaser launched at the event.",
        aliases=["Lord Gaga"],
    )
    assert result.eligible_for_review


def test_too_short_excerpt_is_rejected():
    result = validate(excerpt="ಲಾರ್ಡ್ ಗಾಗ")
    assert not result.eligible_for_review
