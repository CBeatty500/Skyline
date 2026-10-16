        // ---------- Thunderstorm probability: NWS gridded forecast (probabilityOfThunder), US only ----------
        let nwsThunder = null;
        function parseNwsSeries(series) {
            if (!series || !Array.isArray(series.values)) return null;
            const m = new Map();
            series.values.forEach(v => {
                const [t0, dur] = String(v.validTime || '').split('/');
                const start = Date.parse(t0); if (isNaN(start) || v.value == null) return;
                const mt = String(dur || 'PT1H').match(/P(?:(\d+)D)?(?:T(?:(\d+)H)?)?/);
                const hrs = mt ? (+(mt[1] || 0) * 24 + +(mt[2] || 0)) || 1 : 1;
                for (let k = 0; k < hrs; k++) m.set(start + k * 36e5, v.value);
            });
            return m.size ? m : null;
        }
        function thunderAt(j) {
            if (!nwsThunder || !ensembleData || !ensembleData.hourly) return null;
            const k = ensembleData.hourly.time[j]; if (!k) return null;
            const ms = Date.parse(k + ':00Z') - (ensembleData.utc_offset_seconds || 0) * 1000;
            const v = nwsThunder.get(ms);
            return v == null ? null : v;
        }
        // highest thunderstorm chance per forecast day (today: hours still ahead)
        function annotateThunder() {
            if (!bestBetResults || !ensembleData || !ensembleData.hourly) return;
            const h = ensembleData.hourly, cur = hourlyStart();
            bestBetResults.forEach((b, i) => {
                let mx = null;
                h.time.forEach((t, j) => { if (!t.startsWith(b.date) || (i === 0 && j < cur)) return; const v = thunderAt(j); if (v != null && (mx === null || v > mx)) mx = v; });
                b.thunder = mx;
            });
        }
        function tstmTag(p, cls) { return p != null && p >= 15 ? `<span class="tstm ${cls || ''}" title="${Math.round(p)}% chance of thunderstorms (NWS)"><i class="fa-solid fa-bolt"></i> ${Math.round(p)}%</span>` : ''; }

