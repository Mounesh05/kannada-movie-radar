
-- Independent evidence attached to movie candidates.

CREATE TABLE IF NOT EXISTS movie_evidence (
    id BIGSERIAL PRIMARY KEY,

    candidate_id BIGINT NOT NULL
        REFERENCES movie_candidates(id) ON DELETE RESTRICT,

    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    evidence_excerpt TEXT NOT NULL,

    claim_type TEXT NOT NULL
        CHECK (
            claim_type IN (
                'identity',
                'language',
                'release'
            )
        ),

    recorded_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_candidate_evidence_source
        UNIQUE (candidate_id, source_url, claim_type),

    CHECK (length(btrim(source_title)) > 0),
    CHECK (length(btrim(evidence_excerpt)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_movie_evidence_candidate
ON movie_evidence (candidate_id);

-- Permanent record of verification decisions.

CREATE TABLE IF NOT EXISTS movie_verification_reviews (
    id BIGSERIAL PRIMARY KEY,

    candidate_id BIGINT NOT NULL
        REFERENCES movie_candidates(id) ON DELETE RESTRICT,

    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL
        CHECK (decision IN ('verified', 'rejected')),

    review_note TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(btrim(reviewer)) > 0),
    CHECK (length(btrim(review_note)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_movie_reviews_candidate
ON movie_verification_reviews (candidate_id);
