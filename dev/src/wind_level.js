        // ---------- Breezy / windy / very windy ----------
        // sustained wind (not gusts) for a stretch of hours: breezy 10+ mph, windy 20+ mph, very windy 30+ mph or while a
        // wind advisory / high wind / tropical storm / hurricane warning is in effect
        const WIND_WORD = ['', 'breezy', 'windy', 'very windy'];
        const WIND_ALERT_RE = /wind advisory|high wind|extreme wind|hurricane warning|tropical storm warning/i;
        function windAlertAt(ms) {
            return (nwsAlerts || []).some(a => WIND_ALERT_RE.test(a.event || '') && Date.parse(a.onset || a.effective || 0) <= ms && ms < Date.parse(a.ends || a.expires || 0));
        }
        function windLevelOf(kmh) { return kmh >= 48 ? 3 : kmh >= 32 ? 2 : kmh >= 16 ? 1 : 0; }
        let _wR = null;
        function windHourKmh(j) {
            try {
                if (!_wR || _wR.d !== ensembleData) _wR = { d: ensembleData, r: windCalib('wind_speed_10m') };
                const w = windForecastAt('wind_speed_10m', j, _wR.r);
                return w == null || isNaN(w) ? null : w;
            } catch (e) { return null; }
        }
        function hourWindLevel(j) {
            let lv = windLevelOf(windHourKmh(j) || 0);
            try { if (windAlertAt(hourMs(j) + 18e5)) lv = 3; } catch (e) {}
            return lv;
        }
        // a stretch counts when the wind holds for more than a single hour (second-highest hour when there are 3+)
        function windLevel(s, e) {
            const h = ensembleData && ensembleData.hourly; if (!h) return 0;
            const v = []; let alert = 0;
            for (let j = Math.max(0, s); j < e && j < h.time.length; j++) {
                const w = windHourKmh(j); if (w != null) v.push(w);
                try { if (windAlertAt(hourMs(j) + 18e5)) alert++; } catch (x) {}
            }
            if (alert >= Math.min(2, Math.max(1, e - s))) return 3;
            if (!v.length) return 0;
            v.sort((a, b) => b - a);
            return windLevelOf(v[Math.min(v.length >= 3 ? 1 : v.length - 1, v.length - 1)]);
        }
        // sky words for one part of a period, given the part before it
        function skyWindState(prev, sky, lv) {
            if (prev && prev.sky === sky) return lv ? `becoming ${WIND_WORD[lv]}` : 'less windy';
            return lv ? `${sky} and ${WIND_WORD[lv]}` : sky;
        }
        // the same wind level across several sky changes is said once: 'Overcast this morning, partly cloudy this afternoon,
        // then clear this evening. Breezy through this afternoon.' Returns the extra sentence ('' when nothing changes).
        function windSummary(parts) {
            if (!parts || parts.length < 2) return '';
            // first stretch of 2+ parts with the same wind level whose skies differ
            let i = 0, k = -1;
            for (; i < parts.length - 1; i++) {
                if (!parts[i].lv) continue;
                k = i; while (k + 1 < parts.length && parts[k + 1].lv === parts[i].lv && parts[k + 1].sky !== parts[k].sky) k++;
                if (k > i) break; k = -1;
            }
            if (k < 0) return '';
            const L = parts[i].lv;
            for (let m = i; m <= k; m++) parts[m].state = parts[m].sky;
            const W = WIND_WORD[L], Wc = W[0].toUpperCase() + W.slice(1);
            const lab = (p, last) => { let l = last ? p.labels[p.labels.length - 1] : p.labels[0]; return /^(this|in the|after)\b/.test(l) ? l.replace(/^in the /, 'the ') : 'this ' + l; };
            const end = k === parts.length - 1;
            if (i === 0 && end) return `${Wc}.`;
            if (i === 0) return `${Wc} through ${lab(parts[k], true)}.`;
            if (end) return `Becoming ${W} ${lab(parts[i], false).replace(/^the /, 'in the ')}.`;
            return `${Wc} ${lab(parts[i], false).replace(/^the /, 'in the ')} through ${lab(parts[k], true)}.`;
        }
        function windPhrase(sky, s, e) { const lv = windLevel(s, e); return lv ? `${sky} and ${WIND_WORD[lv]}` : sky; }
        const WIND_TAG_CLS = ['', 'wl1', 'wl2', 'wl3'];
        // day card: daytime (6 AM to 6 PM, from now for today) or tonight
        function windTag(i, ni) {
            try {
                const h = ensembleData.hourly, d = ensembleData.daily;
                let s, e;
                if (ni) { const ts = tonightSegs(ni); s = ts[0][1]; e = ts[ts.length - 1][2]; }
                else { const f = h.time.findIndex(t => t.startsWith(d.time[i])); if (f < 0) return ''; s = Math.max(f + 6, i === 0 ? hourlyStart() : 0); e = f + 18; }
                const lv = windLevel(s, e); if (!lv) return '';
                const w = WIND_WORD[lv];
                return `<span class="wtag ${WIND_TAG_CLS[lv]}" title="${w[0].toUpperCase() + w.slice(1)}"><i class="fa-solid fa-wind"></i> ${w[0].toUpperCase() + w.slice(1)}</span>`;
            } catch (e) { return ''; }
        }
        // hourly cell: sustained speed once it is breezy
        function hourWindTag(j) {
            const lv = hourWindLevel(j); if (!lv) return '';
            const k = isImperial ? 0.621371 : 1, w = windHourKmh(j);
            return `<span class="hwind ${WIND_TAG_CLS[lv]}" title="${WIND_WORD[lv]}"><i class="fa-solid fa-wind"></i> ${w != null ? Math.round(w * k) + (isImperial ? ' mph' : '') : ''}</span>`;
        }
        // 'Now' cell: the observed wind
        function nowWindTag(cc) {
            if (!cc || cc.wind == null || isNaN(cc.wind)) return '';
            let lv = windLevelOf(cc.wind); try { if (windAlertAt(Date.now())) lv = 3; } catch (e) {}
            if (!lv) return '';
            const k = isImperial ? 0.621371 : 1;
            return `<span class="hwind ${WIND_TAG_CLS[lv]}" title="${WIND_WORD[lv]}"><i class="fa-solid fa-wind"></i> ${Math.round(cc.wind * k)}${isImperial ? ' mph' : ''}</span>`;
        }
        // wind for a period said on its own (used when precipitation is falling and the sky sentence is skipped):
        // 'Breezy.' / 'Breezy this morning.' / 'Breezy through this afternoon.' / 'Becoming windy this evening.'
        function windSentence(segs) {
            const L = segs.filter(([, s, e]) => e - s >= 1).map(([label, s, e]) => ({ label, lv: windLevel(s, e) }));
            const i = L.findIndex(x => x.lv > 0); if (i < 0) return '';
            let k = i; while (k + 1 < L.length && L[k + 1].lv === L[i].lv) k++;
            const W = WIND_WORD[L[i].lv], Wc = W[0].toUpperCase() + W.slice(1);
            if (i === 0 && k === L.length - 1) return `${Wc}.`;
            if (i === 0) return k === 0 ? `${Wc} ${L[0].label}.` : `${Wc} through ${L[k].label}.`;
            return `Becoming ${W} ${L[i].label}.`;
        }
        // '... then clear this evening. Breezy' + 'high near 53' -> '... then clear this evening. Breezy, with a high near 53.'
        function withHigh(phrase, hi) {
            const m = String(phrase).match(/^(.*)\. (Breezy|Windy|Very windy)\.?$/);
            return m ? `${m[1]}. ${m[2]}, with a ${hi}.` : `${phrase}. ${hi[0].toUpperCase() + hi.slice(1)}.`;
        }
