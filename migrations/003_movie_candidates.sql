
-- Phase 2.2: Persist unverified Gemini movie candidates.

CREATE TABLE IF NOT EXISTS movie_candidates (
    id BIGSERIAL PRIMARY KEY,

    article_id BIGINT NOT NULL
        REFERENCES articles(id) ON DELETE RESTRICT,

    movie_title TEXT NOT NULL
        CHECK (length(btrim(movie_title)) > 0),

    film_language TEXT,

    is_kannada_film TEXT NOT NULL
        CHECK (
            is_kannada_film IN ('yes', 'no', 'unknown')
        ),

    release_date_text TEXT,

    mentioned_people JSONB NOT NULL
        DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(mentioned_people) = 'array'),

    evidence JSONB NOT NULL
        DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(evidence) = 'array'),

    ai_needs_review BOOLEAN NOT NULL,

    -- Store the input and model for provenance.
    input_title TEXT NOT NULL,
    model_name TEXT NOT NULL,

    -- Verification is separate from AI confidence.
    verification_status TEXT NOT NULL
        DEFAULT 'unverified'
        CHECK (
            verification_status IN (
                'unverified',
                'verified',
                'rejected'
            )
        ),

    extracted_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    -- Current MVP: one primary candidate per article.
    CONSTRAINT unique_movie_candidate_article
        UNIQUE (article_id)
);

CREATE INDEX IF NOT EXISTS idx_movie_candidates_status
ON movie_candidates (verification_status);

CREATE INDEX IF NOT EXISTS idx_movie_candidates_title
ON movie_candidates (movie_title);
