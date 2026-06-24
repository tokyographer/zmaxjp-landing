# RFQ Form → Neon Postgres Integration

How the lead/quote-request form on `index.html` captures submissions, stores them in Neon, and tracks conversions.

## Flow

```
Visitor → RFQ form (index.html)
        → POST /api/quote  (Vercel serverless function, server-side)
        → INSERT into Neon (quote_submissions)
        → 200 { redirect: "/thank-you" }
        → browser redirects to /thank-you  (Google Ads conversion fires here)
```

## What gets captured

Every submission stores:

- **Form fields:** `name`, `company`, `email`, `application`, `quantity`
- **Google Ads attribution** (when present in the landing URL): `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`, `gad_source`, plus `first_seen`
- **Request context:** `page_url`, `referer`, `user_agent`, `ip`, `created_at`

Attribution is read from the URL query string on page load, cached in `localStorage` (`zmax_attr`), and sent with the submission — so it survives the visitor scrolling to the footer form or navigating within the page.

## Spam protection

1. **Honeypot** — an off-screen `company_url` field. If filled, the server silently accepts (200) but does not store.
2. **Time-trap** — submissions faster than 2s after page load are silently dropped.
3. **Validation & limits** — required-field + email-format checks and per-field length caps in `api/quote.js`.

## Files

| File | Role |
|------|------|
| `api/quote.js` | Serverless endpoint: validation, spam checks, Neon insert |
| `schema.sql` | `quote_submissions` table definition |
| `thank-you.html` | Conversion landing page (served at `/thank-you`) |
| `vercel.json` | `cleanUrls` so `/thank-you` resolves |
| `package.json` | `@neondatabase/serverless` dependency |
| `index.html` | Form `data-endpoint=/api/quote`, honeypot, attribution capture, JSON submit + redirect |

## Setup

### 1. Neon

Create a database (Neon dashboard or Vercel Marketplace → Neon), then apply the schema:

```bash
psql "$DATABASE_URL" -f schema.sql
```

Use the **pooled** connection string (host contains `-pooler`).

### 2. Environment variable

Add `DATABASE_URL` to Vercel → Project → Settings → Environment Variables for **Production, Preview, and Development**:

```bash
vercel env add DATABASE_URL production
vercel env add DATABASE_URL preview
vercel env add DATABASE_URL development
```

For local dev: `cp .env.example .env` and fill in the value (run `vercel dev` to exercise `/api`).

> If you install Neon via the Vercel Marketplace integration, `DATABASE_URL` is provisioned automatically — just run the schema.

### 3. Deploy

```bash
vercel deploy --prod
```

### 4. Wire conversion tracking

Paste your Google Ads / GTM snippet into `thank-you.html` (placeholder block in `<head>`). Optionally fill `fireConversion()` in `index.html` to also fire on submit.

## Placeholders still to replace before launch

- `REPLACE_SALES_EMAIL` (footer, thank-you page, error fallback)
- `REPLACE_EU_PHONE`, `REPLACE_PRIVACY_URL`
- Google Ads conversion ID/label in `thank-you.html`

## Verifying

```bash
curl -X POST https://<your-domain>/api/quote \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test","company":"ACME","email":"t@example.com","application":"cool a laser diode","quantity":"100","gclid":"abc123","elapsed_ms":5000}'
# → {"ok":true,"redirect":"/thank-you"}

psql "$DATABASE_URL" -c "SELECT created_at, name, company, gclid FROM quote_submissions ORDER BY id DESC LIMIT 5;"
```
