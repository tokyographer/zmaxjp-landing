# Z-MAX Landing — Quote Request

A self-contained, single-file landing page for **Z-MAX** custom thermoelectric (Peltier) coolers, with a quote-request call to action. The entire page — markup, styles, and scripts — ships in single bundled `index.html` file plus a serverless API for form handling.

## Contents

- `index.html` — the complete landing page (self-unpacking bundle, no build step)
- `api/quote.js` — serverless endpoint that stores RFQ submissions in Neon Postgres
- `thank-you.html` — post-submit conversion page (served at `/thank-you`)
- `schema.sql` — Neon database schema for `quote_submissions`

## RFQ form → Neon Postgres

The quote-request form posts to `/api/quote`, which validates input, applies spam
protection, captures Google Ads attribution (`utm_*`, `gclid`), stores the
submission in Neon, and redirects to `/thank-you` for conversion tracking.

**Setup is documented in [INTEGRATION.md](INTEGRATION.md).** In short: create a Neon
DB, run `psql "$DATABASE_URL" -f schema.sql`, set `DATABASE_URL` in Vercel env vars,
and deploy.

## Usage

Open the file locally:

```bash
open index.html
```

Or serve it with any static server:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/index.html
```

## Deployment

Deploy to **Vercel** so the `/api/quote` serverless function and Neon integration work:

```bash
vercel deploy --prod
```

Set the `DATABASE_URL` environment variable and apply `schema.sql` first — see
[INTEGRATION.md](INTEGRATION.md). The static page alone can be hosted anywhere, but
form submissions require the Vercel function + Neon backend.

## License

See [LICENSE](LICENSE).
