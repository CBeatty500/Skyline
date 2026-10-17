        // ---------- NWS gridded hourly PoP and sky cover, blended 50/50 with the model ensemble (US) ----------
        function blendNwsGrid(nws) {
            const h = ensembleData && ensembleData.hourly;
            if (!h || !nws) return;
            const off = (ensembleData.utc_offset_seconds || 0) * 1000;
            const at = (m, j) => m ? m.get(Date.parse(h.time[j] + ':00Z') - off) : undefined;
            if (nws.pop && h.precipitation_probability) h.precipitation_probability = h.precipitation_probability.map((v, j) => { const n = at(nws.pop, j); return n == null ? v : (v == null ? n : Math.round(0.5 * v + 0.5 * n)); });
            if (nws.sky && h.cloud_cover) h.cloud_cover = h.cloud_cover.map((v, j) => { const n = at(nws.sky, j); return n == null ? v : (v == null ? n : 0.5 * v + 0.5 * n); });
        }

        // ---------- Radar nowcast (0-3 h): NOAA/NWS national base reflectivity mosaic, sampled on a grid around the location.
        // Echo motion from the last 30 minutes (pattern matching), extrapolated to the location. Raises the hourly chance and
        // wet/thunder codes when echoes are on the way; trims the next hour when there are no echoes anywhere nearby. ----------
        let radarInfo = null, radarNow = null, radarDry = {};   // radarDry: hour indices radar shows clear of precipitation   // radarNow: reflectivity right over the location { z (dBZ), z3 (max within ~15 km), t }
        const RADAR_IS = 'https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity_time/ImageServer';
        // This NOAA mosaic draws reflectivity on a continuous colour path (calibrated Oct 2026 against IEM's numeric N0Q
        // composite): grey-blue -> blue -> cyan -> teal -> bright green -> dark green -> yellow, then (standard positions,
        // not yet calibrated) orange -> red -> magenta. A sample is placed on the nearest segment and its dBZ interpolated.
        const DBZ_PATH = [[[138, 148, 178], 2], [[114, 129, 172], 6], [[86, 108, 164], 10], [[67, 94, 159], 13], [[75, 118, 173], 15], [[86, 149, 193], 17],
            [[94, 173, 207], 19], [[89, 189, 189], 21], [[83, 210, 167], 23], [[82, 214, 162], 24], [[55, 214, 105], 26], [[14, 214, 20], 28],
            [[13, 191, 19], 31], [[12, 159, 17], 34], [[10, 119, 13], 37], [[9, 94, 9], 40], [[58, 120, 7], 43], [[83, 134, 6], 45], [[132, 160, 5], 46],
            [[181, 186, 3], 47], [[230, 213, 1], 48], [[255, 226, 0], 49], [[255, 211, 0], 50], [[255, 197, 0], 51], [[255, 182, 0], 52],
            [[255, 150, 0], 54], [[255, 124, 0], 56], [[230, 0, 0], 60], [[180, 0, 0], 63], [[255, 0, 255], 66], [[150, 80, 200], 70]];   // calibrated to 53 dBZ (Oct 17); above that standard positions
        function rgbToDbz(v) {
            const p = String(v || '').trim().split(/[\s,]+/).map(Number);
            if (p.length < 3 || (p.length >= 4 && p[3] === 0) || (p[0] + p[1] + p[2] === 0)) return 0;
            let best = 0, bd = Infinity;
            for (let i = 0; i < DBZ_PATH.length - 1; i++) {
                const [a, za] = DBZ_PATH[i], [b, zb] = DBZ_PATH[i + 1];
                const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ap = [p[0] - a[0], p[1] - a[1], p[2] - a[2]];
                const L = ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2, t = L ? Math.max(0, Math.min(1, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / L)) : 0;
                const d = (ap[0] - t * ab[0]) ** 2 + (ap[1] - t * ab[1]) ** 2 + (ap[2] - t * ab[2]) ** 2;
                if (d < bd) { bd = d; best = za + t * (zb - za); }
            }
            return bd < 40 * 40 ? Math.round(best) : 0;   // not on the radar colour path (map features, artefacts)
        }
        // samples in chunks (large requests are sometimes refused), each retried once
        async function radarFrame(pts, t) {
            const out = new Array(pts.length).fill(0);
            for (let k = 0; k < pts.length; k += 400) {
                const chunk = pts.slice(k, k + 400);
                const body = new URLSearchParams({ geometry: JSON.stringify({ points: chunk, spatialReference: { wkid: 4326 } }), geometryType: 'esriGeometryMultipoint', returnFirstValueOnly: 'true', interpolation: 'RSP_NearestNeighbor', f: 'json' });
                if (t) body.set('time', String(t));
                let j = null;
                for (let a = 0; a < 2 && !(j && Array.isArray(j.samples)); a++) {
                    try { const r = await fetch(`${RADAR_IS}/getSamples`, { method: 'POST', body }); j = r.ok ? await r.json() : null; } catch (e) { j = null; }
                }
                if (!j || !Array.isArray(j.samples)) throw new Error('radar samples');
                j.samples.forEach(s => { const i = s.locationId != null ? s.locationId : null; if (i != null && i < chunk.length) out[k + i] = rgbToDbz(s.value); });
            }
            return out;
        }
        async function radarNowcast(lat, lon) {
            // 33 x 33 samples over +-1.5 deg (about 10 km apart); three frames 15 minutes apart
            const N = 33, C = 16, dLat = 1.5, dLon = 1.5 / Math.cos(lat * Math.PI / 180);
            const pts = [];
            for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) pts.push([+(lon - dLon + 2 * dLon * x / (N - 1)).toFixed(4), +(lat + dLat - 2 * dLat * y / (N - 1)).toFixed(4)]);
            const kmX = 2 * dLon * 111.32 * Math.cos(lat * Math.PI / 180) / (N - 1), kmY = 2 * dLat * 111.32 / (N - 1);
            const info = await (await fetch(`${RADAR_IS}?f=json`)).json();
            const tEnd = info && info.timeInfo && info.timeInfo.timeExtent ? info.timeInfo.timeExtent[1] : null;
            if (!tEnd || Date.now() - tEnd > 45 * 60e3) throw new Error('radar not current');
            const [B, M, A] = await Promise.all([radarFrame(pts, tEnd), radarFrame(pts, tEnd - 15 * 60e3), radarFrame(pts, tEnd - 30 * 60e3)]);
            const g = (arr, x, y) => (x < 0 || y < 0 || x >= N || y >= N) ? 0 : arr[y * N + x];
            // motion: the shift that best lays the earlier echoes onto the later ones (normalized overlap), refined to a
            // fraction of a cell; a shift at the edge of the search is not a real match
            const w = z => Math.max(0, z - 15);
            const match = (P, Q, R) => {
                let nP = 0, nQ = 0; for (let i = 0; i < N * N; i++) { nP += w(P[i]) ** 2; nQ += w(Q[i]) ** 2; }
                if (!(nP > 0 && nQ > 0)) return null;
                const S = {}, sc = (sx, sy) => { const k = sx + ',' + sy; if (S[k] === undefined) { let v = 0; for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const a = w(g(P, x, y)); if (a) v += a * w(g(Q, x + sx, y + sy)); } S[k] = v / Math.sqrt(nP * nQ); } return S[k]; };
                let best = { sx: 0, sy: 0, s: -1 };
                for (let sy = -R; sy <= R; sy++) for (let sx = -R; sx <= R; sx++) { const v = sc(sx, sy) - 0.004 * Math.hypot(sx, sy); if (v > best.s) best = { sx, sy, s: v }; }
                if (Math.abs(best.sx) === R || Math.abs(best.sy) === R) return null;
                const sub = (m, c, p) => { const d = m - 2 * c + p; return d < 0 ? Math.max(-0.5, Math.min(0.5, 0.5 * (m - p) / d)) : 0; };
                const c0 = sc(best.sx, best.sy);
                return { x: best.sx + sub(sc(best.sx - 1, best.sy), c0, sc(best.sx + 1, best.sy)), y: best.sy + sub(sc(best.sx, best.sy - 1), c0, sc(best.sx, best.sy + 1)), s: c0 };
            };
            const m30 = match(A, B, 7), m1 = match(A, M, 5), m2 = match(M, B, 5);
            // trust the motion only when the two 15-minute steps agree with the 30-minute step and the echoes held together
            const agree = m30 && m1 && m2 && m30.s > 0.35 && Math.abs(m1.x + m2.x - m30.x) <= 1.2 && Math.abs(m1.y + m2.y - m30.y) <= 1.2;
            let vx = agree ? m30.x / 30 : 0, vy = agree ? m30.y / 30 : 0;   // cells per minute (x east, y south)
            let moving = !!agree && Math.hypot(vx * kmX, vy * kmY) * 60 >= 5;
            if (Math.hypot(vx * kmX, vy * kmY) * 60 > 100) { vx = 0; vy = 0; moving = false; }   // over ~60 mph: not believable for a precipitation area
            let motionSrc = moving ? 'radar' : null;
            if (!moving) {
                // echoes changing too much to track: steer them with the model wind near 10,000 ft (700 mb), which moves showers and storms
                try {
                    const sj = await (await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat.toFixed(3)}&longitude=${lon.toFixed(3)}&hourly=wind_speed_700hPa,wind_direction_700hPa&forecast_hours=2&timezone=GMT`)).json();
                    const ws = sj && sj.hourly && sj.hourly.wind_speed_700hPa ? sj.hourly.wind_speed_700hPa[0] : null, wd = sj && sj.hourly ? sj.hourly.wind_direction_700hPa[0] : null;
                    if (ws != null && wd != null && ws >= 10 && ws <= 160) {
                        const r = wd * Math.PI / 180, ue = -ws * Math.sin(r), vn = -ws * Math.cos(r);   // km/h toward east / north
                        vx = ue / 60 / kmX; vy = -vn / 60 / kmY; moving = true; motionSrc = 'steering';
                    }
                } catch (e) {}
            }
            const near = (z, r) => { let m = 0; for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) m = Math.max(m, g(B, Math.round(C + z.x) + x, Math.round(C + z.y) + y)); return m; };
            // echo at the location after t minutes = echo now at (location - v*t)
            const ahead = t => {
                if (!moving && t > 20) return 0;          // motion unknown: radar speaks only for the next 20 minutes
                return near({ x: -vx * t, y: -vy * t }, t <= 15 ? 0 : 1);
            };
            // rain that has already passed: echoes just downstream of the location and none on the way
            let behind = 0; if (moving) for (let t = 10; t <= 90; t += 10) behind = Math.max(behind, near({ x: vx * t, y: vy * t }, 1));
            let upstream = 0; for (let t = 0; t <= 120; t += 10) upstream = Math.max(upstream, ahead(t));
            const passed = moving && behind >= 30 && upstream < 25;
            // when the precipitation over the location ends (two clear samples in a row along the trajectory)
            let endMin = null; if (g(B, C, C) >= 15 && moving) for (let t = 10; t <= 180; t += 10) if (ahead(t) < 15 && ahead(t + 10) < 15) { endMin = t; break; }
            // nothing more on the way for two hours after the current precipitation ends
            let after = 0; for (let t = endMin != null ? endMin : 0; t <= 120 + (endMin || 0); t += 10) after = Math.max(after, ahead(t));
            const clearUpstream = moving && (g(B, C, C) < 15 || endMin != null) && after < 20;
            let any = 0; for (let i = 0; i < N * N; i++) if (B[i] >= 20) { const x = i % N, y = Math.floor(i / N); if (Math.hypot((x - C) * kmX, (y - C) * kmY) <= 100) any++; }
            let arrive = null; for (let t = 0; t <= 180; t += 10) if (ahead(t) >= 20) { arrive = t; break; }
            const speedKmh = Math.hypot(vx * kmX, vy * kmY) * 60;
            return { here: g(B, C, C), here3: near({ x: 0, y: 0 }, 1), passed, clearUpstream, endMin, motionSrc, ahead, any, arrive, speedKmh, vx, vy, kmX, kmY, peak: arrive !== null ? Math.max(...[0, 10, 20, 30, 40, 50, 60].map(d => ahead(arrive + d))) : 0, t: tEnd, moving };
        }
        function applyRadarNowcast(rn) {
            const h = ensembleData && ensembleData.hourly; if (!h || !rn) return;
            radarDry = {};
            if (h._preRadar) { Object.entries(h._preRadar).forEach(([j, v]) => { h.precipitation_probability[j] = v.pp; h.weather_code[j] = v.code; }); h._preRadar = null; }   // undo the carried-over result
            const cur = hourlyStart(), ct = ensembleData.current && ensembleData.current.time;
            const mm = ct ? (parseInt(ct.slice(14, 16)) || 0) : 0;
            const P = [90, 80, 65, 50];
            for (let k = 0; k <= 3; k++) {
                const j = cur + k; if (j >= h.time.length) break;
                const t0 = Math.max(0, k * 60 - mm), t1 = k * 60 - mm + 60;
                let z = 0; for (let t = t0; t <= t1; t += 10) z = Math.max(z, rn.ahead(t));
                const pp = h.precipitation_probability[j] || 0;
                if (z >= 20) {
                    h.precipitation_probability[j] = Math.max(pp, z >= 30 ? P[k] : P[k] - 15);
                    const wc = h.weather_code[j] || 0;
                    const th = typeof thunderAt === 'function' ? thunderAt(j) : null;
                    const thunderOK = z >= 50 && ((th != null && th >= 15) || (typeof spcThunderAt === 'function' && spcThunderAt(Date.now() + k * 36e5)));
                    if (thunderOK) h.weather_code[j] = Math.max(wc, 95);
                    else if (!(wc >= 51 && wc <= 94)) h.weather_code[j] = z >= 40 ? 82 : z >= 30 ? 81 : 80;   // showers by intensity
                } else if (rn.passed && k <= 2) {
                    h.precipitation_probability[j] = Math.min(pp, 20);
                    radarDry[j] = true;
                } else if (rn.any === 0 && k <= 1) {
                    h.precipitation_probability[j] = Math.min(pp, 15);
                    radarDry[j] = true;
                } else if (rn.clearUpstream && k >= 1 && k <= 2) {
                    h.precipitation_probability[j] = Math.min(pp, 30);
                    if (h.precipitation_probability[j] < 40) radarDry[j] = true;
                }
            }
            try {   // remember this result for a quick reload
                const st = { saved: Date.now(), pp: {}, code: {}, dry: {} };
                for (let k = 0; k <= 3; k++) { const j = cur + k; if (j >= h.time.length) break; st.pp[h.time[j]] = h.precipitation_probability[j]; st.code[h.time[j]] = h.weather_code[j]; if (radarDry[j]) st.dry[h.time[j]] = true; }
                applyRadarNowcast._st = st;
            } catch (e) {}
            // one line for the forecast text, only for precipitation on the way (rain overhead is handled by current conditions)
            radarInfo = null;
            if (rn.motionSrc === 'radar' && rn.arrive !== null && rn.arrive >= 15 && rn.arrive <= 150) {
                const tz = ensembleData.timezone;
                const when = new Date(Math.round((Date.now() + rn.arrive * 60e3) / 9e5) * 9e5).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: tz });
                const snowy = (() => { const c = getCurrentConditions(); return c && c.temp != null && c.temp <= 0.5; })();
                const th0 = typeof thunderAt === 'function' ? thunderAt(hourlyStart() + 1) : null, tsOK = rn.peak >= 50 && ((th0 != null && th0 >= 15) || (typeof spcThunderAt === 'function' && spcThunderAt(Date.now())));
                const what = snowy ? (rn.peak >= 30 ? 'Snow' : 'Light snow') : tsOK ? 'Thunderstorms' : rn.peak >= 40 ? 'Heavy rain' : rn.peak >= 30 ? 'Rain' : 'Light rain';
                radarInfo = { msg: `${what} arriving around ${when}.` };
            }
        }
        async function loadRadar(token, lat, lon) {
            if (!nwsOffice || !spcInConus(lat, lon)) { radarInfo = null; return; }
            try {
                const rn = await radarNowcast(+lat, +lon);
                if (token !== fetchToken) return;
                radarNow = { z: rn.here, z3: rn.here3, t: rn.t, clearAhead: rn.passed || rn.arrive === null || rn.clearUpstream, endMin: rn.endMin };
                if (applyRadarNowcast._st) saveRadarState({ ...applyRadarNowcast._st, now: radarNow, info: radarInfo });
                window._lastRadar = { here: rn.here, here3: rn.here3, passed: rn.passed, clearUpstream: rn.clearUpstream, endMin: rn.endMin, motionSrc: rn.motionSrc, moving: rn.moving, mph: Math.round(rn.speedKmh * 0.621), arrive: rn.arrive, peak: rn.peak, any: rn.any, ahead: [0, 30, 60, 90, 120, 150, 180].map(t => rn.ahead(t)) };   // diagnostics
                applyRadarNowcast(rn);
                recomputeForecast();
            } catch (e) { console.warn('Radar nowcast unavailable:', e); }
        }
        function recomputeForecast() {
            try {
                computeBestBetPredictions(); applyOvernightLows(); applyRemainingToday(); applyContinuity(); floorTodayHigh();
                annotateThunder(); raiseTodayHigh();
                _adjCache = null;
                renderDashboard(); renderDiscussion();
            } catch (e) { console.warn(e); }
        }

