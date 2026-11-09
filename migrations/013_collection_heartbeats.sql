
CREATE TABLE IF NOT EXISTS collector_runs (
    id BIGSERIAL PRIMARY KEY,
    github_run_key TEXT NOT NULL UNIQUE,
    completed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collector_runs_completed
ON collector_runs (completed_at DESC);
