
import pytest

from radar.services.article_classifier import classify_article


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        (
            "Kannada movie release date announced",
            "relevant",
        ),
        (
            "Kannada film trailer released",
            "relevant",
        ),
        (
            "Kannada movie shooting begins",
            "relevant",
        ),
        (
            "New Kannada film announced",
            "relevant",
        ),
        (
            "Yash celebrates birthday with family",
            "not_relevant",
        ),
        (
            "Kannada actor wedding announced",
            "not_relevant",
        ),
        (
            "Sandalwood actor divorce controversy",
            "not_relevant",
        ),
        (
            "Upcoming Tamil film release",
            "not_relevant",
        ),
        (
            "Kannada cinema industry discussion",
            "needs_review",
        ),
        (
            "New film teaser released",
            "needs_review",
        ),
        (
            "Film festival highlights",
            "needs_review",
        ),
        (
            "Actor joins cast of a new film",
            "needs_review",
        ),
        (
            "ಹೊಸ ಕನ್ನಡ ಸಿನಿಮಾ ಬಿಡುಗಡೆ",
            "relevant",
        ),
        (
            "ಹೊಸ ಚಿತ್ರದ ಟ್ರೇಲರ್ ಬಿಡುಗಡೆ",
            "needs_review",
        ),
        (
            "ಯಶ್ ಹುಟ್ಟುಹಬ್ಬ",
            "not_relevant",
        ),
        (
            "ಬಿಫೆಸ್ 15 ನೋಡಿದ್ದು ಕೇಳಿದ್ದು",
            "needs_review",
        ),
    ],
)
def test_film_first_relevance(title, expected):
    result = classify_article(title)

    assert result.status == expected
    assert result.reason
