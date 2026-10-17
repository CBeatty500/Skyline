        // ---------- Past 24 hours: one station report per hour (the routine hourly report when there is one) ----------
        function toggleObs24() {
            const w = document.getElementById('obs24Wrap'), b = document.getElementById('obs24Toggle');
            const open = w.classList.toggle('hidden') === false;
            b.setAttribute('aria-expanded', String(open)); b.classList.toggle('open', open);
            document.getElementById('obs24Hint').innerText = open ? 'Hide' : 'Show hourly observations';
            if (open) renderObs24();
        }
        function renderObs24() {
            const w = document.getElementById('obs24Wrap');
            if (!w || w.classList.contains('hidden')) return;
            const n = v => v !== null && v !== undefined && !isNaN(v);
            const val = q => q && n(q.value) ? q.value : null;
            const kmh = q => { const v = val(q); return v === null ? null : (q.unitCode && /m_s/.test(q.unitCode) ? v * 3.6 : v); };
            const tz = ensembleData && ensembleData.timezone, now = Date.now();
            const obs = (nwsObsToday || []).filter(o => o && o.timestamp && o.temperature && n(o.temperature.value) && now - Date.parse(o.timestamp) <= 24.5 * 36e5);
            if (!obs.length) { w.innerHTML = '<div class="text-xs text-slate-400 p-2">No station reports in the last 24 hours.</div>'; return; }
            // one per clock hour: the routine report (minutes 45-59) if there is one, else the latest that hour
            const byHour = {};
            obs.forEach(o => {
                const t = Date.parse(o.timestamp), mins = new Date(t).getUTCMinutes(), k = Math.floor(t / 36e5);
                const score = mins >= 45 ? 100 + mins : mins;
                if (!byHour[k] || score > byHour[k].score) byHour[k] = { o, score, t };
            });
            const rows = Object.values(byHour).sort((a, b) => b.t - a.t).slice(0, 24);
            const td = (x, c = '') => `<td class="p-2 whitespace-nowrap ${c}">${x}</td>`;
            const th = x => `<th class="p-2 whitespace-nowrap">${x}</th>`;
            const body = rows.map(({ o, t }) => {
                const time = new Date(t).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: tz });
                const T = val(o.temperature), D = val(o.dewpoint), RH = val(o.relativeHumidity);
                const ws = kmh(o.windSpeed), wg = kmh(o.windGust), wd = val(o.windDirection);
                const wind = ws === null ? '--' : ws < 1 ? 'Calm' : `${n(wd) ? compass(wd) + ' ' : ''}${formatSpeed(ws)}`;
                const vis = val(o.visibility), visTxt = vis === null ? '--' : isImperial ? `${(vis / 1609.34) >= 9.95 ? '10' : (vis / 1609.34).toFixed(vis / 1609.34 < 3 ? 1 : 0)} mi` : `${(vis / 1000).toFixed(vis < 5000 ? 1 : 0)} km`;
                const slp = val(o.seaLevelPressure), alt = val(o.barometricPressure), pr = n(slp) ? slp / 100 : n(alt) ? alt / 100 : null;
                const p1 = val(o.precipitationLastHour);
                const day = (() => { const d = ensembleData && ensembleData.daily; if (!d) return true; const ds = new Date(t).toLocaleDateString('en-CA', { timeZone: tz }), i = d.time.indexOf(ds); return i < 0 || !d.sunrise[i] ? true : (t >= Date.parse(d.sunrise[i] + ':00Z') - (ensembleData.utc_offset_seconds || 0) * 1000 && t < Date.parse(d.sunset[i] + ':00Z') - (ensembleData.utc_offset_seconds || 0) * 1000); })();
                const sky = o.textDescription ? skyWording(o.textDescription, day) : '--';
                const wet = /rain|drizzle|snow|thunder|shower|sleet|freezing|ice/i.test(sky);
                return `<tr class="border-t border-white/5">${td(time, 'text-slate-200')}${td(n(T) ? formatTemp(T) : '--', 'text-amber-200')}${td(n(D) ? formatTemp(D) : '--', 'text-emerald-200')}${td(n(RH) ? Math.round(RH) + '%' : '--')}${td(wind)}${td(n(wg) ? formatSpeed(wg) : '')}${td(esc(sky), wet ? 'text-sky-300' : '')}${td(visTxt)}${td(pr !== null ? formatPressure(pr) : '--')}${td(n(p1) ? formatPrecip(p1) : '', p1 > 0 ? 'text-sky-300' : '')}</tr>`;
            }).join('');
            const sid = nwsObs && nwsObs.stationId ? nwsObs.stationId : '';
            w.innerHTML = `<table class="dclim w-full text-xs text-left text-slate-300 font-mono"><thead class="text-[11px] text-slate-400 uppercase bg-slate-800/80"><tr>${th('Time')}${th('Temp')}${th('Dewpt')}${th('RH')}${th('Wind')}${th('Gust')}${th('Sky / weather')}${th('Vis')}${th('Pressure')}${th('Precip')}</tr></thead><tbody>${body}</tbody></table>
                <div class="text-[11px] text-slate-400 mt-2">${esc(sid)} reports, newest first; precipitation is for the hour ending at that time.</div>`;
        }
