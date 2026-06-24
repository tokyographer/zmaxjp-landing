/**
 * Z-MAX RFQ → Google Sheets sync (Apps Script Web App)
 *
 * Receives each new lead from /api/quote and appends it as a row.
 *
 * SETUP
 * 1. Create/open a Google Sheet. Note the tab (sheet) name — default "Leads".
 * 2. Extensions → Apps Script. Delete the default code, paste this file.
 * 3. Set SECRET below to a long random string (must match the
 *    SHEETS_WEBHOOK_TOKEN env var in Vercel).
 * 4. Deploy → New deployment → type "Web app".
 *      - Execute as:        Me
 *      - Who has access:    Anyone
 *    Copy the Web app URL (ends in /exec) → this is SHEETS_WEBHOOK_URL in Vercel.
 * 5. Re-deploy whenever you edit this script (Deploy → Manage deployments → edit → Deploy).
 */

const SECRET = 'REPLACE_WITH_A_LONG_RANDOM_STRING';
const SHEET_NAME = 'Leads';

const COLUMNS = [
  'created_at', 'name', 'company', 'email', 'application', 'quantity',
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
  'gclid', 'gad_source', 'first_seen', 'page_url', 'referer', 'user_agent', 'ip',
];

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    if (!SECRET || body.token !== SECRET) {
      return json_({ ok: false, error: 'forbidden' });
    }
    const rec = body.record || {};

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) sheet = ss.insertSheet(SHEET_NAME);

    if (sheet.getLastRow() === 0) {
      sheet.appendRow(COLUMNS);
      sheet.setFrozenRows(1);
    }

    sheet.appendRow(COLUMNS.map(function (c) {
      return rec[c] === undefined || rec[c] === null ? '' : rec[c];
    }));

    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
