
import pytest

from radar.services.article_classifier import classify_article


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("ಹೊಸ ಕನ್ನಡ ಸಿನಿಮಾ ಬಿಡುಗಡೆ", "relevant"),
        ("Upcoming Kannada movie announcement", "relevant"),
        ("ಮಲಯಾಳಂ ಸಿನಿಮಾ ವಿಮರ್ಶೆ", "not_relevant"),
        ("New Tamil movie announced", "not_relevant"),
        ("ಹೊಸ ಚಿತ್ರದ ಟ್ರೇಲರ್ ಬಿಡುಗಡೆ", "needs_review"),
        ("Film festival highlights", "needs_review"),
        (
            "Kannada movie and Tamil film comparison",
            "needs_review",
        ),
    ],
)
def test_article_classification(title, expected):
    result = classify_article(title)

    assert result.status == expected
    assert result.reason
