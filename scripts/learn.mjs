// Forecast self-verification for Skyline (runs several times a day from .github/workflows/learn.yml).
// For each location in data/locations.json the real app is opened headless and its forecast recorded before any learned
// correction: highs, lows, rain chance and amount for the next 7 days, and every hour for the next 72 hours (temperature,
// dewpoint, wind, gusts, cloud cover, rain chance). Past days are scored against the measured daily values the app uses
// (NWS climate report or the station's daily summary); past hours against the station's own observations (NWS API).
// The running errors become per-location corrections in data/learning.json, which the app applies.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const rd = (f, d) => { const p = path.join(root, f); try { return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : d; } catch (e) { return d; } };
const locs = rd('data/locations.json', []);
const snaps = rd('data/snapshots.json', {});
const hsnaps = rd('data/hourly_snaps.json', {});
const learning = rd('data/learning.json', { locations: {} });
const LEADS = ['0', '1', '2', '3+'], leadKey = l => l >= 3 ? '3+' : String(l);
const hlLead = hrs => hrs < 6 ? '0-6' : hrs < 24 ? '6-24' : hrs < 48 ? '24-48' : '48+';
const key = l => `${(+l.lat).toFixed(2)},${(+l.lon).toFixed(2)}`;
const nextDay = d => { const t = new Date(d + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 10); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ok = v => v !== null && v !== undefined && !Number.isNaN(v);
const UA = { 'User-Agent': '(Skyline forecast verification, github.com/CBeatty500/Skyline)', Accept: 'application/geo+json' };

// ---- station observations, last 7 days ----
const COVER = { SKC: 0, CLR: 0, FEW: 19, SCT: 44, BKN: 75, OVC: 100, VV: 100 };
const WET = /rain|drizzle|snow|thunder|shower|sleet|hail|pellets|graupel|ice/i;
async function stationObs(id) {
  const start = new Date(Date.now() - 7 * 864e5).toISOString().replace(/\.\d+Z$/, 'Z');
  for (let a = 0; a < 3; a++) {
    try {
      const r = await fetch(`https://api.weather.gov/stations/${id}/observations?start=${start}&limit=500`, { headers: UA, signal: AbortSignal.timeout(30000) });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json();
      const val = q => q && ok(q.value) ? (q.unitCode && /m_s/.test(q.unitCode) ? q.value * 3.6 : q.value) : null;
      return (j.features || []).map(f => f.properties).filter(p => p && p.timestamp).map(p => {
        const layers = Array.isArray(p.cloudLayers) ? p.cloudLayers : [];
        const cc = layers.length ? Math.max(...layers.map(l => COVER[l.amount] ?? 0)) : null;
        const pw = Array.isArray(p.presentWeather) ? p.presentWeather : [];
        const pl = val(p.precipitationLastHour);
        return { ms: Date.parse(p.timestamp), t: val(p.temperature), td: val(p.dewpoint), ws: val(p.windSpeed), wg: val(p.windGust), cc,
                 wet: (pl !== null && pl >= 0.25) || pw.some(w => WET.test(`${w.weather || ''} ${w.rawString || ''}`)) ? 1 : 0 };
      });
    } catch (e) { if (a === 2) { console.log(`  obs ${id}: ${e.message}`); return []; } await sleep(5000); }
  }
}

// ---- running, recency-weighted error statistics (each new case multiplies the old weights by DECAY) ----
const DECAY = 0.985;
function addCase(cell, v, x) {
  const s = cell[v] || (cell[v] = { w: 0, s: 0, a: 0, o: 0, f: 0, p: 0, n: 0 });
  for (const k of ['w', 's', 'a', 'o', 'f', 'p']) s[k] *= DECAY;
  s.w += 1; s.n++;
  if ('e' in x) { s.s += x.e; s.a += Math.abs(x.e); }
  if ('obs' in x) { s.o += x.obs; s.f += x.fc; }
  if ('pp' in x) { s.p += x.pp; s.o += x.wet; }
}
function hourlyCorr(cell) {
  const cap = (x, m) => Math.max(-m, Math.min(m, x));
  const add = (a, m) => a && a.w >= 6 ? +cap(-(a.s / a.w) * a.w / (a.w + 24), m).toFixed(2) : 0;
  const ratio = (a, lo, hi) => { if (!a || a.w < 6 || a.f <= 0) return 1; const r = Math.max(lo, Math.min(hi, a.o / a.f)); return +(1 + (r - 1) * a.w / (a.w + 24)).toFixed(3); };
  let pp = 1;
  if (cell.pp && cell.pp.w >= 24) { const r = Math.max(0.75, Math.min(1.25, (cell.pp.o / cell.pp.w + 0.05) / (cell.pp.p / cell.pp.w + 0.05))); pp = +(1 + (r - 1) * cell.pp.w / (cell.pp.w + 48)).toFixed(3); }
  return { t: add(cell.t, 3), td: add(cell.td, 3), cc: add(cell.cc, 20), ws: ratio(cell.ws, 0.75, 1.25), wg: ratio(cell.wg, 0.75, 1.25), pp };
}

async function loadPage(browser, loc) {
  let lastErr = null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const page = await browser.newPage();
    try {
      const url = `file://${path.join(root, 'index.html')}?city=${encodeURIComponent(loc.name)}&lat=${loc.lat}&lon=${loc.lon}&nolearn=1`;
      await page.goto(url, { timeout: 60000 });
      await page.waitForFunction(() => typeof bestBetResults !== 'undefined' && bestBetResults.length > 0, null, { timeout: 90000 });
      await page.waitForTimeout(12000);   // station climate, climate reports
      return await page.evaluate(async () => {
        const h = ensembleData.hourly, raw = h._raw || h, cur = hourlyStart(), off = (ensembleData.utc_offset_seconds || 0) * 1000;
        const hrs = [];
        for (let j = cur; j < Math.min(h.time.length, cur + 73); j++) {
          const g = (f) => raw[f] && raw[f][j] != null ? +(+raw[f][j]).toFixed(2) : null;
          const w = f => { const v = _modelWindAtRaw(f, j); return v == null || isNaN(v) ? null : +v.toFixed(1); };
          hrs.push({ ms: Date.parse(h.time[j] + ':00Z') - off, d: h.is_day && h.is_day[j] ? 1 : 0, t: g('temperature_2m'), td: g('dew_point_2m'), cc: g('cloud_cover'), pp: g('precipitation_probability'), ws: w('wind_speed_10m'), wg: w('wind_gusts_10m') });
        }
        return {
          today: ensembleData.daily.time[0],
          fc: bestBetResults.slice(0, 7).map(b => ({ date: b.date, max: b.learnRawMax ?? b.bestMax, min: b.learnRawMin ?? b.bestMin, pp: b.learnRawPP ?? b.precipProb, pr: b.learnRawPR ?? b.bestPrecip ?? null })),
          meas: await measuredDays(),
          obsStation: nwsObs && nwsObs.stationId || null,
          station: (cliTotals && cliTotals.station) || (nwsObs && nwsObs.stationId) || null,
          hrs
        };
      });
    } catch (e) { lastErr = e; await sleep(20000); }
    finally { await page.close(); }
  }
  throw lastErr || new Error('load failed');
}

