/**
 * Z-MAX leads → Google Sheets (PULL model)
 *
 * This script runs inside YOUR account and fetches leads from the secured
 * /api/leads endpoint on a timer. It needs NO public Web App / "Anyone"
 * access, so it works even on Google Workspace accounts that block that.
 *
 * SETUP
 * 1. Open your Google Sheet → Extensions → Apps Script.
 * 2. Delete the default code, paste this file.
 * 3. Fill in API_KEY below (matches LEADS_API_KEY in Vercel).
 * 4. Run syncLeads() once (Run button). Approve the authorization prompt
 *    — this one is the normal "unverified app" screen → Advanced → Go to ...
 * 5. Run createHourlyTrigger() once to auto-refresh every hour.
 *    (Change the number in that function for a different cadence.)
 */

const API_URL = 'https://zmaxjp-landing.vercel.app/api/leads';
const API_KEY = 'REPLACE_WITH_LEADS_API_KEY';
const SHEET_NAME = 'Leads';

function syncLeads() {
  const resp = UrlFetchApp.fetch(API_URL + '?key=' + encodeURIComponent(API_KEY), {
    muteHttpExceptions: true,
  });
  if (resp.getResponseCode() !== 200) {
    throw new Error('API ' + resp.getResponseCode() + ': ' + resp.getContentText().slice(0, 200));
  }
  const data = JSON.parse(resp.getContentText());
  if (!data.ok) throw new Error('API error: ' + (data.error || 'unknown'));

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);

  const cols = data.columns;
  const values = [cols];
  data.rows.forEach(function (r) {
    values.push(cols.map(function (c) {
      return r[c] === null || r[c] === undefined ? '' : r[c];
    }));
  });

  // Full refresh: clear then write everything (mirrors the DB, reflects deletions).
  sheet.clearContents();
  sheet.getRange(1, 1, values.length, cols.length).setValues(values);
  sheet.setFrozenRows(1);
}

function createHourlyTrigger() {
  // remove existing triggers for this function to avoid duplicates
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncLeads') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('syncLeads').timeBased().everyHours(1).create();
}
