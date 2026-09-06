CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.drafts (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type     TEXT NOT NULL,
  title          TEXT NOT NULL,
  form_data      JSONB NOT NULL DEFAULT '{}'::jsonb,
  generated_text TEXT,
  llm_meta       JSONB DEFAULT '{}'::jsonb,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON public.drafts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_drafts_event_type ON public.drafts(event_type);

ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;
