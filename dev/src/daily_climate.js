        // ---------- shared helpers for the climate tables ----------
        function dcHelpers() {
            const n = v => v !== null && v !== undefined && !isNaN(v);
            const disp = c => isImperial ? Math.round(cToF(c)) : Math.round(c);
            const dep = (c, nc) => {
                if (!n(c) || !n(nc)) return '';
                const d = disp(c) - disp(nc);
                const col = d > 0 ? 'text-rose-300' : d < 0 ? 'text-sky-300' : 'text-slate-400';
                return `<span class="dep ${col}">${d > 0 ? '+' : d < 0 ? '−' : '±'}${Math.abs(d)}</span>`;
            };
            const recCell = (c, y, col) => n(c) ? `<span class="${col} font-semibold">${formatTemp(c)}</span> <span class="text-slate-400">${y ? '(' + y + ')' : ''}</span>` : '--';
            const dShift = (ds, k) => { const d = new Date(ds + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + k); return d.toISOString().slice(0, 10); };
            const dLabel = ds => new Date(ds + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            return { n, disp, dep, recCell, dShift, dLabel };
        }

        // ---------- Quick view: today + next 7 days, forecast against normals and records (sits under the hourly outlook) ----------
        function renderQuickView() {
            const tbody = document.getElementById('quickViewBody');
            if (!tbody || !bestBetResults || !bestBetResults.length) return;
            const { n, disp, dep, recCell, dLabel } = dcHelpers();
            const ni = nightInfo(), so = getTodaySoFar();
            const NEXT = Math.min(7, bestBetResults.length - 1);
            const rows = [];
            for (let i = 0; i <= NEXT; i++) {
                const b = bestBetResults[i], st = getHistoricalStatsForDate(b.date), isT = i === 0;
                const cond = (isT && ni) ? ni.cond : dailyCondition(b);
                const hiC = b.bestMax;
                // calendar-day low: today = lowest of what has been observed and what is still to come; later days = that morning's low
                const loC = isT ? (n(so.lo) ? Math.min(so.lo, b.bestMin) : b.bestMin) : bestBetResults[i - 1].bestMin;
                const fh = n(hiC) && st && n(st.recHigh) && disp(hiC) >= disp(st.recHigh);
                const fl = n(loC) && st && n(st.recLow) && disp(loC) <= disp(st.recLow);
                const pc = precipCell(i);
                const name = isT ? (ni ? 'Tonight' : 'Today') : new Date(b.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
                const md = new Date(b.date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                rows.push(`<tr class="${isT ? 'today' : ''}">
                    <td class="text-slate-200 font-bold"><span class="inline-block" style="min-width:4.6em;margin-right:6px">${name}</span><span class="text-slate-400 font-normal">${md}</span></td>
                    <td class="qv-ic" title="${esc(cond.text)}"><i class="fa-solid ${cond.icon} ${cond.color}"></i></td>
                    <td><span class="text-rose-200 font-semibold">${formatTemp(hiC)}</span>${st ? dep(hiC, st.normMax) : ''}${fh ? '<i class="fa-solid fa-trophy rec" title="At or above the record"></i>' : ''}</td>
                    <td><span class="text-sky-200 font-semibold">${formatTemp(loC)}</span>${st ? dep(loC, st.normMin) : ''}${fl ? '<i class="fa-solid fa-trophy rec" title="At or below the record"></i>' : ''}</td>
                    <td>${pc}</td>
                    <td class="text-teal-300">${st && n(st.normMax) && n(st.normMin) ? `${formatTemp(st.normMax)} / ${formatTemp(st.normMin)}` : '--'}</td>
                    <td>${st ? recCell(st.recHigh, st.recHighYr, 'text-rose-300') : '--'}</td>
                    <td>${st ? recCell(st.recLow, st.recLowYr, 'text-indigo-300') : '--'}</td>
                </tr>`);
            }
            tbody.innerHTML = rows.join('');
            const src = document.getElementById('quickViewSource');
            if (src) src.innerText = (cliTotals && cliTotals.byMD) ? `Normals & records: ${cliTotals.station} NWS climate reports` : '';
        }

        // ---------- Daily Climate: what was measured — today so far and the past 30 days (NWS climate report) ----------
        // ---------- Daily Climate: a calendar month of measured values (this month by default; any month/year on request) ----------
        let dcSel = null;            // { y, m } chosen in the month picker; null = the current month
        const dcMonthCache = {};     // station:YYYY-MM -> rows from ACIS
        function dcSelect() {
            const ms = document.getElementById('dcMonth'), ys = document.getElementById('dcYear');
            if (!ms || !ys || !bestBetResults || !bestBetResults.length) return;
            const today = bestBetResults[0].date, cy = +today.slice(0, 4), cm = +today.slice(5, 7);
            let y = +ys.value, m = +ms.value;
            if (y > cy || (y === cy && m > cm)) { m = cm; ms.value = String(m); }
            dcSel = (y === cy && m === cm) ? null : { y, m };
            renderDailyRecordsTable();
        }
        function dcFillPickers(today) {
            const ms = document.getElementById('dcMonth'), ys = document.getElementById('dcYear');
            if (!ms || !ys) return;
            const cy = +today.slice(0, 4), cm = +today.slice(5, 7);
            const first = Math.max(1872, +((stationClim && stationClim.recStart) || (cy - 75)));
            if (!ms.options.length) ms.innerHTML = Array.from({ length: 12 }, (_, i) => `<option value="${i + 1}">${new Date(2001, i, 15).toLocaleDateString('en-US', { month: 'long' })}</option>`).join('');
            const want = Array.from({ length: cy - first + 1 }, (_, i) => cy - i);
            if (ys.options.length !== want.length) ys.innerHTML = want.map(y => `<option value="${y}">${y}</option>`).join('');
            const y = dcSel ? dcSel.y : cy, m = dcSel ? dcSel.m : cm;
            ys.value = String(y); ms.value = String(m);
        }
        async function dcFetchMonth(y, m) {
            const stn = await resolveClimateStation(currentLoc.lat, currentLoc.lon, { obs: nwsObs }).catch(() => null);
            const ids = (stn && stn.ids) || [];
            const mm = String(m).padStart(2, '0'), last = new Date(Date.UTC(y, m, 0)).getUTCDate();
            const key = `${ids[0] || (nwsObs && nwsObs.stationId) || 'x'}:${y}-${mm}`;
            if (dcMonthCache[key]) return dcMonthCache[key];
            for (const sid of ids) {
                try {
                    const r = await fetch(`${ACIS}/StnData?sid=${encodeURIComponent(sid)}&sdate=${y}-${mm}-01&edate=${y}-${mm}-${String(last).padStart(2, '0')}&elems=maxt,mint,pcpn,snow,snwd&output=json`);
                    if (!r.ok) continue;
                    const j = await r.json();
                    if (!j || j.error || !Array.isArray(j.data)) continue;
                    const rows = j.data.map(([d, mx, mn, pc, sn, sd]) => ({ valid: d, high: mx, low: mn, precip: pc, snow: sn, snowdepth: sd }));
                    if (rows.some(o => isFinite(parseFloat(o.high)))) { dcMonthCache[key] = rows; return rows; }
                } catch (e) {}
            }
            // the observing airport itself (IEM daily summaries computed from its own reports)
            try {
                const rows = (await iemDailyObs(y, m)) || [];
                if (rows.some(o => isFinite(parseFloat(o.high)))) { dcMonthCache[key] = rows; return rows; }
            } catch (e) {}
            return null;
        }

        // Daily max/min/precip for the observing ASOS/AWOS station from the Iowa Environmental Mesonet (measured, from the station's reports)
        const iemDailyCache = {};
        async function iemDailyObs(y, m, sid0, st0) {
            const sid = sid0 || (nwsObs && nwsObs.stationId), st = st0 || nwsState;
            if (!sid || !st || !/^K[A-Z0-9]{3}$/.test(sid)) return null;
            const k = `${sid}:${y}`;
            if (!iemDailyCache[k]) iemDailyCache[k] = fetch(`https://mesonet.agron.iastate.edu/api/1/daily.json?station=${sid.slice(1)}&network=${st}_ASOS&year=${y}`)
                .then(r => r.ok ? r.json() : { data: [] }).then(j => (Array.isArray(j.data) ? j.data : []).map(d => {
                    const p = d.precip == null ? null : +d.precip;
                    return { valid: String(d.date || d.day || '').slice(0, 10), high: d.max_tmpf ?? null, low: d.min_tmpf ?? null,
                             precip: p == null ? 'M' : (p > 0 && p < 0.005) ? 'T' : p.toFixed(2), snow: d.snow ?? 'M', snowdepth: d.snowd ?? 'M' };
                }).filter(o => o.valid)).catch(() => []);
            const rows = await iemDailyCache[k];
            if (!m) return rows;
            const pre = `${y}-${String(m).padStart(2, '0')}`;
            return rows.filter(o => o.valid.startsWith(pre));
        }

        function renderDailyRecordsTable() {
            renderQuickView();
            if ((!historicalData && !climLite && !stationClim && !(cliTotals && cliTotals.byMD)) || !bestBetResults || !bestBetResults.length) return;
            const tbody = document.getElementById('dailyRecordsTableBody');
            const rr = document.getElementById('recordsRange');
            const hasCli = !!(cliTotals && cliTotals.rows);
            const today = bestBetResults[0].date;
            const ovR = climOverride(currentLoc.lat, currentLoc.lon);
            if (rr) rr.innerText = ovR ? `${ovR.name} (${ovR.label}), your chosen station` : (cliTotals && cliTotals.byMD) ? `${cliTotals.station} · NWS climate reports` : (stationClim && stationClim.rec) ? `${stationClim.icao} · records ${stationClim.recStart}–present` : (nwsObs && nwsObs.stationId) ? `${nwsObs.stationId} · station reports` : '';
            dcFillPickers(today);
            const cur = !dcSel, y = cur ? +today.slice(0, 4) : dcSel.y, m = cur ? +today.slice(5, 7) : dcSel.m;
            const mm = String(m).padStart(2, '0');
            const cliBy = {};
            if (hasCli) [...(cliTotals.prevRows || []), ...cliTotals.rows].forEach(o => { if (o && o.valid) cliBy[o.valid] = o; });
            const lastDay = cur ? +today.slice(8, 10) - 1 : new Date(Date.UTC(y, m, 0)).getUTCDate();
            const dates = []; for (let d = lastDay; d >= 1; d--) dates.push(`${y}-${mm}-${String(d).padStart(2, '0')}`);
            const allCli = dates.every(ds => cliBy[ds]);
            if (allCli) { drawMonth(dates.map(ds => cliBy[ds] || null)); return; }
            tbody.innerHTML = `<tr><td colspan="7" class="p-3 text-slate-400 italic">Loading ${new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' })}…</td></tr>`;
            const want = `${y}-${mm}`;
            dcFetchMonth(y, m).then(rows => {
                const sel = dcSel ? `${dcSel.y}-${String(dcSel.m).padStart(2, '0')}` : today.slice(0, 7);
                if (sel !== want) return;   // the picker moved on
                const by = {}; (rows || []).forEach(o => { by[o.valid] = o; });
                drawMonth(dates.map(ds => cliBy[ds] || by[ds] || null), !rows);
            });

            function drawMonth(rowsDesc, failed) {
                const { n, disp, dep, recCell, dShift, dLabel } = dcHelpers();
                const C = f => (f - 32) / 1.8;
                const yrsOf = x => (Array.isArray(x) ? x : String(x ?? '').split(/[^0-9]+/)).map(String).filter(z => /^\d{4}$/.test(z));
                const trophy = (tie, info) => `<button type="button" class="rec-btn" onclick="recPop(this, event)" data-info="${esc(info || ((tie ? 'Tied' : 'Set') + ' the daily record'))}" aria-label="Record details"><i class="fa-solid fa-trophy rec"></i></button>`;
                const stnName = (cliTotals && cliTotals.station) || '';
                const recInfo = (what, tie, val, prior) => `${what} ${tie ? 'tied' : 'set'}: ${val}${stnName ? ' at ' + stnName : ''}.${prior ? ` Previous record year ${prior}.` : ''}`;
                const pFmt = (inch, trace) => (trace && !(inch > 0)) ? 'T' : formatPrecip(inch * 25.4);
                const recent = [];
                // daily normals (°F / inches) from the climate reports, else the station's 1991-2020 averages
                const normFor = (ds, o) => {
                    const md = ds.slice(5), b = cliTotals && cliTotals.byMD && cliTotals.byMD[md];
                    const hn = o && cliVal(o.high_normal) ? cliVal(o.high_normal).v : b && b.hn !== undefined ? b.hn : stationClim && stationClim.norm && stationClim.norm[md] ? cToF(stationClim.norm[md].max) : null;
                    const ln = o && cliVal(o.low_normal) ? cliVal(o.low_normal).v : b && b.ln !== undefined ? b.ln : stationClim && stationClim.norm && stationClim.norm[md] ? cToF(stationClim.norm[md].min) : null;
                    const pn = o && cliVal(o.precip_normal) ? cliVal(o.precip_normal).v : stationClim && stationClim.pnorm && stationClim.pnorm[md] != null ? stationClim.pnorm[md] / 25.4 : null;
                    const sn = stationClim && stationClim.snorm && stationClim.snorm[md] != null ? stationClim.snorm[md] / 2.54 : null;
                    return { hn, ln, pn, sn };
                };
                const anySnow = rowsDesc.some(o => { const v = o && cliVal(o.snow); return v && (v.v > 0 || v.t); });
                const NC = anySnow ? 8 : 7;
                const sTh = document.getElementById('dcSnowTh'); if (sTh) sTh.classList.toggle('hidden', !anySnow);
                const snowTd = o => {
                    if (!anySnow) return '';
                    const v = o ? cliVal(o.snow) : null, dp = o ? cliVal(o.snowdepth ?? o.snow_depth) : null;
                    const fall = !v ? '--' : (v.t && !(v.v > 0)) ? '<span class="text-cyan-200">T</span>' : v.v > 0 ? `<span class="text-cyan-200 font-semibold">${formatSnow(v.v * 2.54)}</span>` : '<span class="text-slate-400">0.0"</span>';
                    return `<td>${fall}${dp && dp.v > 0 ? ` <span class="text-slate-400">· ${formatSnow(dp.v * 2.54)} on ground</span>` : ''}</td>`;
                };
                // month statistics
                const S = { hi: [], lo: [], hn: [], ln: [], p: 0, pT: false, pn: 0, pnOk: true, s: 0, sT: false, sn: 0, wet: 0, hot: 0, frz: 0, max: null, min: null };
                const out = [];
                rowsDesc.forEach((o, k) => {
                    const ds = `${y}-${mm}-${String(lastDay - k).padStart(2, '0')}`;
                    if (!o) { out.push(`<tr><td class="text-slate-200 font-bold">${dLabel(ds)}</td><td colspan="${NC - 1}" class="text-slate-500 italic">No report</td></tr>`); return; }
                    const yy = ds.slice(0, 4);
                    const hi = cliVal(o.high), lo = cliVal(o.low), p = cliVal(o.precip), sw = cliVal(o.snow);
                    const N = normFor(ds, o), st = getHistoricalStatsForDate(ds);
                    const hr = cliVal(o.high_record), lr = cliVal(o.low_record);
                    const hy = yrsOf(o.high_record_years), ly = yrsOf(o.low_record_years), py = yrsOf(o.precip_record_years), pr = cliVal(o.precip_record);
                    const recHiF = hr ? hr.v : st && n(st.recHigh) ? Math.round(cToF(st.recHigh)) : null, recLoF = lr ? lr.v : st && n(st.recLow) ? Math.round(cToF(st.recLow)) : null;
                    const recHiY = hr ? '' : st ? st.recHighYr : '', recLoY = lr ? '' : st ? st.recLowYr : '';
                    const hiRec = hi && recHiF !== null && (hy.includes(yy) || hi.v >= recHiF || recHiY === yy), loRec = lo && recLoF !== null && (ly.includes(yy) || lo.v <= recLoF || recLoY === yy);
                    const pRec = p && pr && p.v > 0 && (py.includes(yy) || p.v >= pr.v);
                    const prior = ys => ys.filter(z => z !== yy).pop() || '';
                    if (cur && k < 7) {
                        if (hiRec) recent.push({ ds, kind: 'high', tie: hi.v === recHiF, val: formatTemp(C(hi.v)), prior: prior(hy) });
                        if (loRec) recent.push({ ds, kind: 'low', tie: lo.v === recLoF, val: formatTemp(C(lo.v)), prior: prior(ly) });
                        if (pRec) recent.push({ ds, kind: 'rainfall', tie: p.v === pr.v, val: pFmt(p.v), prior: prior(py) });
                    }
                    if (hi) { S.hi.push(hi.v); if (N.hn !== null) S.hn.push(N.hn); if (S.max === null || hi.v > S.max.v) S.max = { v: hi.v, ds }; if (hi.v >= 90) S.hot++; }
                    if (lo) { S.lo.push(lo.v); if (N.ln !== null) S.ln.push(N.ln); if (S.min === null || lo.v < S.min.v) S.min = { v: lo.v, ds }; if (lo.v <= 32) S.frz++; }
                    if (p) { S.p += p.v; if (p.t) S.pT = true; if (p.v >= 0.01) S.wet++; }
                    if (N.pn !== null) S.pn += N.pn; else S.pnOk = false;
                    if (sw) { S.s += sw.v; if (sw.t) S.sT = true; }
                    if (N.sn !== null) S.sn += N.sn;
                    const yrShow = (ys, rec, fb) => rec ? yy : (ys.slice(-1)[0] || fb || '');
                    out.push(`<tr>
                        <td class="text-slate-200 font-bold">${dLabel(ds)}</td>
                        <td><span class="text-rose-200 font-semibold">${hi ? formatTemp(C(hi.v)) : '--'}</span>${hi && N.hn !== null ? dep(C(hi.v), C(N.hn)) : ''}${hiRec ? trophy(hi.v === recHiF, recInfo('Record high', hi.v === recHiF, formatTemp(C(hi.v)), prior(hy))) : ''}</td>
                        <td><span class="text-sky-200 font-semibold">${lo ? formatTemp(C(lo.v)) : '--'}</span>${lo && N.ln !== null ? dep(C(lo.v), C(N.ln)) : ''}${loRec ? trophy(lo.v === recLoF, recInfo('Record low', lo.v === recLoF, formatTemp(C(lo.v)), prior(ly))) : ''}</td>
                        <td>${p ? `<span class="${p.v > 0 || p.t ? 'text-blue-200 font-semibold' : 'text-slate-400'}">${pFmt(p.v, p.t)}</span>${pRec ? trophy(p.v === pr.v, recInfo('Record rainfall', p.v === pr.v, pFmt(p.v), prior(py))) : ''}` : '--'}</td>
                        ${snowTd(o)}
                        <td class="text-teal-300">${N.hn !== null && N.ln !== null ? `${formatTemp(C(N.hn))} / ${formatTemp(C(N.ln))}` : '--'}</td>
                        <td>${recHiF !== null ? recCell(C(recHiF), yrShow(hy, hiRec, recHiY), 'text-rose-300') : '--'}</td>
                        <td>${recLoF !== null ? recCell(C(recLoF), yrShow(ly, loRec, recLoY), 'text-indigo-300') : '--'}</td>
                    </tr>`);
                });
                // today so far (current month only)
                let todayRow = '';
                if (cur) {
                    const so = getTodaySoFar(), recsT = recordsToday(), stT = getHistoricalStatsForDate(today), Nt = normFor(today, null);
                    const rh = recsT.find(r => r.kind === 'high'), rl = recsT.find(r => r.kind === 'low'), rp = recsT.find(r => r.kind === 'precip');
                    todayRow = `<tr class="today">
                        <td class="text-slate-200 font-bold">${dLabel(today)} <span class="text-[10px] text-sky-300 font-normal ml-1">so far</span></td>
                        <td><span class="text-rose-200 font-semibold">${n(so.hi) ? formatTemp(so.hi) : '--'}</span>${Nt.hn !== null && n(so.hi) ? dep(so.hi, C(Nt.hn)) : ''}${rh ? trophy(rh.tie, `Record high ${rh.tie ? 'tied' : 'set'} today: ${rh.valF}°F, previous record ${rh.recF}°F${rh.yr ? ' (' + rh.yr + ')' : ''}. Preliminary.`) : ''}</td>
                        <td><span class="text-sky-200 font-semibold">${n(so.lo) ? formatTemp(so.lo) : '--'}</span>${Nt.ln !== null && n(so.lo) ? dep(so.lo, C(Nt.ln)) : ''}${rl ? trophy(rl.tie, `Record low ${rl.tie ? 'tied' : 'set'} today: ${rl.valF}°F, previous record ${rl.recF}°F${rl.yr ? ' (' + rl.yr + ')' : ''}. Preliminary.`) : ''}</td>
                        <td>${n(so.precip) ? `<span class="${so.precip > 0 ? 'text-blue-200 font-semibold' : 'text-slate-400'}">${formatPrecip(so.precip)}</span>${rp ? trophy(rp.tie, `Record rainfall ${rp.tie ? 'tied' : 'set'} today: ${rp.valIn != null ? rp.valIn.toFixed(2) + '"' : ''}, previous record ${rp.recIn != null ? rp.recIn.toFixed(2) + '"' : ''}${rp.yr ? ' (' + rp.yr + ')' : ''}. Preliminary.`) : ''}` : '--'}</td>
                        ${anySnow ? '<td class="text-slate-500">—</td>' : ''}
                        <td class="text-teal-300">${Nt.hn !== null && Nt.ln !== null ? `${formatTemp(C(Nt.hn))} / ${formatTemp(C(Nt.ln))}` : '--'}</td>
                        <td>${stT ? recCell(stT.recHigh, stT.recHighYr, 'text-rose-300') : '--'}</td>
                        <td>${stT ? recCell(stT.recLow, stT.recLowYr, 'text-indigo-300') : '--'}</td>
                    </tr>`;
                }
                tbody.innerHTML = (failed ? `<tr><td colspan="${NC}" class="p-3 text-slate-400 italic">No station data is available for that month.</td></tr>` : '') + todayRow + out.join('');

                // month summary tiles
                const sumEl = document.getElementById('dcSummary');
                if (sumEl) {
                    const avg = a => a.length ? a.reduce((x, z) => x + z, 0) / a.length : null;
                    const aH = avg(S.hi), aL = avg(S.lo), nH = avg(S.hn), nL = avg(S.ln);
                    const mean = aH !== null && aL !== null ? (aH + aL) / 2 : null, nMean = nH !== null && nL !== null ? (nH + nL) / 2 : null;
                    const fT = f => f === null ? '--' : (isImperial ? `${f.toFixed(1)}°F` : `${((f - 32) / 1.8).toFixed(1)}°C`);
                    const dT = (a, b) => (a === null || b === null) ? '' : (() => { const d = (a - b) * (isImperial ? 1 : 1 / 1.8); return `<span class="${d > 0.05 ? 'text-rose-300' : d < -0.05 ? 'text-sky-300' : 'text-slate-400'}">${d > 0 ? '+' : d < 0 ? '−' : '±'}${Math.abs(d).toFixed(1)}° vs normal</span>`; })();
                    const day = s => new Date(s + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    const tile = (lab, val, sub, vc) => `<div class="dcs"><div class="text-[11px] text-slate-400">${lab}</div><div class="text-lg font-bold ${vc || 'text-slate-100'} font-mono">${val}</div><div class="text-[11px] mt-0.5">${sub || '&nbsp;'}</div></div>`;
                    const pVal = (S.pT && S.p < 0.005) ? 'T' : formatPrecip(S.p * 25.4);
                    const tiles = [
                        tile('Warmest', S.max ? fT(S.max.v).replace('.0', '') : '--', S.max ? `<span class="text-slate-400">${day(S.max.ds)}</span>` : '', 'text-rose-200'),
                        tile('Coldest', S.min ? fT(S.min.v).replace('.0', '') : '--', S.min ? `<span class="text-slate-400">${day(S.min.ds)}</span>` : '', 'text-sky-200'),
                        tile('Average high', fT(aH), dT(aH, nH)),
                        tile('Average low', fT(aL), dT(aL, nL)),
                        tile('Mean temperature', fT(mean), dT(mean, nMean)),
                        tile('Precipitation', pVal, S.pnOk && S.pn > 0 ? `<span class="text-slate-400">normal ${formatPrecip(S.pn * 25.4)} · ${Math.round(100 * S.p / S.pn)}%</span>` : `<span class="text-slate-400">${S.wet} day${S.wet === 1 ? '' : 's'} ≥ 0.01"</span>`)
                    ];
                    if (anySnow || S.sn > 0.05) tiles.push(tile('Snowfall', (S.sT && S.s < 0.05) ? 'T' : formatSnow(S.s * 2.54), S.sn > 0.05 ? `<span class="text-slate-400">normal ${formatSnow(S.sn * 2.54)}</span>` : ''));
                    const extra = [S.hot ? `${S.hot} day${S.hot === 1 ? '' : 's'} ≥ 90°F` : '', S.frz ? `${S.frz} night${S.frz === 1 ? '' : 's'} ≤ 32°F` : '', S.pnOk && S.pn > 0 ? `${S.wet} day${S.wet === 1 ? '' : 's'} with precipitation` : ''].filter(Boolean).join(' · ');
                    const label = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });
                    sumEl.innerHTML = rowsDesc.some(Boolean) ? `<div class="dcs-grid">${tiles.join('')}</div>` : '';
                    const mEl = document.getElementById('dcMeta'), tEl = document.getElementById('dcToDate');
                    if (mEl) mEl.innerText = rowsDesc.some(Boolean) ? `${S.hi.length} day${S.hi.length === 1 ? '' : 's'} reported${extra ? ' · ' + extra : ''}` : '';
                    if (tEl) tEl.innerText = cur ? 'to date' : '';
                }

                // recent records (current month view)
                const yEl = document.getElementById('climateYesterday');
                if (yEl) {
                    const stn = (cliTotals && cliTotals.station) || '';
                    const yd = dShift(today, -1);
                    yEl.innerHTML = recent.map(r => {
                        const when = r.ds === yd ? 'yesterday' : 'on ' + new Date(r.ds + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
                        const what = r.kind === 'rainfall' ? 'Record rainfall' : `Record ${r.kind}`;
                        return `<div class="yrec"><i class="fa-solid fa-trophy"></i><div><div class="text-sm font-bold text-amber-100">${what} ${r.tie ? 'tied' : 'set'} ${when}</div><div class="text-xs text-slate-300 mt-0.5"><b class="font-mono">${r.val}</b> ${r.tie ? 'tied' : 'set'} the daily record${stn ? ' at ' + esc(stn) : ''}${r.prior ? ` (previous ${r.prior})` : ''}.</div></div></div>`;
                    }).join('');
                    yEl.innerHTML = ''; yEl.classList.add('hidden');
                }
            }
        }
