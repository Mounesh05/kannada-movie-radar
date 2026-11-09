
BEGIN;

ALTER TABLE public.news_events
DROP CONSTRAINT IF EXISTS news_events_category_check;

ALTER TABLE public.news_events
ADD CONSTRAINT news_events_category_check
CHECK (
    category IN (
        'announcement',
        'release',
        'trailer',
        'ott',
        'cast_crew',
        'production',
        'box_office',
        'music',
        'booking',
        'other'
    )
);

COMMIT;
