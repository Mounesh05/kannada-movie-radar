
from radar.services.news_categorizer import categorize_news


def test_trailer_category():
    result = categorize_news(
        "Kannada movie trailer released"
    )
    assert result.category == "trailer"


def test_ott_category():
    result = categorize_news(
        "Kannada film streaming on Prime Video"
    )
    assert result.category == "ott"


def test_release_category():
    result = categorize_news(
        "Kannada movie release date announced"
    )
    assert result.category == "release"


def test_production_category():
    result = categorize_news(
        "Kannada film shooting begins"
    )
    assert result.category == "production"


def test_box_office_category():
    result = categorize_news(
        "Kannada movie box office collection report"
    )
    assert result.category == "box_office"


def test_unknown_category():
    result = categorize_news(
        "Cinema discussion and cultural event"
    )
    assert result.category == "other"


def test_empty_category():
    result = categorize_news("")
    assert result.category == "other"
