
-- Phase 2.3: Record Gemini extraction attempts.

CREATE TABLE IF NOT EXISTS extraction_attempts (
    id BIGSERIAL PRIMARY KEY,

    article_id BIGINT NOT NULL
        REFERENCES articles(id) ON DELETE RESTRICT,

    candidate_id BIGINT
        REFERENCES movie_candidates(id) ON DELETE SET NULL,

    model_name TEXT NOT NULL,

    status TEXT NOT NULL
        CHECK (
            status IN (
                'saved',
                'duplicate',
                'no_candidate',
                'failed'
            )
        ),

    error_type TEXT,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        status <> 'failed'
        OR error_type IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_extraction_attempts_article
ON extraction_attempts (article_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_extraction_attempts_status
ON extraction_attempts (status);
