import { neon } from '@neondatabase/serverless';

// Secured read-only export of leads for Google Sheets (pull model).
//   GET /api/leads?key=...            → JSON  { ok, count, columns, rows }
//   GET /api/leads?key=...&format=csv → text/csv
const COLUMNS = [
  'id', 'created_at', 'name', 'company', 'email', 'phone', 'application', 'quantity', 'locale',
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
  'gclid', 'gad_source', 'first_seen', 'page_url', 'referer', 'user_agent', 'ip',
];

function csvCell(v) {
  if (v === null || v === undefined) return '';
  const s = String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

export default async function handler(req, res) {
  const key = req.query?.key || req.headers['x-api-key'];
  if (!process.env.LEADS_API_KEY || key !== process.env.LEADS_API_KEY) {
    return res.status(403).json({ ok: false, error: 'Forbidden' });
  }
  if (!process.env.DATABASE_URL) {
    return res.status(500).json({ ok: false, error: 'Server not configured' });
  }

  let rows;
  try {
    const sql = neon(process.env.DATABASE_URL);
    rows = await sql`
      SELECT id, created_at, name, company, email, phone, application, quantity, locale,
             utm_source, utm_medium, utm_campaign, utm_term, utm_content,
             gclid, gad_source, first_seen, page_url, referer, user_agent, ip
      FROM quote_submissions
      ORDER BY id ASC`;
  } catch (err) {
    console.error('[leads] query failed:', err.message);
    return res.status(500).json({ ok: false, error: 'Query failed' });
  }

  if ((req.query?.format || '').toLowerCase() === 'csv') {
    const lines = [COLUMNS.join(',')];
    for (const r of rows) lines.push(COLUMNS.map((c) => csvCell(r[c])).join(','));
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    return res.status(200).send(lines.join('\n'));
  }

  return res.status(200).json({ ok: true, count: rows.length, columns: COLUMNS, rows });
}
