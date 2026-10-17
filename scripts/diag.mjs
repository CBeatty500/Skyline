// Diagnostic run of the live app for one place: forecast text over time, radar analysis, hourly chances, request timings.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const places = (process.env.PLACES || '39.0437,-77.4875,Ashburn, VA').split(';').map(p => { const [a, b, ...n] = p.split(','); return [a.trim(), b.trim(), n.join(',').trim()]; });
const browser = await chromium.launch();
const results = [];
for (const [lat, lon, name] of places) { try {
const page = await browser.newPage();
const errors = []; page.on('pageerror', e => errors.push(String(e))); page.on('console', m => { if (['warning', 'error'].includes(m.type())) errors.push(m.type() + ': ' + m.text().slice(0, 300)); });
const t0 = Date.now();
await page.goto(`file://${path.join(process.cwd(), 'index.html')}?city=${encodeURIComponent(name)}&lat=${lat}&lon=${lon}`, { timeout: 60000 });
await page.waitForFunction(() => typeof bestBetResults !== 'undefined' && bestBetResults.length > 0 && !document.getElementById('dashboardContent').classList.contains('hidden'), null, { timeout: 90000 });
const firstView = Date.now() - t0;
const snap = async label => page.evaluate(lbl => {
  const h = ensembleData.hourly, c = hourlyStart();
  return { label: lbl, narrative: document.getElementById('heroNarrative') && document.getElementById('heroNarrative').innerText,
    cond: (getCurrentConditions() || {}).text, radar: window._lastRadar || null, radarInfo: typeof radarInfo !== 'undefined' && radarInfo ? radarInfo.msg : null,
    hours: Array.from({ length: 12 }, (_, k) => ({ t: h.time[c + k].slice(11, 16), pp: h.precipitation_probability[c + k], code: h.weather_code[c + k], wet: hourWetCode(c + k), thunder: thunderAt(c + k), cc: Math.round(h.cloud_cover[c + k]), dry: !!(radarDry && radarDry[c + k]) })),
    spc: spcData && spcData.days ? spcData.days.slice(0, 1).map(d => ({ cat: d.cat, valid: d.valid })) : null,
    nowcast: obsNowcast(), obs: nwsObs ? { id: nwsObs.stationId, ts: nwsObs.timestamp, txt: nwsObs.textDescription } : null };
}, label);
const snaps = [await snap('first view')];
for (const s of [5, 15, 30]) { await page.waitForTimeout(s * 1000 - (s === 5 ? 0 : s === 15 ? 5000 : 15000)); snaps.push(await snap(`+${s}s`)); }
const timings = await page.evaluate(() => performance.getEntriesByType('resource').map(r => ({ url: r.name.replace(/\?.*/, '').slice(0, 110), start: Math.round(r.startTime), dur: Math.round(r.duration) })).sort((a, b) => b.dur - a.dur).slice(0, 30));
results.push({ name, at: new Date().toISOString(), firstViewMs: firstView, errors, snaps, timings: timings.slice(0, 8) });
await page.close();
} catch (e) { results.push({ name, error: String(e).slice(0, 300) }); } }
fs.writeFileSync('data/diag.json', JSON.stringify(results, null, 1));
await browser.close();
