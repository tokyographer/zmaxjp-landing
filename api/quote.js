import { neon } from '@neondatabase/serverless';

// ── config ──────────────────────────────────────────────────────────
const MAX_BODY_BYTES = 16 * 1024;          // reject oversized payloads
const MIN_ELAPSED_MS = 2000;               // time-trap: bots submit instantly
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const REDIRECT_PATH = '/thank-you';

const FIELD_LIMITS = {
  name: 200,
  company: 200,
  email: 320,
  phone: 50,
  application: 5000,
  quantity: 100,
};

const ATTRIBUTION_KEYS = [
  'utm_source', 'utm_medium', 'utm_campaign',
  'utm_term', 'utm_content', 'gclid', 'gad_source',
];

// ── helpers ─────────────────────────────────────────────────────────
function clean(value, max) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.slice(0, max);
}

function clientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (typeof fwd === 'string' && fwd.length) return fwd.split(',')[0].trim();
  return req.socket?.remoteAddress || null;
}

// ── handler ─────────────────────────────────────────────────────────
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, error: 'Method not allowed' });
  }

  let body = req.body;
  if (typeof body === 'string') {
    if (Buffer.byteLength(body) > MAX_BODY_BYTES) {
      return res.status(413).json({ ok: false, error: 'Payload too large' });
    }
    try { body = JSON.parse(body); } catch { body = null; }
  }
  if (!body || typeof body !== 'object') {
    return res.status(400).json({ ok: false, error: 'Invalid request body' });
  }

  // ── spam protection ───────────────────────────────────────────────
  // 1. Honeypot: a hidden field real users never see or fill.
  if (clean(body.company_url, 200)) {
    return res.status(200).json({ ok: true, redirect: REDIRECT_PATH }); // silently drop
  }
  // 2. Time-trap: instant submits are almost always bots.
  const elapsed = Number(body.elapsed_ms);
  if (Number.isFinite(elapsed) && elapsed >= 0 && elapsed < MIN_ELAPSED_MS) {
    return res.status(200).json({ ok: true, redirect: REDIRECT_PATH });
  }

  // ── validation ────────────────────────────────────────────────────
  const name = clean(body.name, FIELD_LIMITS.name);
  const company = clean(body.company, FIELD_LIMITS.company);
  const email = clean(body.email, FIELD_LIMITS.email);
  const phone = clean(body.phone, FIELD_LIMITS.phone);
  const application = clean(body.application, FIELD_LIMITS.application);
  const quantity = clean(body.quantity, FIELD_LIMITS.quantity);

  const errors = {};
  if (!name) errors.name = 'required';
  if (!company) errors.company = 'required';
  if (!email) errors.email = 'required';
  else if (!EMAIL_RE.test(email)) errors.email = 'invalid';
  if (!application) errors.application = 'required';
  if (Object.keys(errors).length) {
    return res.status(422).json({ ok: false, error: 'Validation failed', fields: errors });
  }

  // ── attribution ───────────────────────────────────────────────────
  const attr = {};
  for (const key of ATTRIBUTION_KEYS) attr[key] = clean(body[key], 500);
  let firstSeen = clean(body.first_seen, 40);
  if (firstSeen && Number.isNaN(Date.parse(firstSeen))) firstSeen = null;

  if (!process.env.DATABASE_URL) {
    console.error('[quote] DATABASE_URL is not set');
    return res.status(500).json({ ok: false, error: 'Server not configured' });
  }

  const pageUrl = clean(body.page_url, 2000);
  const referer = clean(req.headers.referer, 2000);
  const userAgent = clean(req.headers['user-agent'], 1000);
  const ip = clientIp(req);

  // ── persist ───────────────────────────────────────────────────────
  try {
    const sql = neon(process.env.DATABASE_URL);
    await sql`
      INSERT INTO quote_submissions
        (name, company, email, phone, application, quantity,
         utm_source, utm_medium, utm_campaign, utm_term, utm_content,
         gclid, gad_source, first_seen,
         page_url, referer, user_agent, ip)
      VALUES
        (${name}, ${company}, ${email}, ${phone}, ${application}, ${quantity},
         ${attr.utm_source}, ${attr.utm_medium}, ${attr.utm_campaign}, ${attr.utm_term}, ${attr.utm_content},
         ${attr.gclid}, ${attr.gad_source}, ${firstSeen},
         ${pageUrl}, ${referer}, ${userAgent}, ${ip})
    `;
  } catch (err) {
    console.error('[quote] insert failed:', err.message);
    return res.status(500).json({ ok: false, error: 'Could not save submission' });
  }

  return res.status(200).json({ ok: true, redirect: REDIRECT_PATH });
}
