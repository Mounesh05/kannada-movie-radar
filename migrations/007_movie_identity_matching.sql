
-- Phase 2.5C.1: Human-reviewed identity links.

CREATE TABLE IF NOT EXISTS movie_candidate_links (
    id BIGSERIAL PRIMARY KEY,

    candidate_id BIGINT NOT NULL UNIQUE
        REFERENCES movie_candidates(id) ON DELETE RESTRICT,

    movie_id BIGINT NOT NULL
        REFERENCES movies(id) ON DELETE RESTRICT,

    reviewer TEXT NOT NULL
        CHECK (length(btrim(reviewer)) > 0),

    review_note TEXT NOT NULL
        CHECK (length(btrim(review_note)) > 0),

    linked_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidate_links_movie
ON movie_candidate_links (movie_id);

-- Audit both accepted and rejected match decisions.

CREATE TABLE IF NOT EXISTS movie_match_reviews (
    id BIGSERIAL PRIMARY KEY,

    candidate_id BIGINT NOT NULL
        REFERENCES movie_candidates(id) ON DELETE RESTRICT,

    movie_id BIGINT NOT NULL
        REFERENCES movies(id) ON DELETE RESTRICT,

    decision TEXT NOT NULL
        CHECK (decision IN ('approved', 'rejected')),

    reviewer TEXT NOT NULL
        CHECK (length(btrim(reviewer)) > 0),

    review_note TEXT NOT NULL
        CHECK (length(btrim(review_note)) > 0),

    reviewed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_match_reviews_candidate
ON movie_match_reviews (candidate_id);
