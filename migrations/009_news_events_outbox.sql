
-- Phase 3.1: Categorized news events and Kafka outbox.

CREATE TABLE IF NOT EXISTS news_events (
    id BIGSERIAL PRIMARY KEY,

    article_id BIGINT NOT NULL UNIQUE
        REFERENCES articles(id) ON DELETE RESTRICT,

    category TEXT NOT NULL DEFAULT 'other'
        CHECK (
            category IN (
                'announcement',
                'release',
                'trailer',
                'ott',
                'cast_crew',
                'production',
                'box_office',
                'other'
            )
        ),

    evidence_label TEXT NOT NULL DEFAULT 'under_review'
        CHECK (
            evidence_label IN (
                'verified',
                'unconfirmed',
                'under_review'
            )
        ),

    category_method TEXT NOT NULL DEFAULT 'rules_v1',

    -- When the source article was first collected.
    first_seen_at TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_events_week
ON news_events (first_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_events_category
ON news_events (category, evidence_label);


-- Transactional event queue for future Kafka publication.
CREATE TABLE IF NOT EXISTS event_outbox (
    id BIGSERIAL PRIMARY KEY,

    event_type TEXT NOT NULL,
    aggregate_id BIGINT NOT NULL,
    topic TEXT NOT NULL,

    payload JSONB NOT NULL
        CHECK (jsonb_typeof(payload) = 'object'),

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'processing',
                'published'
            )
        ),

    attempts INTEGER NOT NULL DEFAULT 0
        CHECK (attempts >= 0),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    published_at TIMESTAMPTZ,

    UNIQUE (event_type, aggregate_id)
);

CREATE INDEX IF NOT EXISTS idx_outbox_pending
ON event_outbox (id)
WHERE status = 'pending';
