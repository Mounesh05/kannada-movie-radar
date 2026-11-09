
BEGIN;

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS review_status TEXT
NOT NULL DEFAULT 'pending';

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS movie_candidate_id BIGINT
REFERENCES movie_candidates(id);

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS supporting_url TEXT;

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS reviewer TEXT;

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS review_note TEXT;

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE news_events
ADD COLUMN IF NOT EXISTS duplicate_of_event_id BIGINT
REFERENCES news_events(id);

ALTER TABLE news_events
ADD CONSTRAINT news_review_status_check
CHECK (
    review_status IN (
        'pending', 'approved', 'rejected', 'duplicate'
    )
);

ALTER TABLE news_events
ADD CONSTRAINT news_approval_evidence_check
CHECK (
    review_status <> 'approved'
    OR (
        evidence_label = 'verified'
        AND movie_candidate_id IS NOT NULL
        AND supporting_url IS NOT NULL
        AND reviewer IS NOT NULL
        AND review_note IS NOT NULL
        AND reviewed_at IS NOT NULL
        AND duplicate_of_event_id IS NULL
    )
);

ALTER TABLE news_events
ADD CONSTRAINT news_duplicate_reference_check
CHECK (
    review_status <> 'duplicate'
    OR (
        duplicate_of_event_id IS NOT NULL
        AND duplicate_of_event_id <> id
    )
);

CREATE INDEX IF NOT EXISTS idx_news_review_status
ON news_events (review_status);

COMMIT;
