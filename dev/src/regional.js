        // ---------- Regional observations (0-9 h): nearby stations versus the model, carried along the low-level flow ----------
        // Each station's latest report is compared with the model at that spot (and at the station's own elevation). Where the
        // models are wrong upstream (a front, outflow or clearing they have placed badly), the same error reaches this location
        // as the air moves in. The change in error expected here is added to the next hours of the forecast.
        let regionalAdj = null, regionalInfo = null, nwsStationList = null;
        async function regionalAnalysis(lat, lon) {
            const ok = v => v !== null && v !== undefined && !isNaN(v);
            const own = nwsObs && nwsObs.stationId;
            const list = (nwsStationList || []).map(f => ({ id: f.properties && f.properties.stationIdentifier, lat: f.geometry && f.geometry.coordinates[1], lon: f.geometry && f.geometry.coordinates[0], elev: f.properties && f.properties.elevation ? f.properties.elevation.value : null }))
                .filter(s => s.id && /^[KP][A-Z0-9]{3}$/.test(s.id) && ok(s.lat) && ok(s.lon))
                .map(s => ({ ...s, km: distKm(lat, lon, s.lat, s.lon) })).filter(s => s.km <= 160).sort((a, b) => a.km - b.km).slice(0, 16);
            if (list.length < 4) throw new Error('too few stations');
            const kmh = q => q && ok(q.value) ? (q.unitCode && /m_s/.test(q.unitCode) ? q.value * 3.6 : q.value) : null;
            const obs = (await Promise.all(list.map(s => fetch(`https://api.weather.gov/stations/${s.id}/observations/latest`).then(r => r.ok ? r.json() : null).catch(() => null))))
                .map((j, i) => { const p = j && j.properties; if (!p || !p.timestamp || Date.now() - Date.parse(p.timestamp) > 100 * 60e3) return null;
                    return { ...list[i], ms: Date.parse(p.timestamp), t: p.temperature ? p.temperature.value : null, td: p.dewpoint ? p.dewpoint.value : null, ws: kmh(p.windSpeed), wd: p.windDirection ? p.windDirection.value : null }; })
                .filter(o => o && ok(o.t));
            if (obs.length < 4) throw new Error('too few reports');
            // the model at each station (and here), at the station's elevation
            const here = { lat: +lat, lon: +lon, elev: ensembleData.elevation };
            const pts = [here, ...obs];
            const q = `latitude=${pts.map(p => (+p.lat).toFixed(4)).join(',')}&longitude=${pts.map(p => (+p.lon).toFixed(4)).join(',')}&elevation=${pts.map(p => ok(p.elev) ? Math.round(p.elev) : 'nan').join(',')}`;
            const mj = await (await fetch(`https://api.open-meteo.com/v1/forecast?${q}&hourly=temperature_2m,dew_point_2m&past_hours=3&forecast_hours=2&timezone=GMT`)).json();
            const arr = Array.isArray(mj) ? mj : [mj];
            if (arr.length !== pts.length) throw new Error('model points');
            const modelAt = (m, f, ms) => { const h = m && m.hourly; if (!h) return null; const T = h.time.map(t => Date.parse(t + ':00Z')); for (let i = 0; i < T.length - 1; i++) if (ms >= T[i] && ms <= T[i + 1]) { const a = h[f][i], b = h[f][i + 1]; return ok(a) && ok(b) ? a + (b - a) * (ms - T[i]) / (T[i + 1] - T[i]) : null; } return null; };
            // errors (observed minus model) here and at each station
            const cc = getCurrentConditions();
            const hereMs = nwsObs && nwsObs.timestamp ? Date.parse(nwsObs.timestamp) : Date.now();
            const e0 = { t: cc && ok(cc.temp) ? cc.temp - modelAt(arr[0], 'temperature_2m', hereMs) : null, td: cc && ok(cc.dew) ? cc.dew - modelAt(arr[0], 'dew_point_2m', hereMs) : null };
            if (!ok(e0.t)) throw new Error('no local error');
            const kx = 111.32 * Math.cos(lat * Math.PI / 180), ky = 111.32;
            const st = obs.map((o, i) => ({ ...o, x: (o.lon - lon) * kx, y: (o.lat - lat) * ky, et: o.t - modelAt(arr[i + 1], 'temperature_2m', o.ms), ed: ok(o.td) ? o.td - modelAt(arr[i + 1], 'dew_point_2m', o.ms) : null }))
                .filter(o => ok(o.et) && o.id !== own);
            // low-level flow: mean wind vector of the reports within 100 km (surface wind runs slower than the air above it)
            let u = 0, v = 0, n = 0;
            [...st, ...(cc && ok(cc.wind) && ok(cc.dir) ? [{ km: 0, ws: cc.wind, wd: cc.dir }] : [])].forEach(o => { if (o.km <= 100 && ok(o.ws) && ok(o.wd) && o.ws > 0) { const r = o.wd * Math.PI / 180; u += -o.ws * Math.sin(r); v += -o.ws * Math.cos(r); n++; } });
            if (n < 3) throw new Error('no flow');
            u = u / n * 1.25; v = v / n * 1.25;   // km/h toward east, toward north
            const spd = Math.hypot(u, v);
            if (spd < 8) return { flow: spd, stations: st.length, adj: null };
            // error expected here after k hours = error now at the point the air is coming from (Gaussian-weighted stations)
            const field = (f, x, y) => { let s = 0, w = 0, m = 0; st.forEach(o => { const e = f === 't' ? o.et : o.ed; if (!ok(e)) return; const d = Math.hypot(o.x - x, o.y - y), ww = Math.exp(-((d / 35) ** 2)); if (ww > 0.05) { s += ww * e; w += ww; m++; } }); return m >= 2 && w > 0.3 ? s / w : null; };
            const adj = { t: [], td: [] }, raw = { t: [], td: [] }, up = { t: [], td: [] }, last = { t: 0, td: 0 }, lastE = { t: null, td: null };
            for (let k = 1; k <= 9; k++) {
                const x = -u * k, y = -v * k;
                const fade = Math.exp(-k / 8) * (k > 6 ? (9 - k + 1) / 4 : 1);
                ['t', 'td'].forEach(f => {
                    const e = field(f, x, y), b = e0[f];
                    // beyond the farthest stations the last upstream value is held (and fades), never dropped to zero
                    let d = ok(e) && ok(b) ? Math.max(-8, Math.min(8, e - b)) : last[f];
                    last[f] = d; raw[f].push(+d.toFixed(2));
                    if (ok(e)) lastE[f] = e; up[f].push(lastE[f]);   // the upstream stations' own error (observed minus model)
                    d = Math.sign(d) * Math.max(0, Math.abs(d) - 1);   // station-to-station noise floor
                    adj[f].push(+(0.7 * d * fade).toFixed(2));
                });
            }
            return { flow: spd, u, v, stations: st.length, adj, raw, up, e0 };
        }
        async function loadRegional(token, lat, lon) {
            if (!nwsOffice) { regionalAdj = null; return; }
            try {
                const ck = `${(+lat).toFixed(3)},${(+lon).toFixed(3)}`;   // reuse for 10 minutes (keeps NWS requests down on refresh)
                const r = loadRegional._c && loadRegional._c.k === ck && Date.now() - loadRegional._c.t < 10 * 60e3 ? loadRegional._c.r : await regionalAnalysis(+lat, +lon);
                loadRegional._c = { k: ck, t: loadRegional._c && loadRegional._c.r === r ? loadRegional._c.t : Date.now(), r };
                if (token !== fetchToken) return;
                regionalAdj = r && r.adj ? { ...r, cur: hourlyStart(), at: Date.now() } : null;
                regionalInfo = r;
                regionalNote();
                recomputeForecast();
            } catch (e) { regionalAdj = null; regionalInfo = null; console.warn('Regional analysis unavailable:', e.message); }
        }
        // one line for the forecast text when the change is large enough to matter
        function regionalNote() {
            if (!regionalAdj) { if (regionalInfo) regionalInfo.msg = null; return; }
            const a = regionalAdj.adj.t; let k = -1, m = 0;
            a.forEach((d, i) => { if (Math.abs(d) > Math.abs(m)) { m = d; k = i; } });
            if (Math.abs(m) < 1.6 || k < 0) { regionalInfo.msg = null; return; }   // about 3 F
            const dirs = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];
            const from = dirs[Math.round(((Math.atan2(-regionalAdj.u, -regionalAdj.v) * 180 / Math.PI) + 360) % 360 / 45) % 8];
            const mi = Math.round(regionalAdj.flow * (k + 1) * 0.621 / 5) * 5;
            const when = new Date(Date.now() + (k + 1) * 36e5).toLocaleTimeString('en-US', { hour: 'numeric', timeZone: ensembleData.timezone });
            const ue = regionalAdj.up.t[k];
            if (ue == null || Math.sign(ue) !== Math.sign(m) || Math.abs(ue) < 1.6) { regionalInfo.msg = null; return; }
            const deg = Math.round(Math.abs(ue) * (isImperial ? 1.8 : 1));
            regionalInfo.msg = `Stations ${mi} miles ${from} are running ${deg}° ${m < 0 ? 'colder' : 'warmer'} than forecast; that air arrives by about ${when}.`;
        }
        // added to the hourly temperature / dewpoint after the observation correction (hours after the analysis)
        function regionalDelta(f, j) {
            if (!regionalAdj || !regionalAdj.adj || Date.now() - regionalAdj.at > 3 * 36e5) return 0;
            const k = j - hourlyStart();
            return k >= 1 && k <= 9 ? (regionalAdj.adj[f][k - 1] || 0) : 0;
        }
