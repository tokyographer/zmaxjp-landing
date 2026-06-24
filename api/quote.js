import { neon } from '@neondatabase/serverless';

// ── config ──────────────────────────────────────────────────────────
const MAX_BODY_BYTES = 16 * 1024;          // reject oversized payloads
const MIN_ELAPSED_MS = 2000;               // time-trap: bots submit instantly
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^\+?[1-9]\d{6,14}$/;     // E.164-style, requires country/area code
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

// Lead notification recipients. Override with NOTIFY_TO (comma-separated).
const NOTIFY_TO = (process.env.NOTIFY_TO ||
  'kojirotani522@gmail.com,takai@z-max.jp,zmaxjapan@gmail.com,ando@z-max.jp,obana@haaarouti.com'
).split(',').map((s) => s.trim()).filter(Boolean);
// Verified Resend sender. Set MAIL_FROM to e.g. "Z-MAX RFQ <rfq@z-max.jp>".
const MAIL_FROM = process.env.MAIL_FROM || 'Z-MAX RFQ <onboarding@resend.dev>';

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

function esc(s) {
  return String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

// Email the lead to the sales team via Resend. Best-effort: a failure is
// logged but never affects the (already-stored) submission.
async function sendNotification(lead) {
  if (!process.env.RESEND_API_KEY) return;
  const rows = [
    ['Name', lead.name], ['Company', lead.company], ['Email', lead.email],
    ['Phone', lead.phone], ['Quantity', lead.quantity], ['Language', lead.locale],
    ['Application', lead.application],
    ['Source', [lead.utm_source, lead.utm_medium, lead.utm_campaign].filter(Boolean).join(' / ')],
    ['gclid', lead.gclid], ['Page', lead.page_url],
  ];
  const html = '<h2>New RFQ — Z-MAX</h2><table cellpadding="6" style="border-collapse:collapse">'
    + rows.filter(([, v]) => v).map(([k, v]) =>
        `<tr><td style="border:1px solid #ddd"><b>${esc(k)}</b></td><td style="border:1px solid #ddd">${esc(v)}</td></tr>`).join('')
    + '</table>';
  const text = rows.filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`).join('\n');
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 6000);
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: MAIL_FROM,
        to: NOTIFY_TO,
        reply_to: lead.email,
        subject: `New RFQ: ${lead.company || lead.name}`,
        html, text,
      }),
      signal: ctrl.signal,
    });
    clearTimeout(t);
    if (!res.ok) console.error('[quote] email HTTP', res.status, await res.text());
  } catch (err) {
    console.error('[quote] email failed:', err.message);
  }
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
  const locale = ['en', 'de', 'ja'].includes(body.locale) ? body.locale : null;

  const errors = {};
  if (!name) errors.name = 'required';
  if (!email) errors.email = 'required';
  else if (!EMAIL_RE.test(email)) errors.email = 'invalid';
  if (!phone) errors.phone = 'required';
  else if (!PHONE_RE.test(phone.replace(/[\s().-]/g, ''))) errors.phone = 'invalid';
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
        (name, company, email, phone, application, quantity, locale,
         utm_source, utm_medium, utm_campaign, utm_term, utm_content,
         gclid, gad_source, first_seen,
         page_url, referer, user_agent, ip)
      VALUES
        (${name}, ${company}, ${email}, ${phone}, ${application}, ${quantity}, ${locale},
         ${attr.utm_source}, ${attr.utm_medium}, ${attr.utm_campaign}, ${attr.utm_term}, ${attr.utm_content},
         ${attr.gclid}, ${attr.gad_source}, ${firstSeen},
         ${pageUrl}, ${referer}, ${userAgent}, ${ip})
    `;
  } catch (err) {
    console.error('[quote] insert failed:', err.message);
    return res.status(500).json({ ok: false, error: 'Could not save submission' });
  }

  await sendNotification({
    name, company, email, phone, application, quantity, locale,
    utm_source: attr.utm_source, utm_medium: attr.utm_medium, utm_campaign: attr.utm_campaign,
    gclid: attr.gclid, page_url: pageUrl,
  });

  return res.status(200).json({ ok: true, redirect: REDIRECT_PATH });
}
