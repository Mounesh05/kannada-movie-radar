
CREATE TABLE IF NOT EXISTS telegram_digest_deliveries (
    id BIGSERIAL PRIMARY KEY,
    chat_id TEXT NOT NULL,
    week_start_ist DATE NOT NULL,
    week_end_ist DATE NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('sending', 'sent')),
    claimed_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMPTZ,
    telegram_message_id BIGINT,
    UNIQUE (chat_id, week_start_ist)
);
