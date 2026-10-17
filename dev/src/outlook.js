        // ---------- Text forecast for the next periods (tonight / tomorrow / tomorrow night / next day) ----------
        // Same wet-hour rule as the hourly icons and the hero sentence, so all three always agree.
        function phraseForSegments(segs) {
            const h = ensembleData.hourly, ok = v => v !== null && v !== undefined && !isNaN(v);
            const parts = [];
            let wetAll = false, codeAll = 0;
            segs.forEach(([label, s, e]) => {
                if (e - s < 2 || s < 0 || e > h.time.length) return;
                let cl = [], day = 0, n = 0, wetH = 0, wpp = 0, sn = 0, code = 0, thunderOK = false;
                for (let j = s; j < e; j++) {
                    n++;
                    if (h.cloud_cover && ok(h.cloud_cover[j])) cl.push(h.cloud_cover[j]);
                    if (h.is_day && h.is_day[j]) day++;
                    const wc = hourWetCode(j);
                    if (wc) {
                        wetH++; code = Math.max(code, wc);
                        wpp = Math.max(wpp, h.precipitation_probability && ok(h.precipitation_probability[j]) ? h.precipitation_probability[j] : 0);
                        if (h.snowfall && ok(h.snowfall[j])) sn += h.snowfall[j];
                        if (spcThunderAt(new Date(h.time[j]).getTime())) thunderOK = true;
                    }
                }
                const sky = skyCondition(cl.length ? cl.reduce((x, y) => x + y, 0) / cl.length : null, day >= n / 2).text.toLowerCase();
                let state = sky;
                if (wetH) {
                    wetAll = true; codeAll = Math.max(codeAll, code);
                    const kind = code >= 95 ? (thunderOK && wpp < 80 ? 'showers and thunderstorms' : 'thunderstorms') : sn >= 0.5 ? 'snow showers' : 'showers';
                    const widespread = wetH >= Math.max(2, n / 2);
                    if (wpp >= 80 && widespread) state = code >= 95 ? 'thunderstorms' : sn >= 0.5 ? 'snow' : 'rain';
                    else if (wpp >= 60) state = `${sky} with ${kind} likely`;
                    else state = `${sky} with a ${Math.round(wpp / 10) * 10}% chance of ${kind}`;
                }
                const last = parts[parts.length - 1];
                if (last && last.state === state) last.labels.push(label);
                else parts.push({ state, labels: [label] });
            });
            if (!parts.length) return null;
            const cap = t => t[0].toUpperCase() + t.slice(1);
            const text = parts.length === 1 ? cap(parts[0].state)
                : cap(parts.map((p, i) => `${p.state} ${p.labels.length > 1 ? 'through the ' + p.labels[p.labels.length - 1].replace(/^in the |^after /, '') : p.labels[0]}`).join(', then '));
            return { text, wet: wetAll };
        }
        function periodAmount(s, e) {
            const h = ensembleData.hourly, byDate = {};
            if (!h.precipitation) return 0;
            const hourlySum = {};
            h.time.forEach((t, j) => { const d = t.slice(0, 10); hourlySum[d] = (hourlySum[d] || 0) + (h.precipitation[j] || 0); });
            bestBetResults.forEach(b => { const full = b.full ? b.full.bestPrecip : b.bestPrecip; byDate[b.date] = hourlySum[b.date] > 0 ? full / hourlySum[b.date] : 1; });
            let a = 0;
            for (let j = s; j < e && j < h.time.length; j++) a += (h.precipitation[j] || 0) * (byDate[h.time[j].slice(0, 10)] ?? 1);
            return a;
        }
        function periodGust(s, e) {
            let g = 0;
            try {
                const r = windCalib('wind_gusts_10m');
                for (let j = s; j < e; j++) { const v = windForecastAt('wind_gusts_10m', j, r); if (v !== null && v > g) g = v; }
            } catch (e2) {}
            return g;
        }
        function renderHeroOutlook() {
            const box = document.getElementById('heroOutlook');
            if (!box) return;
            if (!ensembleData || !ensembleData.hourly || !bestBetResults.length) { box.innerHTML = ''; return; }
            const h = ensembleData.hourly, d0 = ensembleData.daily.time[0];
            const first = h.time.findIndex(t => t.startsWith(d0));
            if (first < 0) { box.innerHTML = ''; return; }
            const wd = k => { const ds = ensembleData.daily.time[k]; return ds ? new Date(ds + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long' }) : ''; };
            const night = !!nightInfo();
            const P = [];
            const dayP = k => ({ name: wd(k), k, night: false, segs: [['in the morning', first + 24 * k + 6, first + 24 * k + 12], ['in the afternoon', first + 24 * k + 12, first + 24 * k + 18]] });
            const nightP = (k, name) => ({ name, k, night: true, segs: [['in the evening', first + 24 * k + 18, first + 24 * k + 24], ['after midnight', first + 24 * k + 24, first + 24 * k + 30]] });
            if (!night) P.push(nightP(0, 'Tonight'), dayP(1), nightP(1, `${wd(1)} Night`));
            else P.push(dayP(1), nightP(1, `${wd(1)} Night`), dayP(2));
            const thunderRisk = (s, e) => {
                if (!spcData || !spcData.days) return null;
                let best = null;
                spcData.days.forEach(d => {
                    if (!d.cat || d.cat.n < 1) return;
                    const st = d.valid ? d.valid.getTime() : null; if (st === null) return;
                    const a = new Date(h.time[s]).getTime(), b = new Date(h.time[Math.min(e, h.time.length - 1)]).getTime();
                    if (a < st + 24 * 36e5 && b > st && (!best || d.cat.n > best.n)) best = d.cat;
                });
                return best;
            };
            const html = P.map(p => {
                const s = p.segs[0][1], e = p.segs[p.segs.length - 1][2];
                if (e > h.time.length) return '';
                const ph = phraseForSegments(p.segs);
                if (!ph) return '';
                const b = bestBetResults[p.k];
                const bits = [b ? withHigh(ph.text, p.night ? `low near ${formatTemp(b.bestMin)}` : `high near ${formatTemp(b.full ? b.full.bestMax : b.bestMax)}`) : ph.text + '.'];
                const amt = periodAmount(s, e);
                if (ph.wet && amt >= 2.5) bits.push(`About ${formatPrecip(amt)} possible.`);
                const sv = ph.wet && /thunder/.test(ph.text) ? thunderRisk(s, e) : null;
                if (sv) bits.push(sv.n >= 3 ? 'Severe storms possible.' : 'A few storms could be severe.');
                const g = periodGust(s, e);
                if (g >= 40) bits.push(`Gusts to ${formatSpeed(g)}.`);
                return `<div class="ho-item"><div class="ho-name">${esc(p.name)}</div><p>${esc(bits.join(' '))}</p></div>`;
            }).join('');
            box.innerHTML = html;
        }

