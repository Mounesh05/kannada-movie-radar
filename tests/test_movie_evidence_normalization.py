
from radar.agents.movie_graph import (
    evidence_review_node,
    normalize_evidence,
)
from radar.agents.movie_schema import MovieExtraction


def test_kannada_quote_normalization():
    original = (
        "‘ದೇವಿ ಮಹಾತ್ಮೆ’ ಚಿತ್ರದ "
        "‘ಎದೆ ಸುಡುತಿದೆ ಗಾಯ’ ಹಾಡಿನಲ್ಲಿ ಮಿಂಚಿದ ಗಾಯಕಿ ಅನನ್ಯಾ ಭಟ್."
    )
    evidence = (
        "ದೇವಿ ಮಹಾತ್ಮೆ ಚಿತ್ರದ "
        "ಎದೆ ಸುಡುತಿದೆ ಗಾಯ ಹಾಡಿನಲ್ಲಿ ಮಿಂಚಿದ ಗಾಯಕಿ ಅನನ್ಯಾ ಭಟ್"
    )

    assert normalize_evidence(original) == normalize_evidence(evidence)


def test_valid_evidence_with_different_punctuation():
    extraction = MovieExtraction(
        movie_title="ದೇವಿ ಮಹಾತ್ಮೆ",
        film_language=None,
        is_kannada_film="unknown",
        release_date=None,
        mentioned_people=[],
        evidence=["ದೇವಿ ಮಹಾತ್ಮೆ ಚಿತ್ರದ ಎದೆ ಸುಡುತಿದೆ ಗಾಯ"],
        needs_review=True,
    )

    result = evidence_review_node({
        "title": "‘ದೇವಿ ಮಹಾತ್ಮೆ’ ಚಿತ್ರದ ‘ಎದೆ ಸುಡುತಿದೆ ಗಾಯ’ ಹಾಡು.",
        "extraction": extraction,
    })

    assert result["outcome"] == "ready"


def test_invented_evidence_is_rejected():
    extraction = MovieExtraction(
        movie_title="ದೇವಿ ಮಹಾತ್ಮೆ",
        film_language=None,
        is_kannada_film="unknown",
        release_date=None,
        mentioned_people=[],
        evidence=["ಈ ಚಿತ್ರ ನಾಳೆ ಬಿಡುಗಡೆಯಾಗಲಿದೆ"],
        needs_review=True,
    )

    result = evidence_review_node({
        "title": "‘ದೇವಿ ಮಹಾತ್ಮೆ’ ಚಿತ್ರದ ಹಾಡು ಬಿಡುಗಡೆ.",
        "extraction": extraction,
    })

    assert result["outcome"] == "no_candidate"
