-- Z-MAX RFQ / lead submissions
-- Apply once against your Neon database:
--   psql "$DATABASE_URL" -f schema.sql

CREATE TABLE IF NOT EXISTS quote_submissions (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- form fields
  name          TEXT NOT NULL,
  company       TEXT,
  email         TEXT NOT NULL,
  phone         TEXT,
  application   TEXT NOT NULL,
  quantity      TEXT,
  locale        TEXT,

  -- Google Ads / marketing attribution
  utm_source    TEXT,
  utm_medium    TEXT,
  utm_campaign  TEXT,
  utm_term      TEXT,
  utm_content   TEXT,
  gclid         TEXT,
  gad_source    TEXT,
  first_seen    TIMESTAMPTZ,

  -- request context (no PII beyond what the user submitted)
  page_url      TEXT,
  referer       TEXT,
  user_agent    TEXT,
  ip            INET
);

CREATE INDEX IF NOT EXISTS idx_quote_submissions_created_at ON quote_submissions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quote_submissions_gclid ON quote_submissions (gclid) WHERE gclid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_quote_submissions_email ON quote_submissions (email);
