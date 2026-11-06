
import pytest

from radar.services.article_classifier import classify_article


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("ಹೊಸ ಕನ್ನಡ ಸಿನಿಮಾ ಬಿಡುಗಡೆ", "relevant"),
        ("Kannada movie announced", "relevant"),
        ("Upcoming Tamil film", "not_relevant"),
        ("ಮಲಯಾಳಂ ಸಿನಿಮಾ ವಿಮರ್ಶೆ", "not_relevant"),
        ("Cinema news today", "needs_review"),
        ("Kannada movie and Tamil film", "needs_review"),
        ("", "needs_review"),
        ("kannadamovie announcement", "needs_review"),
    ],
)
def test_improved_classification(title, expected):
    result = classify_article(title)
    assert result.status == expected
