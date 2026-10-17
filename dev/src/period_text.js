        // ---------- Period forecast wording: precipitation as a range near the end, and a full wind sentence ----------
        // e.g. 'A trace to 0.10" of rain this morning, then a slight chance of rain this afternoon with the potential for an
        // additional 0.05". Winds from the south at 5-10 mph with gusts to 20 mph, becoming calm in the afternoon.'
        const PT_DIRS = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];
        // model spread for a day: how far the wettest and driest models sit from the middle one
        function ptSpread(dateStr) {
            try {
                const md = modelDataRaw && modelDataRaw.daily; if (!md || !md.time) return null;
                const i = md.time.indexOf(dateStr); if (i < 0) return null;
                const v = Object.keys(md).filter(k => /^precipitation_sum_/.test(k)).map(k => md[k][i]).filter(x => x != null && !isNaN(x)).sort((a, b) => a - b);
                if (v.length < 3) return null;
                const med = v[Math.floor(v.length / 2)]; if (!(med > 0.2)) return null;
                return { lo: Math.max(0.15, Math.min(1, v[0] / med)), hi: Math.max(1.4, Math.min(2.2, v[v.length - 1] / med)) };
            } catch (e) { return null; }
        }
        function ptRange(lowMm, highMm, snow) {
            const imp = isImperial;
            const steps = snow ? (imp ? [0, 1, 2, 3, 4, 6, 8, 10, 12, 18, 24, 36] : [0, 2, 5, 10, 15, 20, 30, 45, 60, 90])
                               : (imp ? [0, 0.05, 0.10, 0.15, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00, 2.50, 3.00, 4.00, 5.00, 6.00, 8.00] : [0, 1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]);
            const lo = imp ? (snow ? lowMm / 2.54 : lowMm / 25.4) : lowMm, hi = imp ? (snow ? highMm / 2.54 : highMm / 25.4) : highMm;   // snow arrives in cm
            let a = 0; steps.forEach(s => { if (s <= lo) a = s; });
            let b = steps.find(s => s >= hi && s > a); if (b === undefined) b = steps[steps.length - 1];
            const f = x => snow ? `${x}` : imp ? x.toFixed(2) : `${x}`;
            const unit = snow ? (imp ? (b === 1 ? ' inch' : ' inches') : ' cm') : (imp ? '"' : ' mm');
            return { a, b, text: a === 0 ? (snow ? `up to ${f(b)}${unit}` : `a trace to ${f(b)}${unit}`) : `${f(a)} to ${f(b)}${unit}`, upTo: `${f(b)}${unit}` };
        }
        function ptSeg(s, e) {
            const h = ensembleData.hourly, ok = v => v !== null && v !== undefined && !isNaN(v);
            let pp = 0, wet = 0, snowCm = 0, tsum = 0, tn = 0;   // (pp / wet may be raised below when precipitation is falling now)
            for (let j = s; j < e && j < h.time.length; j++) {
                if (ok(h.precipitation_probability[j])) pp = Math.max(pp, h.precipitation_probability[j]);
                if (hourWetCode(j)) wet++;
                if (h.snowfall && ok(h.snowfall[j])) snowCm += h.snowfall[j];
                if (ok(h.temperature_2m[j])) { tsum += h.temperature_2m[j]; tn++; }
            }
            let amt = periodAmount(s, e);
            const cur = hourlyStart();
            if (s <= cur && cur < e) {   // precipitation falling now: this part of the period is certain, and lasts until it ends
                const nc = obsNowcast();
                if (nc && nc.wet) { pp = 100; wet = Math.max(wet, 1); const hrs = Math.max(1, Math.min(e, rainEndIdx()) - cur); amt = Math.max(amt, (nc.lastHourMm || 0.3) * hrs * 0.7, 0.2); }
            }
            const tm = tn ? tsum / tn : 5, adj = adjustSnow(amt, snowCm, tm, tm);
            return { pp, wet, amt, snow: adj.snow, rain: adj.rain, date: h.time[Math.min(s, h.time.length - 1)].slice(0, 10) };
        }
        // segs: [[label, startIdx, endIdx], ...] with labels such as 'this morning' or 'after midnight'
        function periodPrecipSentence(segs) {
            const out = []; let said = false;
            segs.forEach(([label, s, e]) => {
                if (e - s < 1) return;
                const g = ptSeg(s, e);
                if (g.pp < 20 || (g.amt < 0.1 && !g.wet)) return;
                if (g.wet && g.amt < 0.3) g.amt = 0.3;   // the text calls this part wet, so it always gets an amount
                const sp = ptSpread(g.date) || { lo: 0.5, hi: 1.8 };
                const isSnow = g.snow >= 0.5 && g.snow >= g.rain / 10;
                const best = isSnow ? g.snow : g.amt;
                const r = ptRange(best * sp.lo * (g.pp < 60 ? 0 : 1), best * sp.hi + (isSnow ? 0.5 : 0.5), isSnow);
                const what = isSnow ? 'snow' : 'rain', add = said ? 'an additional ' : '';
                if (g.pp >= 60 && g.wet) out.push(`${add}${r.text} of ${what} ${label}`);
                else if (g.pp >= 30) out.push(`a chance of ${what} ${label} with ${add}${r.upTo === r.text ? r.text : 'up to ' + r.upTo} possible`);
                else out.push(`a slight chance of ${what} ${label} with the potential for ${add}${r.upTo}`);
                said = true;
            });
            if (!out.length) return '';
            const t = out.join(', then ');
            return t[0].toUpperCase() + t.slice(1) + '.';
        }
        function ptWind(s, e) {
            const h = ensembleData.hourly, ok = v => v !== null && v !== undefined && !isNaN(v);
            let lo = Infinity, hi = 0, g = 0, u = 0, v = 0, ws = 0, n = 0;
            let rW = 1, rG = 1; try { rW = windCalib('wind_speed_10m'); rG = windCalib('wind_gusts_10m'); } catch (e2) {}
            for (let j = s; j < e && j < h.time.length; j++) {
                const w = windForecastAt('wind_speed_10m', j, rW), gg = windForecastAt('wind_gusts_10m', j, rG);
                if (ok(w)) { lo = Math.min(lo, w); hi = Math.max(hi, w); n++; }
                if (ok(gg)) g = Math.max(g, gg);
                const d = h.wind_direction_10m ? h.wind_direction_10m[j] : null;
                if (ok(d) && ok(w)) { const r = d * Math.PI / 180; u += w * Math.sin(r); v += w * Math.cos(r); ws += w; }
            }
            if (!n) return null;
            const dirDeg = ws > 0 ? (Math.atan2(u, v) * 180 / Math.PI + 360) % 360 : null, steady = ws > 0 ? Math.hypot(u, v) / ws : 0;
            return { lo, hi, g, dir: dirDeg, steady };
        }
        function periodWindSentence(segs) {
            const W = segs.filter(([, s, e]) => e - s >= 1).map(([label, s, e]) => ({ label, ...(ptWind(s, e) || {}) })).filter(x => x.hi != null);
            if (!W.length) return '';
            const notable = x => x.hi >= 13 || x.g >= 32;
            if (!W.some(notable)) return '';
            const k = isImperial ? 0.621371 : 1, unit = isImperial ? 'mph' : 'km/h';
            const rng = x => { let a = Math.floor(x.lo * k / 5) * 5, b = Math.ceil(x.hi * k / 5) * 5; if (b - a < 5) a = Math.max(0, b - 5); return a <= 0 ? `up to ${b} ${unit}` : `${a}-${b} ${unit}`; };
            const gust = x => x.g >= 30 && x.g >= x.hi + 13 ? ` with gusts to ${Math.round(x.g * k / 5) * 5} ${unit}` : '';
            const dirW = x => x.dir == null || x.steady < 0.5 ? null : PT_DIRS[Math.round(x.dir / 45) % 8];
            const A = W.find(notable) || W[0];
            const dA = dirW(A);
            let t = `${dA ? `Winds from the ${dA}` : 'Variable winds'} at ${rng(A)}${gust(A)}`;
            const hiA = Math.ceil(A.hi * k / 5) * 5;
            for (const B of W.slice(W.indexOf(A) + 1)) {   // the first later part of the period that is clearly different
                const dB = dirW(B), diff = A.dir != null && B.dir != null ? Math.abs(((B.dir - A.dir + 540) % 360) - 180) : 0, hiB = Math.ceil(B.hi * k / 5) * 5;
                if (B.hi < 6) { t += `, becoming calm ${B.label}`; break; }
                if (dB && dA && diff >= 67.5) { t += `, becoming ${dB} ${B.label}${hiB !== hiA ? ` at ${rng(B)}` : ''}`; break; }
                if (hiB <= hiA - 10) { t += `, diminishing to ${rng(B)} ${B.label}`; break; }
                if (hiB >= hiA + 10) { t += `, increasing to ${rng(B)}${gust(B)} ${B.label}`; break; }
            }
            return t + '.';
        }
        function periodExtras(segs) { return [periodPrecipSentence(segs), periodWindSentence(segs)].filter(Boolean); }
        // the rest of today (from now) and tonight, as labelled segments
        function todaySegs() {
            const h = ensembleData.hourly, d0 = ensembleData.daily.time[0], first = h.time.findIndex(t => t.startsWith(d0)), cur = hourlyStart();
            return [['this morning', 6, 12], ['this afternoon', 12, 18], ['this evening', 18, 24]].map(([l, a, b]) => [l, Math.max(first + a, cur), first + b]).filter(([, s, e]) => e - s >= 1);
        }
        function tonightSegs(ni) {
            const h = ensembleData.hourly, cur = hourlyStart();
            let endIdx = h.time.findIndex(t => t >= ni.end); if (endIdx < 0) endIdx = h.time.length;
            const mid = h.time.findIndex((t, j) => j > cur && t.slice(11, 13) === '00');
            if (ni.early || mid < 0 || mid >= endIdx) return [['overnight', cur, endIdx]];
            return [['this evening', cur, mid], ['after midnight', mid, endIdx]].filter(([, s, e]) => e - s >= 1);
        }
