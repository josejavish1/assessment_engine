-- Migration 002: War Room Messages Persistence

CREATE TABLE IF NOT EXISTS public.war_room_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_slug TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    impacted_vectors TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_war_room_client_slug ON public.war_room_messages(client_slug, created_at ASC);

-- Enable Row Level Security
ALTER TABLE public.war_room_messages ENABLE ROW LEVEL SECURITY;

-- Allow read/write access
DROP POLICY IF EXISTS "Public War Room Access" ON public.war_room_messages;
CREATE POLICY "Public War Room Access"
    ON public.war_room_messages FOR ALL
    USING (true);

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';
