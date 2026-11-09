
-- Phase 2.5C.3: Source-backed claim review.

-- Keep an excerpt supporting manually entered claims.
ALTER TABLE movie_claims
ADD COLUMN IF NOT EXISTS source_excerpt TEXT;

-- Record release context when known.
ALTER TABLE movie_claims
ADD COLUMN IF NOT EXISTS release_kind TEXT;

ALTER TABLE movie_claims
ADD COLUMN IF NOT EXISTS release_territory TEXT;

-- Audit every human review decision.
CREATE TABLE IF NOT EXISTS movie_claim_reviews (
    id BIGSERIAL PRIMARY KEY,

    claim_id BIGINT NOT NULL
        REFERENCES movie_claims(id) ON DELETE RESTRICT,

    previous_status TEXT NOT NULL
        CHECK (
            previous_status IN (
                'unverified',
                'supported',
                'disputed',
                'rejected'
            )
        ),

    new_status TEXT NOT NULL
        CHECK (
            new_status IN (
                'supported',
                'disputed',
                'rejected'
            )
        ),

    reviewer TEXT NOT NULL
        CHECK (length(btrim(reviewer)) > 0),

    review_note TEXT NOT NULL
        CHECK (length(btrim(review_note)) > 0),

    sources_checked BOOLEAN NOT NULL
        CHECK (sources_checked = TRUE),

    reviewed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (previous_status <> new_status)
);

CREATE INDEX IF NOT EXISTS idx_claim_reviews_claim
ON movie_claim_reviews (claim_id);
