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

## Google Sheets sync (pull model)

The sheet pulls leads from a secured read endpoint on a timer. This avoids any
public Apps Script Web App ("Anyone" access), so it works on Google Workspace
accounts that block public web apps.

- **Endpoint:** `GET /api/leads?key=<LEADS_API_KEY>` → JSON (or `&format=csv`)
- **Sheet script:** `sheets-appscript.gs` runs `syncLeads()` on an hourly trigger,
  fetching the endpoint and doing a full refresh of the `Leads` tab.

**Setup**

1. Set the API key in Vercel (Production):

   ```bash
   vercel env add LEADS_API_KEY production
   vercel deploy --prod
   ```

2. Google Sheet → **Extensions → Apps Script**, paste `sheets-appscript.gs`,
   set `API_KEY` to the same value.
3. Run `syncLeads()` once (approve the auth prompt), then run
   `createHourlyTrigger()` once to auto-refresh every hour.

The full-refresh means the sheet always mirrors the DB (including deletions).

## Email notifications (Resend)

Every saved submission emails the sales team via Resend
(`api/quote.js` → `sendNotification()`). Best-effort: a mail failure never
blocks the lead (it's already in Neon and the user still sees the thank-you page).

- **Recipients:** set in code (`NOTIFY_TO` default), overridable via the
  `NOTIFY_TO` env var (comma-separated).
- **Reply-To** is the submitter's email, so replying goes straight to the lead.

**Setup**

1. Create a Resend account, **verify a sending domain** (e.g. `z-max.jp`) — required
   to deliver to external inboxes (Gmail, z-max.jp, …).
2. Add env vars in Vercel (Production):

   ```bash
   vercel env add RESEND_API_KEY production    # re_...
   vercel env add MAIL_FROM       production    # e.g. "Z-MAX RFQ <rfq@z-max.jp>"
   vercel deploy --prod
   ```

> Without a verified domain, Resend's `onboarding@resend.dev` only delivers to the
> Resend account owner — fine for a smoke test, not for the live recipient list.

## Multilingual (en / de / ja)

The site ships in English (`/`), German (`/de`), and Japanese (`/ja`).

- **Source of truth:** `i18n/base.template.html` (English page) + the translation
  map in `i18n/build.py`.
- **Build:** `python3 i18n/build.py` regenerates `index.html`, `de.html`, `ja.html`
  (adds the language switcher, `hreflang` tags, per-language canonical, and a
  hidden `locale` field). Use `--check` for a dry run.
- **Editing copy:** change English in `base.template.html` and/or the `T` / `ATTR`
  dicts in `build.py`, then rerun the build. Never hand-edit `de.html` / `ja.html`.
- **Lead language** is captured in the `locale` column (en/de/ja).

> Translations are first-draft — have a native speaker review the German and
> Japanese technical terms before launch.

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
