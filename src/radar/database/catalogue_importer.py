
from radar.collectors.wikidata_collector import WikidataMovie
from radar.database.connection import get_connection


def save_wikidata_movies(
    movies: list[WikidataMovie],
) -> dict[str, int]:
    """Import movies and unverified claims transactionally.

    This importer is idempotent for repeated Wikidata IDs.
    It does not verify or overwrite canonical release facts.
    """

    stats = {
        "new_movies": 0,
        "existing_movies": 0,
        "new_claims": 0,
    }

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for movie in movies:
                wikidata_id = movie["wikidata_id"]
                title = movie["title"]
                source_url = movie["source_url"]

                cursor.execute(
                    """
                    SELECT movie_id
                    FROM movie_external_ids
                    WHERE provider = 'wikidata'
                      AND external_id = %s
                    """,
                    (wikidata_id,),
                )

                existing = cursor.fetchone()

                if existing:
                    movie_id = existing[0]
                    stats["existing_movies"] += 1

                else:
                    cursor.execute(
                        """
                        INSERT INTO movies (
                            primary_title,
                            original_language
                        )
                        VALUES (%s, %s)
                        RETURNING id
                        """,
                        (
                            title,
                            movie["original_language"],
                        ),
                    )

                    movie_id = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO movie_external_ids (
                            movie_id,
                            provider,
                            external_id,
                            source_url
                        )
                        VALUES (%s, 'wikidata', %s, %s)
                        """,
                        (
                            movie_id,
                            wikidata_id,
                            source_url,
                        ),
                    )

                    stats["new_movies"] += 1

                # Preserve source claims without treating them
                # as verified catalogue facts.
                claims = [
                    ("title", title),
                    (
                        "original_language",
                        movie["original_language"],
                    ),
                ]

                reported_date = movie[
                    "reported_release_date"
                ]

                if reported_date:
                    claims.append(
                        ("release_date", reported_date)
                    )

                for claim_type, claim_value in claims:
                    cursor.execute(
                        """
                        INSERT INTO movie_claims (
                            movie_id,
                            claim_type,
                            claim_value,
                            date_precision,
                            source_name,
                            source_url
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            'Wikidata', %s
                        )
                        ON CONFLICT (
                            movie_id,
                            claim_type,
                            claim_value,
                            source_url
                        )
                        DO NOTHING
                        RETURNING id
                        """,
                        (
                            movie_id,
                            claim_type,
                            claim_value,
                            (
                                "unknown"
                                if claim_type == "release_date"
                                else None
                            ),
                            source_url,
                        ),
                    )

                    if cursor.fetchone() is not None:
                        stats["new_claims"] += 1

    return stats
