
"""Tests for independent movie evidence matching."""

from radar.agents.evidence_matcher import (
    Article,
    MovieCandidate,
    match_evidence,
    title_matches,
)


def candidate():
    return MovieCandidate(
        id=1,
        movie_title="ಲಾರ್ಡ್ ಗಾಗ",
        original_url="https://www.cinisuddi.com/original/",
    )


def test_kannada_title_matching():
    assert title_matches(
        "ಹೊಸ ಚಿತ್ರ 'ಲಾರ್ಡ್ ಗಾಗ' ಟ್ರೇಲರ್ ಬಿಡುಗಡೆ",
        "ಲಾರ್ಡ್ ಗಾಗ",
    )


def test_unrelated_title_does_not_match():
    assert not title_matches(
        "ಕನ್ನಡ ಚಿತ್ರ ಬಿಡುಗಡೆ",
        "ಲಾರ್ಡ್ ಗಾಗ",
    )


def test_short_alias_rejected():
    assert not title_matches(
        "A new movie",
        "A",
    )


def test_original_publisher_excluded():
    articles = [
        Article(
            id=10,
            title="ಲಾರ್ಡ್ ಗಾಗ ಚಿತ್ರದ ಸುದ್ದಿ",
            url="https://www.cinisuddi.com/another-story/",
        ),
    ]

    assert match_evidence(candidate(), articles) == []


def test_independent_publisher_match():
    articles = [
        Article(
            id=11,
            title="ಲಾರ್ಡ್ ಗಾಗ ಚಿತ್ರದ ಹೊಸ ಸುದ್ದಿ",
            url="https://example-news.com/story/",
        ),
    ]

    result = match_evidence(candidate(), articles)

    assert len(result) == 1
    assert result[0].publisher == "example-news.com"


def test_duplicate_url_excluded():
    article = Article(
        id=12,
        title="ಲಾರ್ಡ್ ಗಾಗ ಚಿತ್ರದ ಟೀಸರ್",
        url="https://example-news.com/story/",
    )

    result = match_evidence(
        candidate(),
        [article, article],
    )

    assert len(result) == 1


def test_confirmed_romanized_alias():
    articles = [
        Article(
            id=13,
            title="Lord Gaga movie teaser released",
            url="https://example-news.com/teaser/",
        ),
    ]

    result = match_evidence(
        candidate(),
        articles,
        aliases=["Lord Gaga"],
    )

    assert len(result) == 1
    assert result[0].matched_alias == "Lord Gaga"


def test_different_movies_not_matched():
    articles = [
        Article(
            id=14,
            title="Another Kannada film trailer released",
            url="https://example-news.com/other/",
        ),
    ]

    assert match_evidence(candidate(), articles) == []
