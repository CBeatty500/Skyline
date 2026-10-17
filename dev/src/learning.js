        // ---------- Self-verification and learning (stored on this device) ----------
        // Every load saves the forecast for the coming days (before any learned correction). Once a day has been measured
        // (NWS climate report, else the observing station's daily summary) each saved forecast is scored. The running errors,
        // by lead time, become small corrections: a shrunk bias for highs and lows, and a reliability factor for rain chances.
        let learnState = null;   // { buckets: {lead: {n, bMax, bMin, maeMax, maeMin, pp, wet}}, corr: {...} }
        const LEARN_LEADS = ['0', '1', '2', '3+'];
        const leadKey = l => l >= 3 ? '3+' : String(l);
        function learnLocKey() { return `${(+currentLoc.lat).toFixed(2)},${(+currentLoc.lon).toFixed(2)}`; }
        async function saveForecastSnapshot() {
            if (!bestBetResults || !bestBetResults.length || !ensembleData || NOLEARN) return;
            const k = 'fcs1:' + learnLocKey(), today = ensembleData.daily.time[0];
            const st = (await idb.get(k)) || { days: {} };
            bestBetResults.slice(0, 7).forEach((b, i) => {
                if (b.bestMax == null) return;
                const d = st.days[b.date] || (st.days[b.date] = {});
                const L = String(i);
                if (d[L] && d[L].issued === today) { /* keep the first forecast made on each day for each lead */ }
                if (!d[L] || d[L].issued !== today) {
                    if (!d[L] || d[L].issued < today) d[L] = { issued: today, max: b.learnRawMax ?? b.bestMax, min: b.learnRawMin ?? b.bestMin, pp: b.learnRawPP ?? b.precipProb, pr: b.learnRawPR ?? b.bestPrecip ?? null };
                }
            });
            // keep 60 days
            const cutoff = new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10);
            Object.keys(st.days).forEach(dt => { if (dt < cutoff) delete st.days[dt]; });
            await idb.set(k, st);
        }
        // measured daily values (°C, mm) for past dates: NWS climate report first, else the station's own daily summary
        async function measuredDays() {
            const out = {};
            const F = f => (f - 32) / 1.8;
            if (cliTotals && cliTotals.rows) cliTotals.rows.forEach(o => {
                const hi = cliVal(o.high), lo = cliVal(o.low), p = cliVal(o.precip);
                out[o.valid] = { hi: hi ? F(hi.v) : null, lo: lo ? F(lo.v) : null, pr: p ? p.v * 25.4 : null };
            });
            try {
                const y = +ensembleData.daily.time[0].slice(0, 4);
                const rows = await iemDailyObs(y, null);
                (rows || []).forEach(o => {
                    if (out[o.valid]) return;
                    const hi = parseFloat(o.high), lo = parseFloat(o.low), p = o.precip === 'T' ? 0 : parseFloat(o.precip);
                    out[o.valid] = { hi: isFinite(hi) ? F(hi) : null, lo: isFinite(lo) ? F(lo) : null, pr: isFinite(p) ? p * 25.4 : null };
                });
            } catch (e) {}
            return out;
        }
        // shared nightly verification published by the repository's GitHub Action (all devices, every day)
        let sharedLearnP = null;
        function sharedLearning() {
            if (!sharedLearnP) sharedLearnP = fetch('https://raw.githubusercontent.com/CBeatty500/Skyline/main/data/learning.json', { cache: 'no-cache' })
                .then(r => r.ok ? r.json() : null).catch(() => null);
            return sharedLearnP;
        }
        const NOLEARN = /[?&]nolearn=1/.test(location.search);
        async function updateLearning() {
            if (!ensembleData || NOLEARN) return;
            const loc = learnLocKey(), today = ensembleData.daily.time[0];
            const st = (await idb.get('fcs1:' + loc)) || { days: {} };
            const meas = await measuredDays();
            const vk = 'fcv1:' + loc, ver = (await idb.get(vk)) || { list: [] };
            const have = new Set(ver.list.map(v => v.date + '|' + v.lead));
            const next = dt => { const t = new Date(dt + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 10); };
            Object.entries(st.days).forEach(([dt, leads]) => {
                if (dt >= today) return;
                const m = meas[dt], mN = meas[next(dt)];   // the forecast low is the overnight low into the next morning
                if (!m) return;
                Object.entries(leads).forEach(([L, f]) => {
                    if (have.has(dt + '|' + L)) return;
                    const rec = { date: dt, lead: +L };
                    if (m.hi != null && f.max != null) rec.eMax = f.max - m.hi;
                    if (mN && mN.lo != null && next(dt) < today && f.min != null) rec.eMin = f.min - mN.lo;
                    if (m.pr != null && f.pp != null) { rec.pp = f.pp; rec.wet = m.pr >= 0.25 ? 1 : 0; }
                    if (rec.eMax == null && rec.eMin == null && rec.pp == null) return;
                    ver.list.push(rec); have.add(dt + '|' + L);
                });
            });
            ver.list = ver.list.sort((a, b) => a.date < b.date ? -1 : 1).slice(-400);
            await idb.set(vk, ver);
            // summarize by lead, most recent first, with a 10-case half-life
            const buckets = {};
            LEARN_LEADS.forEach(L => {
                const rows = ver.list.filter(v => leadKey(v.lead) === L).slice(-40).reverse();
                let sw = 0, sMax = 0, sMin = 0, wMax = 0, wMin = 0, aMax = 0, aMin = 0, nMax = 0, nMin = 0, ppS = 0, wetS = 0, nP = 0;
                rows.forEach((r, i) => {
                    const w = Math.pow(0.5, i / 10);
                    if (r.eMax != null) { sMax += w * r.eMax; wMax += w; aMax += Math.abs(r.eMax); nMax++; }
                    if (r.eMin != null) { sMin += w * r.eMin; wMin += w; aMin += Math.abs(r.eMin); nMin++; }
                    if (r.pp != null) { ppS += r.pp / 100; wetS += r.wet; nP++; }
                    sw += w;
                });
                buckets[L] = { nMax, nMin, nP, bMax: wMax ? sMax / wMax : 0, bMin: wMin ? sMin / wMin : 0, maeMax: nMax ? aMax / nMax : null, maeMin: nMin ? aMin / nMin : null,
                               ppMean: nP ? ppS / nP : null, wetFreq: nP ? wetS / nP : null };
            });
            const cap = x => Math.max(-3, Math.min(3, x));
            const corr = {};
            LEARN_LEADS.forEach(L => {
                const b = buckets[L];
                const ratio = (b.nP >= 10) ? Math.max(0.75, Math.min(1.25, (b.wetFreq + 0.05) / (b.ppMean + 0.05))) : 1;
                corr[L] = { max: b.nMax >= 3 ? cap(-b.bMax * b.nMax / (b.nMax + 6)) : 0, min: b.nMin >= 3 ? cap(-b.bMin * b.nMin / (b.nMin + 6)) : 0,
                            pp: 1 + (ratio - 1) * (b.nP / (b.nP + 10)) };
            });
            learnState = { buckets, corr, total: ver.list.length };
            try {
                const best = await sharedEntryFor(currentLoc.lat, currentLoc.lon);
                if (best && best.corr && (best.total || 0) >= learnState.total) learnState = { buckets: best.buckets, corr: best.corr, total: best.total, shared: true, updated: best.updated };
            } catch (e) {}
            // nationwide daily corrections (US): the full nationwide value with no local cases, fading as local cases grow
            try {
                const sh = await sharedLearning(), nat = sh && sh.national && sh.national.daily;
                if (nat && typeof nwsOffice !== 'undefined' && nwsOffice) {
                    const corr = {};
                    LEARN_LEADS.forEach(L => {
                        const c = learnState.corr[L] || { max: 0, min: 0, pp: 1 }, n = nat[L] || { max: 0, min: 0, pp: 1 }, b = (learnState.buckets && learnState.buckets[L]) || {};
                        corr[L] = { ...c, max: (c.max || 0) + (n.max || 0) * 6 / ((b.nMax || 0) + 6), min: (c.min || 0) + (n.min || 0) * 6 / ((b.nMin || 0) + 6),
                                    pp: (c.pp || 1) * (1 + ((n.pp || 1) - 1) * 10 / ((b.nP || 0) + 10)) };
                    });
                    learnState = { ...learnState, corr, nationwide: true };
                }
            } catch (e) {}
        }
        // apply learned corrections (leads 1+ for highs; tonight's low counts as lead 0)
        function applyLearning() {
            if (!learnState || !bestBetResults || NOLEARN) return;
            bestBetResults.forEach((b, i) => {
                const c = learnState.corr[leadKey(i)]; if (!c) return;
                b.learnRawMax = b.bestMax; b.learnRawMin = b.bestMin; b.learnRawPP = b.precipProb; b.learnRawPR = b.bestPrecip;
                if (i >= 1 && b.bestPrecip != null && c.pr && c.pr !== 1) b.bestPrecip = b.bestPrecip * c.pr;
                if (i >= 1 && b.bestMax != null) b.bestMax += c.max;
                if (b.bestMin != null) b.bestMin += c.min;
                if (i >= 1 && b.precipProb != null && c.pp !== 1) b.precipProb = Math.max(0, Math.min(100, Math.round(b.precipProb * c.pp)));
                b.learned = { max: i >= 1 ? c.max : 0, min: c.min, pp: i >= 1 ? c.pp : 1, pr: i >= 1 ? (c.pr || 1) : 1 };
            });
        }
        function learningHTML() {
            if (!learnState) return '<div class="text-xs text-slate-400">Collecting forecasts to score. Corrections start after a few days of measured results for this location.</div>';
            const dU = isImperial ? 1.8 : 1, u = isImperial ? '°F' : '°C';
            const f = (x, sign) => x == null ? '--' : `${sign && x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(x * dU).toFixed(1)}${u}`;
            const lbl = { '0': 'Today / tonight', '1': 'Tomorrow', '2': 'Day 2', '3+': 'Days 3+' };
            const rows = LEARN_LEADS.map(L => {
                const b = learnState.buckets[L], c = learnState.corr[L];
                return `<tr><td class="p-2 text-slate-200">${lbl[L]}</td><td class="p-2">${Math.max(b.nMax, b.nMin)}</td>
                    <td class="p-2">${b.nMax ? `${f(b.bMax, true)} <span class="text-slate-500">(${f(b.maeMax)})</span>` : '--'}</td>
                    <td class="p-2">${b.nMin ? `${f(b.bMin, true)} <span class="text-slate-500">(${f(b.maeMin)})</span>` : '--'}</td>
                    <td class="p-2">${b.nP ? `${Math.round(b.ppMean * 100)}% vs ${Math.round(b.wetFreq * 100)}%` : '--'}</td>
                    <td class="p-2 text-amber-300">${(c.max || c.min || (L !== '0' && (c.pp !== 1 || (c.pr && c.pr !== 1)))) ? [L !== '0' && c.max ? `high ${f(c.max, true)}` : '', c.min ? `low ${f(c.min, true)}` : '', c.pp !== 1 && L !== '0' ? `rain chance ×${c.pp.toFixed(2)}` : '', c.pr && c.pr !== 1 && L !== '0' ? `rain amount ×${c.pr.toFixed(2)}` : ''].filter(Boolean).join(', ') : '<span class="text-slate-500">none yet</span>'}</td></tr>`;
            }).join('');
            return `<div class="overflow-x-auto"><table class="w-full text-xs font-mono text-slate-300"><thead class="text-[10px] uppercase text-slate-400"><tr>
                <th class="p-2 text-left">Lead</th><th class="p-2 text-left">Cases</th><th class="p-2 text-left">High bias (avg miss)</th><th class="p-2 text-left">Low bias (avg miss)</th><th class="p-2 text-left">Rain chance vs observed</th><th class="p-2 text-left">Correction applied</th></tr></thead><tbody>${rows}</tbody></table></div>
                <div class="text-[11px] text-slate-400 mt-2">Bias = forecast minus measured, recent cases weighted most. Corrections grow with the number of cases and are capped at ±3°C (±5.4°F); rain chances are scaled only after 10+ scored days. ${learnState.shared ? `From the shared nightly verification (${learnState.total} scored forecasts, updated ${new Date(learnState.updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}).` : `Stored on this device for this location (${learnState.total} scored forecasts).`}</div>`;
        }