const browser = await chromium.launch();
for (const loc of locs) {
  const k = key(loc);
  let r;
  try { r = await loadPage(browser, loc); } catch (e) { console.log(`${loc.name}: skipped (${e.message})`); continue; }
  await sleep(4000);
  const L = learning.locations[k] || (learning.locations[k] = { name: loc.name, list: [] });
  try {
    // ---------- daily: highs, lows, rain chance and amount ----------
    const st = snaps[k] || (snaps[k] = { name: loc.name, days: {} });
    r.fc.forEach((f, i) => {
      if (f.max == null) return;
      const d = st.days[f.date] || (st.days[f.date] = {});
      if (!d[i]) d[i] = { issued: r.today, max: f.max, min: f.min, pp: f.pp, pr: f.pr };   // first forecast per day and lead
    });
    const cutoff = new Date(Date.now() - 90 * 864e5).toISOString().slice(0, 10);
    Object.keys(st.days).forEach(dt => { if (dt < cutoff) delete st.days[dt]; });
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
        if (m.pr != null && f.pr != null) { rec.prF = +(+f.pr).toFixed(2); rec.prO = +(+m.pr).toFixed(2); }
        if (rec.eMax == null && rec.eMin == null && rec.pp == null) return;
        L.list.push(rec); have.add(dt + '|' + ld);
      });
    });
    L.list = L.list.sort((a, b) => a.date < b.date ? -1 : 1).slice(-600);
    const buckets = {}, corr = {};
    LEADS.forEach(Lk => {
      const rows = L.list.filter(v => leadKey(v.lead) === Lk).slice(-40).reverse();
      let sMax = 0, sMin = 0, wMax = 0, wMin = 0, aMax = 0, aMin = 0, nMax = 0, nMin = 0, ppS = 0, wetS = 0, nP = 0, prF = 0, prO = 0, nR = 0;
      rows.forEach((x, i) => {
        const w = Math.pow(0.5, i / 10);
        if (x.eMax != null) { sMax += w * x.eMax; wMax += w; aMax += Math.abs(x.eMax); nMax++; }
        if (x.eMin != null) { sMin += w * x.eMin; wMin += w; aMin += Math.abs(x.eMin); nMin++; }
        if (x.pp != null) { ppS += x.pp / 100; wetS += x.wet; nP++; }
        if (x.prF != null && (x.prF >= 0.25 || x.prO >= 0.25)) { prF += x.prF; prO += x.prO; nR++; }
      });
      const b = buckets[Lk] = { nMax, nMin, nP, nR, bMax: wMax ? sMax / wMax : 0, bMin: wMin ? sMin / wMin : 0, maeMax: nMax ? aMax / nMax : null, maeMin: nMin ? aMin / nMin : null, ppMean: nP ? ppS / nP : null, wetFreq: nP ? wetS / nP : null, prRatio: nR && prF > 0 ? prO / prF : null };
      const cap = x => Math.max(-3, Math.min(3, x));
      const ratio = nP >= 10 ? Math.max(0.75, Math.min(1.25, (b.wetFreq + 0.05) / (b.ppMean + 0.05))) : 1;
      const prr = nR >= 8 && b.prRatio != null ? Math.max(0.7, Math.min(1.4, b.prRatio)) : 1;
      corr[Lk] = { max: nMax >= 3 ? cap(-b.bMax * nMax / (nMax + 6)) : 0, min: nMin >= 3 ? cap(-b.bMin * nMin / (nMin + 6)) : 0, pp: 1 + (ratio - 1) * (nP / (nP + 10)), pr: +(1 + (prr - 1) * (nR / (nR + 10))).toFixed(3) };
    });
    Object.assign(L, { lat: loc.lat, lon: loc.lon, station: r.station, buckets, corr, total: L.list.length, updated: new Date().toISOString() });

    // ---------- hourly: temperature, dewpoint, wind, gusts, cloud cover, rain ----------
    const now = Date.now();
    const hs = hsnaps[k] || (hsnaps[k] = { name: loc.name, hrs: {} });
    r.hrs.forEach(x => {
      const lead = hlLead(Math.max(0, (x.ms - now) / 36e5));
      const slot = hs.hrs[x.ms] || (hs.hrs[x.ms] = {});
      if (!slot[lead]) slot[lead] = { d: x.d, t: x.t, td: x.td, cc: x.cc, pp: x.pp, ws: x.ws, wg: x.wg };   // first forecast per hour and lead
    });
    // hourly checks use the location's main airport when one is listed, else the app's observing station
    const obsId = loc.station || r.obsStation;
    if (L.hourly && L.hourly.station && L.hourly.station !== obsId) delete L.hourly;   // a different station starts fresh
    const H = L.hourly || (L.hourly = { cells: {}, corr: {}, n: 0 });
    let scored = 0;
    if (obsId) {
      const obs = (await stationObs(obsId)).filter(o => ok(o.ms)).sort((a, b) => a.ms - b.ms);
      const near = ms => { let b = null; for (const o of obs) { const d = Math.abs(o.ms - ms); if (d <= 25 * 60e3 && (!b || d < Math.abs(b.ms - ms))) b = o; } return b; };
      const oldest = obs.length ? obs[0].ms : Infinity;
      Object.keys(hs.hrs).map(Number).sort((a, b) => a - b).forEach(ms => {
        if (ms > now - 45 * 60e3) return;                       // not observed yet
        const o = ms >= oldest ? near(ms) : null;
        if (o) Object.entries(hs.hrs[ms]).forEach(([lead, f]) => {
          const cell = H.cells[lead + '|' + (f.d ? 'd' : 'n')] || (H.cells[lead + '|' + (f.d ? 'd' : 'n')] = { n: 0 });
          cell.n++; scored++;
          if (ok(f.t) && ok(o.t)) addCase(cell, 't', { e: f.t - o.t });
          if (ok(f.td) && ok(o.td)) addCase(cell, 'td', { e: f.td - o.td });
          if (ok(f.ws) && ok(o.ws) && f.ws >= 8) addCase(cell, 'ws', { obs: o.ws, fc: f.ws });
          // gusts are only reported when they are 10 kt above the wind; with none reported the gust was at most wind + 10 kt
          if (ok(f.wg) && f.wg >= 15) { if (ok(o.wg)) addCase(cell, 'wg', { obs: o.wg, fc: f.wg }); else if (ok(o.ws) && f.wg > o.ws + 18.5) addCase(cell, 'wg', { obs: o.ws + 18.5, fc: f.wg }); }
          // the station's ceilometer sees up to 12,000 ft: a clear report only counts against a mostly cloudy forecast
          if (ok(f.cc) && ok(o.cc)) addCase(cell, 'cc', { e: o.cc === 0 ? Math.max(0, f.cc - 60) : f.cc - o.cc });
          if (ok(f.pp)) addCase(cell, 'pp', { pp: f.pp / 100, wet: o.wet });
        });
        if (o || ms < now - 7 * 864e5 || ms < oldest) delete hs.hrs[ms];
      });
    }
    Object.entries(H.cells).forEach(([c, cell]) => { H.corr[c] = hourlyCorr(cell); });
    H.n = (H.n || 0) + scored; H.station = obsId; H.updated = new Date().toISOString();
    console.log(`${loc.name}: ${r.fc.length} days and ${r.hrs.length} hours saved; ${L.list.length} days and ${H.n} hours scored (${scored} new)`);
  } catch (e) {
    console.log(`${loc.name}: scoring failed (${e.message})`);
  }
}
await browser.close();
learning.updated = new Date().toISOString();
fs.writeFileSync(path.join(root, 'data/snapshots.json'), JSON.stringify(snaps));
fs.writeFileSync(path.join(root, 'data/hourly_snaps.json'), JSON.stringify(hsnaps));
fs.writeFileSync(path.join(root, 'data/learning.json'), JSON.stringify(learning));
