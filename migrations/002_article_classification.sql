
ALTER TABLE articles
ADD COLUMN IF NOT EXISTS classification_status TEXT
    NOT NULL DEFAULT 'needs_review';

ALTER TABLE articles
ADD COLUMN IF NOT EXISTS classification_reason TEXT;

ALTER TABLE articles
DROP CONSTRAINT IF EXISTS articles_classification_status_check;

ALTER TABLE articles
ADD CONSTRAINT articles_classification_status_check
CHECK (
    classification_status IN (
        'relevant',
        'needs_review',
        'not_relevant'
    )
);

CREATE INDEX IF NOT EXISTS idx_articles_classification
ON articles (classification_status);
