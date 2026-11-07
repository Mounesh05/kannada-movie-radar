
-- Phase 2.5B: Multi-source Kannada movie catalogue.
-- No metadata source is automatically trusted.

-- 1. Canonical movie identity

CREATE TABLE IF NOT EXISTS movies (
    id BIGSERIAL PRIMARY KEY,

    primary_title TEXT NOT NULL
        CHECK (length(btrim(primary_title)) > 0),

    original_language TEXT,

    release_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (
            release_status IN (
                'unknown',
                'announced',
                'in_production',
                'upcoming',
                'released',
                'postponed',
                'cancelled'
            )
        ),

    confirmed_release_date DATE,

    verification_status TEXT NOT NULL DEFAULT 'unverified'
        CHECK (
            verification_status IN (
                'unverified',
                'verified',
                'rejected'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movies_title
ON movies (primary_title);

CREATE INDEX IF NOT EXISTS idx_movies_release_status
ON movies (release_status);


-- 2. IDs associated with external movie sources

CREATE TABLE IF NOT EXISTS movie_external_ids (
    id BIGSERIAL PRIMARY KEY,

    movie_id BIGINT NOT NULL
        REFERENCES movies(id) ON DELETE RESTRICT,

    provider TEXT NOT NULL
        CHECK (
            provider IN (
                'wikidata',
                'imdb',
                'tmdb'
            )
        ),

    external_id TEXT NOT NULL
        CHECK (length(btrim(external_id)) > 0),

    source_url TEXT NOT NULL,

    added_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_provider_external_id
        UNIQUE (provider, external_id),

    CONSTRAINT unique_movie_provider
        UNIQUE (movie_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_external_ids_movie
ON movie_external_ids (movie_id);


-- 3. Individual facts reported by sources

CREATE TABLE IF NOT EXISTS movie_claims (
    id BIGSERIAL PRIMARY KEY,

    movie_id BIGINT NOT NULL
        REFERENCES movies(id) ON DELETE RESTRICT,

    claim_type TEXT NOT NULL
        CHECK (
            claim_type IN (
                'title',
                'original_language',
                'release_status',
                'release_date',
                'release_window',
                'director',
                'cast',
                'ott_platform',
                'ott_release_date'
            )
        ),

    claim_value TEXT NOT NULL
        CHECK (length(btrim(claim_value)) > 0),

    -- E.g. day, month, year, quarter, unknown.
    date_precision TEXT
        CHECK (
            date_precision IS NULL
            OR date_precision IN (
                'day',
                'month',
                'year',
                'quarter',
                'unknown'
            )
        ),

    source_name TEXT NOT NULL
        CHECK (length(btrim(source_name)) > 0),

    source_url TEXT NOT NULL
        CHECK (length(btrim(source_url)) > 0),

    claim_status TEXT NOT NULL DEFAULT 'unverified'
        CHECK (
            claim_status IN (
                'unverified',
                'supported',
                'disputed',
                'rejected'
            )
        ),

    observed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    source_published_at TIMESTAMPTZ,

    reviewer_note TEXT,

    CONSTRAINT unique_movie_source_claim
        UNIQUE (
            movie_id,
            claim_type,
            claim_value,
            source_url
        )
);

CREATE INDEX IF NOT EXISTS idx_claims_movie
ON movie_claims (movie_id);

CREATE INDEX IF NOT EXISTS idx_claims_type
ON movie_claims (claim_type);

CREATE INDEX IF NOT EXISTS idx_claims_status
ON movie_claims (claim_status);
