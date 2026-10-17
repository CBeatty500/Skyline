        // ---------- Continuity between loads for the hourly forecast (2 h and beyond) ----------
        // New model runs and grids arrive every hour; small changes are held, moderate ones go halfway, large ones are taken
        // (those come from real new information). The radar / observation hours (now and the next hour) are left alone.
        function hourlyContinuity() {
            const h = ensembleData && ensembleData.hourly; if (!h || NOLEARN) return;
            const key = 'skyline:hcont:' + learnLocKey();
            let prev = null; try { prev = JSON.parse(localStorage.getItem(key) || 'null'); } catch (e) {}
            const cur = hourlyStart(), now = Date.now();
            if (prev && now - prev.t < 3 * 36e5) {
                h.time.forEach((t, j) => {
                    if (j < cur + 2) return;
                    const p = prev.pp[t], c = prev.cc[t];
                    if (p != null && h.precipitation_probability[j] != null) {
                        const d = h.precipitation_probability[j] - p;
                        h.precipitation_probability[j] = Math.abs(d) < 10 ? p : Math.abs(d) < 30 ? Math.round(p + d / 2) : h.precipitation_probability[j];
                    }
                    if (c != null && h.cloud_cover[j] != null) {
                        const d = h.cloud_cover[j] - c;
                        h.cloud_cover[j] = Math.abs(d) < 15 ? c : Math.abs(d) < 40 ? c + d / 2 : h.cloud_cover[j];
                    }
                });
            }
            const pp = {}, cc = {};
            h.time.forEach((t, j) => { if (j >= cur && j < cur + 72) { pp[t] = h.precipitation_probability[j]; cc[t] = h.cloud_cover[j]; } });
            try { localStorage.setItem(key, JSON.stringify({ t: now, pp, cc })); } catch (e) {}
        }
        // the last radar result for this place (reused at once on a reload within 15 minutes, until fresh radar arrives)
        function saveRadarState(js) { try { localStorage.setItem('skyline:radar:' + learnLocKey(), JSON.stringify(js)); } catch (e) {} }
        function restoreRadarState() {
            if (NOLEARN) return;
            let s = null; try { s = JSON.parse(localStorage.getItem('skyline:radar:' + learnLocKey()) || 'null'); } catch (e) {}
            if (!s || Date.now() - s.saved > 15 * 60e3) return;
            const h = ensembleData.hourly;
            h._preRadar = {};
            h.time.forEach((t, j) => {
                if (s.pp[t] == null && s.code[t] == null) return;
                h._preRadar[j] = { pp: h.precipitation_probability[j], code: h.weather_code[j] };   // fresh radar starts from these
                if (s.pp[t] != null) h.precipitation_probability[j] = s.pp[t]; if (s.code[t] != null) h.weather_code[j] = s.code[t]; if (s.dry[t]) radarDry[j] = true;
            });
            if (s.now) radarNow = s.now;
            if (s.info) radarInfo = s.info;
        }
