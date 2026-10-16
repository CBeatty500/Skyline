// Nightly self-verification for Skyline.
// For each location in data/locations.json: open the real app headless, record its forecast for the next 7 days
// (before any learned correction), read the measured highs/lows/precipitation the app uses, score every saved forecast
// whose day has been measured, and publish per-location corrections to data/learning.json for the app to apply.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const locs = JSON.parse(fs.readFileSync(path.join(root, 'data/locations.json'), 'utf8'));
const snapFile = path.join(root, 'data/snapshots.json'), learnFile = path.join(root, 'data/learning.json');
const snaps = fs.existsSync(snapFile) ? JSON.parse(fs.readFileSync(snapFile, 'utf8')) : {};
const learning = fs.existsSync(learnFile) ? JSON.parse(fs.readFileSync(learnFile, 'utf8')) : { locations: {} };
const LEADS = ['0', '1', '2', '3+'], leadKey = l => l >= 3 ? '3+' : String(l);
const key = l => `${(+l.lat).toFixed(2)},${(+l.lon).toFixed(2)}`;
const nextDay = d => { const t = new Date(d + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 10); };

const browser = await chromium.launch();
for (const loc of locs) {
  const k = key(loc);
  const page = await browser.newPage();
  try {
    const url = `file://${path.join(root, 'index.html')}?city=${encodeURIComponent(loc.name)}&lat=${loc.lat}&lon=${loc.lon}&nolearn=1`;
    await page.goto(url, { timeout: 60000 });
    await page.waitForFunction(() => typeof bestBetResults !== 'undefined' && bestBetResults.length > 0, null, { timeout: 90000 });
    await page.waitForTimeout(12000);   // station climate, climate reports, radar
    const r = await page.evaluate(async () => ({
      today: ensembleData.daily.time[0],
      fc: bestBetResults.slice(0, 7).map(b => ({ date: b.date, max: b.learnRawMax ?? b.bestMax, min: b.learnRawMin ?? b.bestMin, pp: b.learnRawPP ?? b.precipProb, pr: b.bestPrecip ?? null })),
      meas: await measuredDays(),
      station: (cliTotals && cliTotals.station) || (nwsObs && nwsObs.stationId) || null
    }));
    // 1) save today's forecasts (first forecast per target day and lead)
    const st = snaps[k] || (snaps[k] = { name: loc.name, days: {} });
    r.fc.forEach((f, i) => {
      if (f.max == null) return;
      const d = st.days[f.date] || (st.days[f.date] = {});
      if (!d[i]) d[i] = { issued: r.today, max: f.max, min: f.min, pp: f.pp, pr: f.pr };
    });
    const cutoff = new Date(Date.now() - 90 * 864e5).toISOString().slice(0, 10);
    Object.keys(st.days).forEach(dt => { if (dt < cutoff) delete st.days[dt]; });
    // 2) score forecasts for measured days
    const L = learning.locations[k] || (learning.locations[k] = { name: loc.name, list: [] });
    const have = new Set(L.list.map(v => v.date + '|' + v.lead));
    Object.entries(st.days).forEach(([dt, leads]) => {
      if (dt >= r.today) return;
      const m = r.meas[dt], mN = r.meas[nextDay(dt)];
      if (!m) return;
      Object.entries(leads).forEach(([ld, f]) => {
        if (have.has(dt + '|' + ld)) return;
        const rec = { date: dt, lead: +ld };
        if (m.hi != null && f.max != null) rec.eMax = +(f.max - m.hi).toFixed(2);
        if (mN && mN.lo != null && nextDay(dt) < r.today && f.min != null) rec.eMin = +(f.min - mN.lo).toFixed(2);
        if (m.pr != null && f.pp != null) { rec.pp = f.pp; rec.wet = m.pr >= 0.25 ? 1 : 0; }
        if (rec.eMax == null && rec.eMin == null && rec.pp == null) return;
        L.list.push(rec); have.add(dt + '|' + ld);
      });
    });
    L.list = L.list.sort((a, b) => a.date < b.date ? -1 : 1).slice(-600);
    // 3) summarize and correct (same rules as the app)
    const buckets = {}, corr = {};
    LEADS.forEach(Lk => {
      const rows = L.list.filter(v => leadKey(v.lead) === Lk).slice(-40).reverse();
      let sMax = 0, sMin = 0, wMax = 0, wMin = 0, aMax = 0, aMin = 0, nMax = 0, nMin = 0, ppS = 0, wetS = 0, nP = 0;
      rows.forEach((x, i) => {
        const w = Math.pow(0.5, i / 10);
        if (x.eMax != null) { sMax += w * x.eMax; wMax += w; aMax += Math.abs(x.eMax); nMax++; }
        if (x.eMin != null) { sMin += w * x.eMin; wMin += w; aMin += Math.abs(x.eMin); nMin++; }
        if (x.pp != null) { ppS += x.pp / 100; wetS += x.wet; nP++; }
      });
      const b = buckets[Lk] = { nMax, nMin, nP, bMax: wMax ? sMax / wMax : 0, bMin: wMin ? sMin / wMin : 0, maeMax: nMax ? aMax / nMax : null, maeMin: nMin ? aMin / nMin : null, ppMean: nP ? ppS / nP : null, wetFreq: nP ? wetS / nP : null };
      const cap = x => Math.max(-3, Math.min(3, x));
      const ratio = nP >= 10 ? Math.max(0.75, Math.min(1.25, (b.wetFreq + 0.05) / (b.ppMean + 0.05))) : 1;
      corr[Lk] = { max: nMax >= 3 ? cap(-b.bMax * nMax / (nMax + 6)) : 0, min: nMin >= 3 ? cap(-b.bMin * nMin / (nMin + 6)) : 0, pp: 1 + (ratio - 1) * (nP / (nP + 10)) };
    });
    Object.assign(L, { lat: loc.lat, lon: loc.lon, station: r.station, buckets, corr, total: L.list.length, updated: new Date().toISOString() });
    console.log(`${loc.name}: ${r.fc.length} days saved, ${L.list.length} scored`);
  } catch (e) {
    console.log(`${loc.name}: skipped (${e.message})`);
  } finally { await page.close(); }
}
await browser.close();
learning.updated = new Date().toISOString();
fs.writeFileSync(snapFile, JSON.stringify(snaps));
fs.writeFileSync(learnFile, JSON.stringify(learning));
