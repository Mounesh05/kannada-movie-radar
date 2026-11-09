
import pytest

from radar.services.news_categorizer import categorize_news


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        (
            "‘ದೇವಿ ಮಹಾತ್ಮೆ’ ಚಿತ್ರದ ಹಾಡಿನಲ್ಲಿ ಮಿಂಚಿದ ಗಾಯಕಿ",
            "music",
        ),
        (
            "‘ಲಂಬೋದರ 2.0’ ಚಿತ್ರದ ಅಡ್ವಾನ್ಸ್ ಬುಕಿಂಗ್ ಶುರು",
            "booking",
        ),
        (
            "‘ಶ್ರೀರಸ್ತು’ ಚಿತ್ರದ ಮೊದಲ ಹಾಡು ಬಿಡುಗಡೆ",
            "music",
        ),
        (
            "‘ವಿದೂಷಕ’ ಚಿತ್ರದ ಟ್ರೇಲರ್ ಅನಾವರಣ",
            "trailer",
        ),
        (
            "‘ಪತ್ತೇದಾರಿ’ ಚಿತ್ರಕ್ಕೆ ಚಾಲನೆ",
            "production",
        ),
        (
            "‘ಕಲ್ಯಾಣಿ’ ಚಿತ್ರದ ಆಡಿಯೋ ಬಿಡುಗಡೆ",
            "music",
        ),
        (
            "ಓ ಮನಸೇ ಟಿವಿ ಸೀರಿಯಲ್",
            "other",
        ),
        (
            "‘ಲಾರ್ಡ್ ಗಾಗ’ ಟೀಸರ್ ರಿಲೀಸ್",
            "trailer",
        ),
        (
            "‘ಅನಂತಪಯಣ’ ಚಿತ್ರದ ಹಾಡು ಬಿಡುಗಡೆ",
            "music",
        ),
        (
            "ರಾಮಾಯಣ ಚಿತ್ರವಿಮರ್ಶೆ",
            "other",
        ),
        (
            "Kannada movie OTT streaming on Netflix",
            "ott",
        ),
        (
            "New Kannada film release date announced",
            "release",
        ),
        (
            "Kannada film box office collections",
            "box_office",
        ),
        (
            "New Kannada film announced",
            "announcement",
        ),
    ],
)
def test_kannada_news_categories(title, expected):
    result = categorize_news(title)

    assert result.category == expected
    assert result.reason
