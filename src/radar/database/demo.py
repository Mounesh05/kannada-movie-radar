
from radar.database.articles import (
    get_recent_articles,
    save_article,
)


def main() -> None:
    inserted = save_article(
        source_name="Sample Kannada Cinema News",
        feed_url="https://example.com/feed.xml",
        title="Sample Movie Announcement",
        article_url="https://example.com/movie-news",
    )

    print("New article inserted:", inserted)

    print("\nSaved articles:")
    for article in get_recent_articles():
        print(article)


if __name__ == "__main__":
    main()
