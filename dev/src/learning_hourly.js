        // ---------- Hourly learning (shared verification, run several times a day by the repository's GitHub Action) ----------
        // Every hour of the forecast is checked against the station's observation: temperature, dewpoint, wind, gusts,
        // cloud cover and whether it rained. Errors are kept by lead time (0-6 h, 6-24 h, 24-48 h, 48 h+) and by day / night.
        // The corrections here are applied once per load to the hourly forecast, before the radar nowcast.
        let hourlyLearn = null;   // { corr: {cell: {t, td, cc, ws, wg, pp}}, cells, n, updated, name }
        const HL_LEADS = ['0-6', '6-24', '24-48', '48+'];
        const hlLead = hrs => hrs < 6 ? '0-6' : hrs < 24 ? '6-24' : hrs < 48 ? '24-48' : '48+';
        async function sharedEntryFor(lat, lon) {
            const sh = await Promise.race([sharedLearning(), new Promise(r => setTimeout(() => r(null), 8000))]);
            if (!sh || !sh.locations) return null;
            let best = null;
            Object.values(sh.locations).forEach(e => { if (e && e.lat != null) { const km = distKm(+lat, +lon, e.lat, e.lon); if (km <= 12 && (!best || km < best.km)) best = { ...e, km }; } });
            return best;
        }
        // the forecast as made, before learned corrections and the radar nowcast (what the verification scores)
        function snapHourlyRaw() {
            const h = ensembleData && ensembleData.hourly; if (!h) return;
            h._raw = {};
            ['temperature_2m', 'dew_point_2m', 'cloud_cover', 'precipitation_probability', 'precipitation'].forEach(f => { if (h[f]) h._raw[f] = h[f].slice(); });
            h._learnF = null;
        }
        function hourMs(j) { const h = ensembleData.hourly; return Date.parse(h.time[j] + ':00Z') - (ensembleData.utc_offset_seconds || 0) * 1000; }
        function applyHourlyLearning(entry) {
            hourlyLearn = entry && entry.hourly && entry.hourly.corr ? { ...entry.hourly, name: entry.name, km: entry.km } : null;
            const h = ensembleData && ensembleData.hourly;
            if (!h || !hourlyLearn || NOLEARN) return;
            const now = Date.now(), ok = v => v !== null && v !== undefined && !isNaN(v);
            const ws = new Array(h.time.length).fill(1), wg = new Array(h.time.length).fill(1);
            h.time.forEach((t, j) => {
                const ahead = (hourMs(j) - now) / 36e5;
                if (ahead < -1) return;
                const c = hourlyLearn.corr[hlLead(Math.max(0, ahead)) + '|' + (h.is_day && h.is_day[j] ? 'd' : 'n')];
                if (!c) return;
                if (h.temperature_2m && ok(h.temperature_2m[j]) && c.t) h.temperature_2m[j] += c.t;
                if (h.dew_point_2m && ok(h.dew_point_2m[j]) && c.td) h.dew_point_2m[j] += c.td;
                if (h.dew_point_2m && h.temperature_2m && ok(h.dew_point_2m[j]) && ok(h.temperature_2m[j])) h.dew_point_2m[j] = Math.min(h.dew_point_2m[j], h.temperature_2m[j]);
                if (h.cloud_cover && ok(h.cloud_cover[j]) && c.cc) h.cloud_cover[j] = Math.max(0, Math.min(100, h.cloud_cover[j] + c.cc));
                if (ahead >= 3 && h.precipitation_probability && ok(h.precipitation_probability[j]) && c.pp && c.pp !== 1) h.precipitation_probability[j] = Math.max(0, Math.min(100, Math.round(h.precipitation_probability[j] * c.pp)));
                ws[j] = c.ws || 1; wg[j] = c.wg || 1;
            });
            h._learnF = { wind_speed_10m: ws, wind_gusts_10m: wg };
        }
        function modelWindAt(field, j) {
            const v = _modelWindAtRaw(field, j), h = ensembleData.hourly;
            const f = h._learnF && h._learnF[field] ? h._learnF[field][j] : 1;
            return v === null || v === undefined || isNaN(v) ? v : v * (f || 1);
        }
        function hourlyLearningHTML() {
            if (!hourlyLearn) return '<div class="text-xs text-slate-400">No hourly verification for this location yet. It is checked several times a day for the tracked cities.</div>';
            const dU = isImperial ? 1.8 : 1, u = isImperial ? '°F' : '°C';
            const f = x => x == null ? '--' : `${x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(x * dU).toFixed(1)}${u}`;
            const pct = x => x == null ? '--' : `${x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(Math.round(x))}%`;
            const rat = x => x == null ? '--' : `×${x.toFixed(2)}`;
            const lbl = { '0-6': '0-6 h', '6-24': '6-24 h', '24-48': '24-48 h', '48+': '48 h+' };
            const rows = [];
            HL_LEADS.forEach(L => ['d', 'n'].forEach(p => {
                const k = L + '|' + p, s = hourlyLearn.cells && hourlyLearn.cells[k], c = hourlyLearn.corr[k];
                if (!s || !s.n) return;
                const m = (a) => a && a.w ? a.s / a.w : null, r = a => a && a.f > 0 ? a.o / a.f : null;
                rows.push(`<tr class="border-t border-white/5"><td class="p-2 text-slate-200">${lbl[L]} ${p === 'd' ? 'day' : 'night'}</td><td class="p-2">${s.n}</td>
                    <td class="p-2">${f(m(s.t))}</td><td class="p-2">${f(m(s.td))}</td><td class="p-2">${rat(r(s.ws))}</td><td class="p-2">${rat(r(s.wg))}</td>
                    <td class="p-2">${pct(m(s.cc))}</td><td class="p-2">${s.pp && s.pp.w ? `${Math.round(s.pp.p / s.pp.w * 100)}% vs ${Math.round(s.pp.o / s.pp.w * 100)}%` : '--'}</td>
                    <td class="p-2 text-amber-300">${[c.t ? `temp ${f(c.t)}` : '', c.td ? `dew ${f(c.td)}` : '', c.ws !== 1 ? `wind ${rat(c.ws)}` : '', c.wg !== 1 ? `gust ${rat(c.wg)}` : '', c.cc ? `cloud ${pct(c.cc)}` : '', c.pp !== 1 ? `rain chance ${rat(c.pp)}` : ''].filter(Boolean).join(', ') || '<span class="text-slate-500">none yet</span>'}</td></tr>`);
            }));
            return `<div class="overflow-x-auto"><table class="w-full text-xs font-mono text-slate-300"><thead class="text-[10px] uppercase text-slate-400"><tr>
                <th class="p-2 text-left">Lead</th><th class="p-2 text-left">Hours</th><th class="p-2 text-left">Temp bias</th><th class="p-2 text-left">Dew bias</th><th class="p-2 text-left">Wind obs/fcst</th><th class="p-2 text-left">Gust obs/fcst</th><th class="p-2 text-left">Cloud bias</th><th class="p-2 text-left">Rain chance vs observed</th><th class="p-2 text-left">Correction applied</th></tr></thead>
                <tbody>${rows.join('') || '<tr><td class="p-2 text-slate-400" colspan="9">Collecting</td></tr>'}</tbody></table></div>
                <div class="text-[11px] text-slate-400 mt-2">Every forecast hour checked against ${esc(hourlyLearn.station || 'the station')} (${hourlyLearn.n} hours, updated ${new Date(hourlyLearn.updated).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}). Bias = forecast minus observed. Corrections grow with the number of cases: temperature and dewpoint up to ±3°C (±5.4°F), cloud ±20%, wind and gusts ×0.75 to ×1.25, rain chance ×0.75 to ×1.25 (not in the first 3 hours, where radar leads). Station cloud reports stop at 12,000 ft, so a clear report only counts against forecasts of mostly cloudy skies.</div>`;
        }
        try { sharedLearning(); } catch (e) {}   // start fetching the shared corrections as the page loads
        // applied after the page is shown (never delays the first view), then the forecast is rebuilt
        async function loadHourlyLearning(token, lat, lon) {
            try {
                const e = await sharedEntryFor(lat, lon);
                if (token !== fetchToken) return;
                applyHourlyLearning(e);
                if (hourlyLearn && !NOLEARN) recomputeForecast();
            } catch (e) { hourlyLearn = null; }
        }
