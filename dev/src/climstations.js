        // ---------- Climate station choice: automatic, or a nearby long-record station the user picks ----------
        function climOverrideKey(lat, lon) { return `skyline:climstn:${(+lat).toFixed(2)},${(+lon).toFixed(2)}`; }
        function climOverride(lat, lon) { try { const v = localStorage.getItem(climOverrideKey(lat, lon)); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
        // normals and records are shown only when they come from real station history (NWS climate reports or a station's own record);
        // outside the US the reanalysis normals stay (there is no station network to use instead)
        function climTrusted() {
            if (cliTotals && cliTotals.byMD) return true;
            if (stationClim && (stationClim.rec || stationClim.norm)) return true;
            return !nwsOffice;
        }
        async function findClimStations() {
            const box = document.getElementById('dcStations');
            if (!box) return;
            if (!box.classList.contains('hidden') && box.dataset.loaded) { box.classList.add('hidden'); return; }
            box.classList.remove('hidden');
            box.innerHTML = '<div class="text-xs text-slate-400 italic p-2">Searching nearby stations…</div>';
            const lat = +currentLoc.lat, lon = +currentLoc.lon;
            const yNow = new Date().getUTCFullYear(), recent = new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10);
            let locE = null; try { locE = (await ptElev([[lat, lon]]))[0]; } catch (e) {}
            let list = [];
            for (const half of [0.35, 0.8]) {
                try {
                    const bb = [lon - half, lat - half, lon + half, lat + half].map(v => v.toFixed(3)).join(',');
                    const r = await fetch(`${ACIS}/StnMeta?bbox=${bb}&elems=maxt,pcpn&meta=name,sids,state,ll,elev,valid_daterange&output=json`);
                    if (!r.ok) continue;
                    const j = await r.json();
                    const rng = x => (Array.isArray(x) && x[0] && x[1]) ? { s: +String(x[0]).slice(0, 4), e: String(x[1]) } : null;
                    list = (j.meta || []).map(m => {
                        const p = parseAcisMeta(m), vr = Array.isArray(m.valid_daterange) ? m.valid_daterange : [];
                        const t = rng(vr[0]), pr = rng(vr[1]);
                        const elevM = m.elev != null && isFinite(+m.elev) ? +m.elev * 0.3048 : null;
                        return { ...p, elevM, t, pr, start: t ? t.s : pr ? pr.s : null, end: [t && t.e, pr && pr.e].filter(Boolean).sort().pop() || null, km: p.lat != null ? distKm(lat, lon, p.lat, p.lon) : null };
                    }).filter(s => s.km != null && (s.t || s.pr) && (s.ghcn || s.faa || s.icao))
                      .sort((a, b) => a.km - b.km).slice(0, 12);
                    if (list.length >= 5) break;
                } catch (e) {}
            }
            box.dataset.loaded = '1';
            const ov = climOverride(lat, lon);
            const ft = m => m == null ? '' : `${Math.round(m * 3.28084).toLocaleString()} ft`;
            const dist = km => isImperial ? `${Math.round(km * 0.621)} mi` : `${Math.round(km)} km`;
            const dE = s => (locE == null || s.elevM == null) ? '' : (() => { const d = Math.round((s.elevM - locE) * 3.28084); return `${d >= 0 ? '+' : '−'}${Math.abs(d).toLocaleString()} ft vs here`; })();
            window._climCands = list;
            box.innerHTML = (list.length ? list.map((s, i) => `<button type="button" class="dc-stn${ov && ov.ids && ov.ids[0] === (s.faa ? s.faa + 'thr' : s.ghcn) ? ' on' : ''}" onclick="useClimStation(${i})">
                    <span class="font-semibold text-slate-100">${esc(String(s.name || '').toLowerCase().replace(/\b[a-z]/g, c => c.toUpperCase()))}</span>
                    <span class="text-[11px] text-slate-400 font-mono">${dist(s.km)} away, ${ft(s.elevM)}${dE(s) ? ' (' + dE(s) + ')' : ''}</span>
                    <span class="text-[11px] text-slate-400 font-mono">${s.t ? 'Temps ' + s.t.s + (s.t.e < recent ? '–' + s.t.e.slice(0, 4) : '–now') : 'No temps'}, ${s.pr ? 'precip ' + s.pr.s + (s.pr.e < recent ? '–' + s.pr.e.slice(0, 4) : '–now') : 'no precip'}</span></button>`).join('')
                : '<div class="text-xs text-slate-400 p-2">No nearby stations were found.</div>')
                + (ov ? `<button type="button" class="dc-stn" onclick="useClimStation(-1)"><span class="font-semibold text-slate-100">Automatic choice</span><span class="text-[11px] text-slate-400 font-mono">Let Skyline pick the station again</span></button>` : '');
        }
        async function useClimStation(i) {
            const lat = +currentLoc.lat, lon = +currentLoc.lon, k = climOverrideKey(lat, lon);
            if (i < 0) { try { localStorage.removeItem(k); } catch (e) {} }
            else {
                const s = (window._climCands || [])[i]; if (!s) return;
                const ids = []; if (s.faa) ids.push(s.faa + 'thr', s.faa); if (s.ghcn) ids.push(s.ghcn); if (s.icao) ids.push(s.icao);
                const v = { ids: [...new Set(ids)], ghcn: s.ghcn, label: s.icao || s.faa || s.ghcn, name: String(s.name || '').toLowerCase().replace(/\b[a-z]/g, c => c.toUpperCase()), km: s.km, override: true };
                try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {}
            }
            const box = document.getElementById('dcStations'); if (box) { box.classList.add('hidden'); delete box.dataset.loaded; }
            for (const key in climStnPromises) delete climStnPromises[key];
            for (const key in dcMonthCache) delete dcMonthCache[key];
            stationClim = null; cliTotals = null; precipNormals = null;
            renderDashboard();
            try { renderDailyRecordsTable(); } catch (e) {}
            const token = fetchToken, nws = { obs: nwsObs, state: nwsState };
            await Promise.all([loadStationClimate(token, nws, lat, lon), retryPrecipTotals()].map(p => Promise.resolve(p).catch(() => {})));
            try { loadPrecipNormals(token, lat, lon, nws, null); } catch (e) {}
            renderDashboard();
            try { renderDailyRecordsTable(); renderPrecipTotals(); } catch (e) {}
        }

