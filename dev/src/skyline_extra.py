# extra output-level edits for skyline.html (exec'd by build_skyline.py with `out` in scope)
def _r(a, b):
    global out
    assert out.count(a) == 1, (a[:80], out.count(a))
    out = out.replace(a, b)
_a = out.index('        // Daily Records Table\n        function renderDailyRecordsTable() {')
_b = out.index('        // Render Charts (Hourly Temp & Precip)')
out = out[:_a] + open('/home/claude/daily_climate.js').read() + '\n' + out[_b:]
_r("if (i === 0) return 'Now'; if (hr % 3) return '';", "if (i === 0) return 'Now'; if (i < 3 || hr % 3) return '';")
_r('<td colspan="4" class="p-3 text-slate-400 italic">${histLoading', '<td colspan="7" class="p-3 text-slate-400 italic">${histLoading')

# ---- condition text -> icon: "Cloudy" / "Mostly Cloudy" are cloud, only partly/few clouds get the sun ----
_r("""            if (/overcast/.test(s)) return mk('fa-cloud', 'text-slate-400');
            if (/cloud/.test(s)) return mk(isDay ? 'fa-cloud-sun' : 'fa-cloud-moon', 'text-blue-300');
            if (/clear|fair|sunny/.test(s)) return isDay ? mk('fa-sun', 'text-amber-400') : mk('fa-moon', 'text-indigo-300');""",
"""            if (/partly|few clouds|mostly sunny|mostly clear|scattered clouds/.test(s)) return mk(isDay ? 'fa-cloud-sun' : 'fa-cloud-moon', 'text-blue-300');
            if (/overcast|cloud/.test(s)) return mk('fa-cloud', 'text-slate-400');
            if (/clear|fair|sunny/.test(s)) return isDay ? mk('fa-sun', 'text-amber-400') : mk('fa-moon', 'text-indigo-300');""")

# ---- location line: compact, sits beside the city name ----
_r("document.getElementById('displayLocationMeta').innerText = `Lat: ${currentLoc.lat.toFixed(4)}° | Lon: ${currentLoc.lon.toFixed(4)}° | Elevation: ${Math.round((currentLoc.ele || 0) * 3.28084).toLocaleString()} ft (${Math.round(currentLoc.ele || 0)} m)`;",
   "document.getElementById('displayLocationMeta').innerText = `Lat: ${currentLoc.lat.toFixed(4)}° ${String.fromCharCode(183)} Lon: ${currentLoc.lon.toFixed(4)}° ${String.fromCharCode(183)} Elev: ${isImperial ? Math.round((currentLoc.ele || 0) * 3.28084).toLocaleString() + ' ft' : Math.round(currentLoc.ele || 0).toLocaleString() + ' m'}`;")

# ---- per-day model consensus (spread of the model highs and lows) ----
_r("""                const acc = {};
                const weights = weightsForDay(i);""", """                const acc = {}, mHi = [], mLo = [];
                const weights = weightsForDay(i);""")
_r("""                    if (i === 0 && Object.values(row).some(v => v !== null)) modelComparisonDay0[m] = row;""",
   """                    if (row.max !== null) mHi.push(row.max);
                    if (row.min !== null) mLo.push(row.min);
                    if (i === 0 && Object.values(row).some(v => v !== null)) modelComparisonDay0[m] = row;""")
_r("""                    nwsBlendApplied
                });""", """                    nwsBlendApplied,
                    spreadHi: mHi.length >= 2 ? Math.max(...mHi) - Math.min(...mHi) : null,
                    spreadLo: mLo.length >= 2 ? Math.max(...mLo) - Math.min(...mLo) : null,
                    nModels: Math.max(mHi.length, mLo.length)
                });""")

# ---- forecast cards: chance + wind near the top, consensus as a quiet footer, past periods removed ----
_BOTTOM = """                        <div class="pt-2 border-t border-slate-800/80 flex justify-between items-center text-[11px] text-slate-400 font-mono">
                            <span><i class="fa-solid fa-umbrella text-blue-400 mr-1"></i>${pv.precipProb}%</span>
                            <span><i class="fa-solid fa-wind text-slate-400 mr-1"></i>${compass(bb.windDir) ? compass(bb.windDir) + ' ' : ''}${formatSpeed(pv.bestWind)}</span>
                        </div>"""
_r(_BOTTOM, """                        <div class="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono flex items-center justify-between gap-2" title="Spread between the individual model forecasts for this day">${consensusLine(bb)}</div>""")
_r("""                            ${ni ? periodStrip(i, 'tonight') : periodStrip(i)}""",
   """                            <div class="flex justify-between items-center text-[11px] text-slate-300 font-mono mb-2.5 px-0.5">
                                <span><i class="fa-solid fa-umbrella text-blue-400 mr-1"></i>${pv.precipProb}%</span>
                                <span><i class="fa-solid fa-wind text-slate-400 mr-1"></i>${compass(bb.windDir) ? compass(bb.windDir) + ' ' : ''}${formatSpeed(pv.bestWind)}</span>
                            </div>
                            ${ni ? periodStrip(i, 'tonight') : periodStrip(i)}""")
_r("""            if (ps && Array.isArray(only)) ps = ps.filter(p => only.includes(p.label));""",
   """            if (ps && Array.isArray(only)) ps = ps.filter(p => only.includes(p.label));
            if (ps) ps = ps.filter(p => !p.past);   // periods that are over drop off""")
_r("""        function updateConfidenceBadge() {""", """        function consensusLine(bb) {
            if (!bb || bb.spreadHi === null || bb.spreadHi === undefined) return `<span>Consensus: single model</span>`;
            const sp = Math.max(bb.spreadHi, bb.spreadLo ?? 0);
            const [t, c] = sp < 1.5 ? ['High', 'text-emerald-300/80'] : sp < 3 ? ['Moderate', 'text-amber-300/80'] : ['Low', 'text-rose-300/80'];
            const f = v => (v === null || v === undefined) ? '--' : `${(isImperial ? v * 1.8 : v).toFixed(1)}°`;
            return `<span>Consensus <span class="${c} font-semibold">${t}</span></span><span>spread H ${f(bb.spreadHi)} · L ${f(bb.spreadLo)}</span>`;
        }

        function updateConfidenceBadge() {""")


# ---- observations: Temperature, Dewpoint (+RH), Pressure, Wind, then the rest ----
_a = out.index("            const tiles = [\n                ['fa-wind', 'text-teal-400', 'Wind (from)'")
_b = out.index("                ['fa-eye', 'text-sky-300', 'Visibility'", _a)
_old = out[_a:_b]
_wind = "                ['fa-wind', 'text-teal-400', 'Wind (from)', windMain, windSub],\n"
_temp = "                ['fa-temperature-half', 'text-rose-400', 'Temperature', formatTemp(cc.temp, 1), `Feels like ${formatTemp(cc.apparent, 1)}`],\n"
_rh = "                ['fa-water', 'text-blue-400', 'Relative Humidity', n(cc.rh) ? `${Math.round(cc.rh)}%` : '--', ''],\n"
for _x in (_wind, _temp, _rh): assert _old.count(_x) == 1, _x
_pi = _old.index("                pressureMode === 'stn'")
_press = _old[_pi:]
_dew = "                ['fa-droplet', 'text-teal-400', 'Dewpoint', `${formatTemp(cc.dew, 1)}${n(cc.rh) ? ` <span class=\"text-xs font-semibold text-sky-200/90 ml-1\">RH ${Math.round(cc.rh)}%</span>` : ''}`, getDewPointCategory(cc.dew)],\n"
out = out[:_a] + "            const tiles = [\n" + _temp + _dew + _press + _wind + out[_b:]

# ---- pressure tendency from measured station pressure (last 3 h of observations), never the model ----
_a = out.index("        function pressureTendency() {")
_b = out.index("        // Full current-conditions detail panel", _a)
out = out[:_a] + r"""        function pressureTendency() {
            const obs = (nwsObsToday || []).filter(o => o && o.timestamp);
            if (obs.length < 2) return null;
            const val = (o, k) => (o[k] && o[k].value !== null && o[k].value !== undefined && !isNaN(o[k].value)) ? o[k].value / 100 : null;
            const sorted = obs.slice().sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            for (const k of ['seaLevelPressure', 'barometricPressure']) {
                const latest = sorted.find(o => val(o, k) !== null);
                if (!latest) continue;
                const t0 = new Date(latest.timestamp).getTime();
                let best = null, bestOff = Infinity;
                sorted.forEach(o => {
                    const v = val(o, k); if (v === null) return;
                    const off = Math.abs((t0 - new Date(o.timestamp).getTime()) / 36e5 - 3);
                    if (off < bestOff) { bestOff = off; best = o; }
                });
                if (!best || bestOff > 0.75) continue;
                const hrs = (t0 - new Date(best.timestamp).getTime()) / 36e5;
                const d = (val(latest, k) - val(best, k)) * 3 / hrs;   // per 3 hours
                return { d, text: d >= 1 ? 'Rising' : d <= -1 ? 'Falling' : 'Steady' };
            }
            return null;
        }

""" + out[_b:]
_r("${tend ? ` · ${tend.text} (${tend.d > 0 ? '+' : ''}${tend.d.toFixed(1)} mb/3h, model)` : ''}",
   "${tend ? ` · ${tend.text} (${tend.d > 0 ? '+' : ''}${tend.d.toFixed(1)} mb/3h)` : ''}")

# ---- "Average to date: " ----
out = out.replace('Average to date <b class="font-mono">', 'Average to date: <b class="font-mono">')
# ---- present weather before UV / AQI ----
_r("""            if (cc.wx && cc.wx.length) tiles.push(['fa-cloud-bolt', 'text-amber-400', 'Present Weather', esc(cc.wx.join(', ')), 'METAR coded']);\n""", "")
_r("""                ['fa-sun-plant-wilt', 'text-amber-400', 'UV Index',""",
   """                ...(cc.wx && cc.wx.length ? [['fa-cloud-bolt', 'text-amber-400', 'Present Weather', esc(cc.wx.join(', ')), 'METAR coded']] : []),
                ['fa-sun-plant-wilt', 'text-amber-400', 'UV Index',""")
# ---- wind: direction stays together; speed wraps as a unit ----
_r("""const windMain = calm ? 'Calm' : `${dirTxt ? `${dirTxt} ${Math.round(cc.dir)}° · ` : ''}${formatSpeed(cc.wind)}`;""",
   """const windMain = calm ? 'Calm' : `${dirTxt ? `<span class="whitespace-nowrap mr-2">${dirTxt} ${Math.round(cc.dir)}°</span>` : ''}<span class="whitespace-nowrap">${formatSpeed(cc.wind)}</span>`;""")

# ---- observation nowcast: precipitation falling now overrides the model for today / the current period ----
_r("""        function applyRemainingToday() {""", r"""        // What the station says is falling now, and how long ago precipitation last fell (latest 6 h of observations)
        function obsNowcast() {
            const kindOf = (codes, text) => {
                const cs = (codes || []).filter(c => c && !/^VC/.test(c));
                const has = re => cs.some(c => re.test(c));
                const t = (text || '').toLowerCase();
                if (has(/TS/) || /thunder/.test(t)) return 'thunder';
                if (has(/FZ(RA|DZ)/) || /freezing (rain|drizzle)/.test(t)) return 'freezing';
                if (has(/(SN|SG|PL|GS)/) && has(/(RA|DZ)/) || /mix|sleet|ice pellets/.test(t)) return 'mix';
                if (has(/(SN|SG)/) || /snow|flurr/.test(t)) return 'snow';
                if (has(/RA|SH/) || /rain|shower/.test(t)) return 'rain';
                if (has(/DZ/) || /drizzle/.test(t)) return 'drizzle';
                return null;
            };
            const cc = getCurrentConditions();
            if (!cc || !nwsObs) return null;
            const nowKind = kindOf(cc.wx, cc.text);
            const obs = (nwsObsToday || []).filter(o => o && o.timestamp).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            const t0 = obs.length ? new Date(obs[0].timestamp).getTime() : Date.now();
            let lastWet = null;
            for (const o of obs) {
                const age = (t0 - new Date(o.timestamp).getTime()) / 36e5;
                if (age > 6) break;
                const k = kindOf(Array.isArray(o.presentWeather) ? o.presentWeather.map(w => w.rawString) : [], o.textDescription);
                if (k) { lastWet = { kind: k, ago: age }; break; }
            }
            const lastHourMm = (cc.precip !== null && cc.precip !== undefined && !isNaN(cc.precip)) ? cc.precip : 0;
            if (nowKind) return { wet: true, kind: nowKind, lastHourMm };
            if (lastWet) return { wet: false, kind: lastWet.kind, endedAgo: lastWet.ago, lastHourMm,
                                  persist: Math.round(60 * Math.exp(-Math.max(0, lastWet.ago) / 1.5)) };   // showers often redevelop soon after they end
            return { wet: false, kind: null, lastHourMm };
        }
        const NOWCAST_CODE = { thunder: 95, freezing: 67, mix: 66, snow: 73, rain: 63, drizzle: 53 };
        const NOWCAST_WORD = { thunder: 'Thunderstorms', freezing: 'Freezing rain', mix: 'A wintry mix', snow: 'Snow', rain: 'Rain', drizzle: 'Drizzle' };
        // apply the nowcast to a forecast summary { pp, amt, snow, code } covering the period that includes now
        function nowcastAdjust(o) {
            const nc = obsNowcast();
            if (!nc) return o;
            if (nc.wet) {
                o.pp = 100;
                o.amt = Math.max(o.amt || 0, nc.lastHourMm, 0.5);
                if (nc.kind === 'snow' || nc.kind === 'mix') o.snow = Math.max(o.snow || 0, 0.6);
                o.code = Math.max(o.code || 0, NOWCAST_CODE[nc.kind] || 61);
            } else if (nc.persist) {
                o.pp = Math.max(o.pp || 0, nc.persist);
            }
            o.nowcast = nc;
            return o;
        }

        function applyRemainingToday() {""")
# today's best bet (rest of day)
_r("""                remaining: true, remainingLabel: tonight ? 'Tonight' : 'Rest of Today'
            });""", """                remaining: true, remainingLabel: tonight ? 'Tonight' : 'Rest of Today'
            });
            {
                const modelProb = bb.precipProb;
                const o = nowcastAdjust({ pp: bb.precipProb, amt: bb.bestPrecip, snow: bb.bestSnow, code: bb.weatherCode });
                bb.precipProb = Math.round(o.pp); bb.weatherCode = o.code; bb.nowcast = o.nowcast || null; bb.laterProb = modelProb;
                if (o.amt > bb.bestPrecip) { bb.bestRain += o.amt - bb.bestPrecip; bb.bestPrecip = o.amt; }
                if ((o.snow || 0) > bb.bestSnow) bb.bestSnow = o.snow;
            }""")
# tonight
_r("""            const tm = tn ? tsum / tn : nowT, sn = adjustSnow(rain, snowRaw, tm, tm);
            const cond = dailyCondition({ precipProb: pp, bestPrecip: rain, bestSnow: sn.snow, weatherCode: code,""",
   """            const tm = tn ? tsum / tn : nowT, sn = adjustSnow(rain, snowRaw, tm, tm);
            const ncT = nowcastAdjust({ pp, amt: rain, snow: sn.snow, code });
            pp = ncT.pp; code = ncT.code; if (ncT.amt > rain) { sn.rain += ncT.amt - rain; rain = ncT.amt; } if ((ncT.snow || 0) > sn.snow) sn.snow = ncT.snow;
            const cond = dailyCondition({ precipProb: pp, bestPrecip: rain, bestSnow: sn.snow, weatherCode: code,""")
_r("""            return { early, end, low: lo, high: rising ? hi : null, pp: Math.round(pp), rain: sn.rain, snow: sn.snow, wind, gust, cond };""",
   """            return { early, end, low: lo, high: rising ? hi : null, pp: Math.round(pp), rain: sn.rain, snow: sn.snow, wind, gust, cond, nowcast: ncT.nowcast || null };""")
# period icons: the period that contains now
_r("""                const tm = tn ? tsum / tn : 0, adj = adjustSnow(amt, snow, tm, tm);
                const cond = dailyCondition({ precipProb: pp, bestPrecip: amt, bestSnow: adj.snow, weatherCode: code,""",
   """                const tm = tn ? tsum / tn : 0, adj = adjustSnow(amt, snow, tm, tm);
                if (i === 0 && first + a <= cur && cur < first + b) { const o = nowcastAdjust({ pp, amt, snow: adj.snow, code }); pp = o.pp; amt = o.amt; adj.snow = o.snow; code = o.code; }
                const cond = dailyCondition({ precipProb: pp, bestPrecip: amt, bestSnow: adj.snow, weatherCode: code,""")
_r("""            return segs.filter(([, , e]) => e > nowKey).map(([label, a, b]) => rangeCondition(Math.max(idx(a), cur), Math.max(idx(b), idx(a) + 1), label)).filter(Boolean);""",
   """            const out2 = segs.filter(([, , e]) => e > nowKey).map(([label, a, b]) => rangeCondition(Math.max(idx(a), cur), Math.max(idx(b), idx(a) + 1), label)).filter(Boolean);
            const nc = obsNowcast();
            if (out2[0] && nc && nc.wet) {
                const c0 = dailyCondition({ precipProb: 100, bestPrecip: Math.max(0.5, nc.lastHourMm), bestSnow: (nc.kind === 'snow' || nc.kind === 'mix') ? 0.6 : 0, weatherCode: NOWCAST_CODE[nc.kind] || 61, cloud: 100 }, false);
                out2[0] = Object.assign({}, out2[0], { cond: c0, pp: 100 });
            }
            return out2;""")

# ---- temperature graph: phones show 6 h back / 48 h ahead; the view always opens at the current hour ----
_r("const cur = hourlyStart(), PAST = 12, NEXT = 48;", "const cur = hourlyStart(), PAST = window.matchMedia('(max-width: 767px)').matches ? 6 : 12, NEXT = 48;")
_r("""                // start the view a few hours before "Now" so recent observations and the coming hours are both visible
                requestAnimationFrame(() => { if (nowPos > 0) scroller.scrollLeft = Math.max(0, (nowPos - 6) * (inner.clientWidth / idx.length)); });""",
   """                // the view opens with the current hour at its left edge; earlier observations are a swipe back
                requestAnimationFrame(() => { if (nowPos > 0) { const sb = scroller.style.scrollBehavior; scroller.style.scrollBehavior = 'auto'; scroller.scrollLeft = Math.max(0, nowPos * (inner.clientWidth / idx.length) - 6); scroller.style.scrollBehavior = sb; } });""")
# quick view refresh with every dashboard render
_r("            renderHero();\n", "            renderHero();\n            renderQuickView();\n")

# ---- temperature graph: day/night shading, forecast high/low markers, Now just left of centre ----
_r("""                    // shade the observed (past) period and mark midnights
                    if (nowPos > 0) {""", """                    // daylight vs night from sunrise / sunset (soft twilight edges)
                    {
                        const dd = ensembleData.daily, colW = keys.length > 1 ? ch.scales.x.getPixelForValue(1) - ch.scales.x.getPixelForValue(0) : 40;
                        const k0 = new Date(keys[0] + ':00Z').getTime();
                        const xAt = iso => ch.scales.x.getPixelForValue(0) + (new Date(iso.slice(0, 16) + ':00Z').getTime() - k0) / 36e5 * colW;
                        const L = ch.chartArea.left - 40, R = ch.chartArea.right + 40;
                        const tw = colW * 2.75;   // twilight blend: about 1 h 20 min either side of sunrise / sunset
                        const srs = (dd.sunrise || []).filter(Boolean).map(s => s.slice(0, 16)), sss = (dd.sunset || []).filter(Boolean).map(s => s.slice(0, 16));
                        const back = s => { const t = new Date(s + ':00Z'); t.setUTCDate(t.getUTCDate() - 1); return t.toISOString().slice(0, 16); };
                        if (srs[0] && sss[0]) { srs.unshift(back(srs[0])); sss.unshift(back(sss[0])); }   // the past part of the graph
                        const band = (a, b, rgb, al) => {
                            a = Math.max(a, L); b = Math.min(b, R); if (b <= a) return;
                            const x0 = a - tw / 2, x1 = b + tw / 2, w = x1 - x0, f = Math.min(.45, tw / w);
                            const gr = g.createLinearGradient(x0, 0, x1, 0);
                            gr.addColorStop(0, `rgba(${rgb},0)`); gr.addColorStop(f, `rgba(${rgb},${al})`); gr.addColorStop(1 - f, `rgba(${rgb},${al})`); gr.addColorStop(1, `rgba(${rgb},0)`);
                            g.fillStyle = gr; g.fillRect(x0, top, w, bottom - top);
                        };
                        const DAY = ['190,220,255', .23], NIGHT = ['56,72,112', .30];
                        srs.forEach((sr, j) => {
                            const ss = sss[j]; if (!ss) return;
                            band(xAt(sr), xAt(ss), ...DAY);
                            const nextSr = srs[j + 1];
                            band(xAt(ss), nextSr ? xAt(nextSr) : R + tw, ...NIGHT);
                            if (j === 0) band(L - tw, xAt(sr), ...NIGHT);
                        });
                    }
                    // shade the observed (past) period and mark midnights
                    if (nowPos > 0) {""")
_r("""                    g.setLineDash([]); g.font = '600 11px Outfit, system-ui, sans-serif'; g.fillStyle = '#e2e8f0'; g.textAlign = 'center'; g.fillText('NOW', x, top - 6); g.restore();
                }, afterLayout(ch) {""", """                    g.setLineDash([]); g.font = '600 11px Outfit, system-ui, sans-serif'; g.fillStyle = '#e2e8f0'; g.textAlign = 'center'; g.fillText('NOW', x, top - 6); g.restore();
                    // forecast high / low: where and when each extreme is expected
                    const ext = [], days = [...new Set(keys.map(k => k.slice(0, 10)))];
                    const inWin = (i, a, b) => keys[i] >= a && keys[i] < b;
                    const nextDay = D => { const t = new Date(D + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 10); };
                    const prevDay = D => { const t = new Date(D + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() - 1); return t.toISOString().slice(0, 10); };
                    const pick = (a, b, hi) => {
                        let best = -1;
                        for (let i = 0; i < keys.length; i++) if (inWin(i, a, b) && fcT[i] !== null && fcT[i] !== undefined && (best < 0 || (hi ? fcT[i] > fcT[best] : fcT[i] < fcT[best]))) best = i;
                        if (best <= nowPos || best >= keys.length - 1) return -1;               // already happened, or cut off by the graph edge
                        if (keys[keys.length - 1] < b) return -1;                                     // window runs past the end of the graph
                        const p = fcT[best - 1], q = fcT[best + 1];                                    // must be a true turning point of the curve
                        if (p === null || p === undefined || q === null || q === undefined) return -1;
                        if (hi ? (fcT[best] < p || fcT[best] < q) : (fcT[best] > p || fcT[best] > q)) return -1;
                        return best;
                    };
                    days.forEach(D => {
                        const h = pick(`${D}T06:00`, `${D}T22:00`, true); if (h >= 0) ext.push([h, true]);
                        const l = pick(`${prevDay(D)}T18:00`, `${D}T11:00`, false); if (l >= 0) ext.push([l, false]);
                    });
                    g.save(); g.font = '700 10.5px Outfit, system-ui, sans-serif'; g.textAlign = 'center';
                    const fmtH = i => { const hr = +keys[i].slice(11, 13); return hr === 0 ? '12a' : hr === 12 ? '12p' : hr < 12 ? `${hr}a` : `${hr - 12}p`; };
                    ext.forEach(([i, hi]) => {
                        const px = ch.scales.x.getPixelForValue(i), py = ch.scales.y.getPixelForValue(fcT[i]);
                        const col = hi ? '#fda4af' : '#93c5fd';
                        const txt = `${hi ? 'H' : 'L'} ${Math.round(fcT[i])}°`;
                        const ty = hi ? py - 9 : py + 18;
                        const w = g.measureText(txt).width + 10;
                        g.fillStyle = 'rgba(8,15,32,.85)'; g.beginPath(); g.roundRect ? g.roundRect(px - w / 2, ty - 11, w, 15, 7) : g.rect(px - w / 2, ty - 11, w, 15); g.fill();
                        g.fillStyle = col; g.fillText(txt, px, ty);
                    });
                    g.restore();
                }, afterLayout(ch) {""")
_r("""                requestAnimationFrame(() => { if (nowPos > 0) { const sb = scroller.style.scrollBehavior; scroller.style.scrollBehavior = 'auto'; scroller.scrollLeft = Math.max(0, nowPos * (inner.clientWidth / idx.length) - 6); scroller.style.scrollBehavior = sb; } });""",
   """                requestAnimationFrame(() => { if (nowPos > 0) { const sb = scroller.style.scrollBehavior; scroller.style.scrollBehavior = 'auto'; const ch = chartInstances.hourlyTemp, nx = ch && ch.scales && ch.scales.x ? ch.scales.x.getPixelForValue(nowPos) : nowPos * (inner.clientWidth / idx.length); scroller.scrollLeft = Math.max(0, nx - scroller.clientWidth * 0.42); scroller.style.scrollBehavior = sb; } });""")
# give the H / L labels room
_r("""                        layout: { padding: { top: 18, right: 10 } },
                        plugins: { legend: { display: false }, tooltip: { enabled: false, external: ({ tooltip }) => { if (tooltip && tooltip.dataPoints && tooltip.dataPoints.length && tooltip.opacity) showReadout(tooltip.dataPoints[0].dataIndex); } } },""",
   """                        layout: { padding: { top: 18, right: 10 } },
                        plugins: { legend: { display: false }, tooltip: { enabled: false, external: ({ tooltip }) => { if (tooltip && tooltip.dataPoints && tooltip.dataPoints.length && tooltip.opacity) showReadout(tooltip.dataPoints[0].dataIndex); } } },""")

# ---- day + date label over each daylight segment, on the NOW line ----
_r("""                    g.setLineDash([]); g.font = '600 11px Outfit, system-ui, sans-serif'; g.fillStyle = '#e2e8f0'; g.textAlign = 'center'; g.fillText('NOW', x, top - 6); g.restore();
""", """                    g.setLineDash([]); g.font = '600 11px Outfit, system-ui, sans-serif'; g.fillStyle = '#e2e8f0'; g.textAlign = 'center'; g.fillText('NOW', x, top - 6);
                    {
                        const dd = ensembleData.daily, colW = keys.length > 1 ? ch.scales.x.getPixelForValue(1) - ch.scales.x.getPixelForValue(0) : 40;
                        const k0 = new Date(keys[0] + ':00Z').getTime();
                        const xAt = iso => ch.scales.x.getPixelForValue(0) + (new Date(iso.slice(0, 16) + ':00Z').getTime() - k0) / 36e5 * colW;
                        const srs = (dd.sunrise || []).filter(Boolean).map(s => s.slice(0, 16)), sss = (dd.sunset || []).filter(Boolean).map(s => s.slice(0, 16));
                        const back = s => { const t = new Date(s + ':00Z'); t.setUTCDate(t.getUTCDate() - 1); return t.toISOString().slice(0, 16); };
                        if (srs[0] && sss[0]) { srs.unshift(back(srs[0])); sss.unshift(back(sss[0])); }
                        const { left: AL, right: AR } = ch.chartArea, nowW = g.measureText('NOW').width;
                        g.font = '600 11px Outfit, system-ui, sans-serif'; g.fillStyle = '#bfdbfe';
                        const fmtD = (iso, o) => new Date(iso.slice(0, 10) + 'T12:00:00').toLocaleDateString('en-US', o);
                        const segs = [];
                        srs.forEach((sr, j) => {
                            const ss = sss[j]; if (!ss) return;
                            segs.push([sr, ss, fmtD(sr, { weekday: 'short', month: 'short', day: 'numeric' }), '#bfdbfe']);
                            const nsr = srs[j + 1] || (() => { const t = new Date(sr + ':00Z'); t.setUTCDate(t.getUTCDate() + 1); return t.toISOString().slice(0, 16); })();
                        });
                        segs.forEach(([s0, s1, txt, colr]) => {
                            const a = Math.max(xAt(s0), AL), b = Math.min(xAt(s1), AR);
                            if (b - a < 40) return;
                            const w = g.measureText(txt).width;
                            let cx = (a + b) / 2;
                            if (Math.abs(cx - x) < (w + nowW) / 2 + 12) {          // keep clear of the NOW label, staying inside the segment
                                const right = x + (w + nowW) / 2 + 12, left = x - (w + nowW) / 2 - 12;
                                cx = (right + w / 2 <= b) ? right : (left - w / 2 >= a) ? left : (b - x > x - a ? right : left);
                            }
                            if (cx - w / 2 < a - 20 || cx + w / 2 > b + 20) return;
                            g.fillStyle = colr; g.fillText(txt, cx, top - 6);
                        });
                    }
                    g.restore();
""")

# ---- daylight length on the forecast cards ----
_r("""                                <span class="text-amber-300" title="Sunrise"><i class="fa-solid fa-sun text-amber-400 mr-1"></i>${fmtClock(bb.sunrise)}</span>
                                <span class="text-orange-300" title="Sunset">""", """                                <span class="text-amber-300" title="Sunrise"><i class="fa-solid fa-sun text-amber-400 mr-1"></i>${fmtClock(bb.sunrise)}</span>
                                <span class="text-slate-300" title="Total daylight">${dayLength(bb.sunrise, bb.sunset)}</span>
                                <span class="text-orange-300" title="Sunset">""")
_r("""        function fmtClock(iso) {""", """        function dayLength(sr, ss) {
            if (!sr || !ss) return '';
            const m = Math.round((new Date(ss.slice(0, 16) + ':00Z') - new Date(sr.slice(0, 16) + ':00Z')) / 60000);
            return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`;
        }

        function fmtClock(iso) {""")

# ---- no subjective dewpoint descriptors ----
_r("$('currentDewPointCategory').innerText = getDewPointCategory(cc.dew);", "$('currentDewPointCategory').innerText = '';")
_r("""<span class="text-xs font-semibold text-sky-200/90 ml-1">RH ${Math.round(cc.rh)}%</span>` : ''}`, getDewPointCategory(cc.dew)],""",
   """<span class="text-xs font-semibold text-sky-200/90 ml-1">RH ${Math.round(cc.rh)}%</span>` : ''}`, ''],""")

# ---- one rule for precipitation amounts everywhere (forecast cards + quick view) ----
_a = out.index("                            <!-- Rain & Snow Forecast Accumulation Panel for each day -->")
_b = out.index("                            </div>\n", out.index("${formatSnow(pv.bestSnow)}</span>", _a)) + len("                            </div>\n")
out = out[:_a] + "                            ${precipPanel(i)}\n" + out[_b:]
_r("""        function dayLength(sr, ss) {""", r"""        // Precipitation shown for forecast day i. Amounts appear only when precipitation is expected (the same test that
        // drives the wet icons); today also carries what has already been measured, matching "Today So Far".
        function precipFor(i) {
            const b = bestBetResults[i]; if (!b) return null;
            const ni = i === 0 ? nightInfo() : null;
            const pp = ni ? ni.pp : b.precipProb, rain = ni ? ni.rain : b.bestRain, snow = ni ? ni.snow : b.bestSnow;
            const liquid = ni ? ni.rain + ni.snow : b.bestPrecip;
            const expected = precipExpected(pp, liquid);
            let soFar = null;
            if (i === 0) { const so = getTodaySoFar(); if (so && so.precip !== null && so.precip !== undefined && !isNaN(so.precip)) soFar = so.precip; }
            return { pp, expected, rain: expected ? rain : 0, snow: expected ? snow : 0, soFar };
        }
        function precipPanel(i) {
            const p = precipFor(i); if (!p) return '';
            const row = (ic, col, lab, val) => `<div class="flex justify-between items-center ${col}"><span class="text-slate-400 font-sans text-[10px] flex items-center gap-1"><i class="fa-solid ${ic}"></i> ${lab}</span><span class="font-bold">${val}</span></div>`;
            const rows = [];
            if (p.soFar !== null && (p.soFar > 0 || p.expected)) rows.push(row('fa-droplet text-blue-400', 'text-blue-200', 'Measured so far', formatPrecip(p.soFar)));
            if (p.expected) {
                if (p.rain >= 0.05 || p.snow < 0.05) rows.push(row('fa-cloud-rain text-indigo-400', 'text-indigo-300', i === 0 && p.soFar !== null ? 'Rain still to come' : 'Rain', formatPrecip(p.rain)));
                if (p.snow >= 0.05) rows.push(row('fa-snowflake text-cyan-400', 'text-cyan-300', i === 0 && p.soFar !== null ? 'Snow still to come' : 'Snow', formatSnow(p.snow)));
            }
            return rows.length ? `<div class="bg-slate-950/70 rounded-lg p-2 border border-slate-800/80 text-[11px] font-mono space-y-1 my-2">${rows.join('')}</div>` : '';
        }
        function precipCell(i) {
            const p = precipFor(i); if (!p) return '--';
            const amt = () => `<span class="text-blue-200">${formatPrecip(p.rain)}</span>${p.snow >= 0.05 ? ` <span class="text-cyan-200">+ ${formatSnow(p.snow)} snow</span>` : ''} <span class="text-slate-400">${p.pp}%</span>`;
            if (i === 0 && p.soFar !== null) {
                const sf = `<span class="${p.soFar > 0 ? 'text-blue-200 font-semibold' : 'text-slate-400'}">${formatPrecip(p.soFar)}</span>`;
                return p.expected ? `${sf} <span class="text-slate-500">·</span> ${amt().replace('<span class="text-blue-200">', '<span class="text-blue-200">+')}` : sf;
            }
            return p.expected ? amt() : '<span class="text-slate-500">—</span>';
        }

        function dayLength(sr, ss) {""")

# ---- fix: stray closing tag left after the precipitation panel; drop the per-card consensus footer ----
_r("""                            ${precipPanel(i)}
                            </div>
""", """                            ${precipPanel(i)}
""")
_r("""                        <div class="pt-2 border-t border-slate-800/80 text-[10px] text-slate-400 font-mono flex items-center justify-between gap-2" title="Spread between the individual model forecasts for this day">${consensusLine(bb)}</div>
""", "")

# ---- records only from official station climate data; reanalysis grid "records" (smoothed) are never used ----
_r("""        function getHistoricalStatsForDate(targetDateStr) {""", """        function getHistoricalStatsForDate(targetDateStr) {
            const st = rawHistoricalStatsForDate(targetDateStr);
            if (!st) return st;
            const key = targetDateStr.substring(5, 10);
            const cr = cliTotals && cliTotals.byMD && cliTotals.byMD[key];
            const sr = stationClim && stationClim.rec && stationClim.rec[key];
            const offHi = (cr && cr.hr !== undefined) || (sr && sr.hi !== null && sr.hi !== undefined);
            const offLo = (cr && cr.lr !== undefined) || (sr && sr.lo !== null && sr.lo !== undefined);
            return Object.assign({}, st, offHi ? {} : { recHigh: null, recHighYr: '' }, offLo ? {} : { recLow: null, recLowYr: '' });
        }

        function rawHistoricalStatsForDate(targetDateStr) {""")

# ---- international: station observations (IEM METAR) + regional high-resolution models ----
_r("""        async function fetchForecastData() {""", open('/home/claude/intl_obs.js').read() + """        async function fetchForecastData() {""")
_r("""                const nwsP = inUS ? fetchNWS(lat, lon) : Promise.resolve({ forecast: null, obs: null, alerts: [] });""",
   """                const nwsP = inUS ? fetchNWS(lat, lon) : Promise.resolve({ forecast: null, obs: null, alerts: [] });
                // where NWS has no station (outside the US, or it failed), use the nearest airport observations instead
                const intlP = nwsP.then(n => (n && n.obs) ? null : baseP.then(b => fetchIntlObs(lat, lon, b))).catch(() => null);""")
_r("""                const [models, nws, aq, pt, sn, cl] = await Promise.all([modelsP, nwsP, aqP, ptP, snP, clP]);""",
   """                const [models, nws, aq, pt, sn, cl, intl] = await Promise.all([modelsP, nwsP, aqP, ptP, snP, clP, intlP]);""")
_r("""                nwsObsToday = nws.obsToday || [];""", """                nwsObsToday = nws.obsToday || [];
                if (intl && intl.obs) { nwsObs = intl.obs; nwsObsToday = intl.obsToday; }""")
# models: base global set plus the best regional model for the location
_r("""models=ecmwf_ifs025,gfs_seamless,icon_seamless,gem_seamless&""", """models=${Object.keys(getModelWeights()).join(',')}&""")
_r("""        function getModelWeights() {
            const na = currentLoc.lat >= 15 && currentLoc.lat <= 75 && currentLoc.lon >= -170 && currentLoc.lon <= -50;
            return na ? { ecmwf_ifs025: 0.35, gfs_seamless: 0.35, icon_seamless: 0.15, gem_seamless: 0.15 }
                      : { ecmwf_ifs025: 0.40, gfs_seamless: 0.30, icon_seamless: 0.15, gem_seamless: 0.15 };
        }""", """        const MODEL_NAMES = { ecmwf_ifs025: 'ECMWF IFS', gfs_seamless: 'NOAA GFS', icon_seamless: 'DWD ICON', gem_seamless: 'CMC GEM',
            ukmo_seamless: 'UK Met Office', jma_seamless: 'JMA (Japan)', kma_seamless: 'KMA (Korea)', meteofrance_seamless: 'Météo-France AROME/ARPEGE',
            metno_nordic: 'MET Norway Nordic', bom_access_global: 'BOM ACCESS (Australia)', knmi_seamless: 'KNMI HARMONIE', dmi_seamless: 'DMI HARMONIE', cma_grapes_global: 'CMA GRAPES (China)' };
        // the regional high-resolution model (if any) that covers this location, with its starting weight
        function modelRegion() {
            const la = currentLoc.lat, lo = currentLoc.lon, inb = (a, b, c, d) => la >= a && la <= b && lo >= c && lo <= d;
            if (inb(15, 75, -170, -50)) return { label: 'North America', extra: {} };
            if (inb(24, 46, 122, 146)) return { label: 'Japan', extra: { jma_seamless: 0.30 } };
            if (inb(33, 39, 124, 131)) return { label: 'Korea', extra: { kma_seamless: 0.30 } };
            if (inb(49.5, 61, -11, 2)) return { label: 'British Isles', extra: { ukmo_seamless: 0.30 } };
            if (inb(54, 72, 4, 32)) return { label: 'Nordic', extra: { metno_nordic: 0.30, ukmo_seamless: 0.10 } };
            if (inb(50.5, 54, 3, 7.5)) return { label: 'Benelux', extra: { knmi_seamless: 0.25, ukmo_seamless: 0.10 } };
            if (inb(37, 56, -6, 17)) return { label: 'Western Europe', extra: { meteofrance_seamless: 0.25, ukmo_seamless: 0.10 } };
            if (inb(-45, -10, 112, 155)) return { label: 'Australia', extra: { bom_access_global: 0.25, ukmo_seamless: 0.10 } };
            if (inb(18, 54, 73, 135)) return { label: 'China', extra: { cma_grapes_global: 0.15, ukmo_seamless: 0.10 } };
            return { label: 'Global', extra: { ukmo_seamless: 0.15 } };
        }
        function getModelWeights() {
            const reg = modelRegion();
            const base = reg.label === 'North America' ? { ecmwf_ifs025: 0.35, gfs_seamless: 0.35, icon_seamless: 0.15, gem_seamless: 0.15 }
                                                      : { ecmwf_ifs025: 0.40, gfs_seamless: 0.30, icon_seamless: 0.15, gem_seamless: 0.15 };
            const w = { ...base, ...reg.extra };
            const tot = Object.values(w).reduce((a, b) => a + b, 0);
            Object.keys(w).forEach(k => { w[k] = w[k] / tot; });
            return w;
        }""")
_r("""            const na = w.gfs_seamless === 0.35;""", """            const reg = modelRegion();""")
_r("""            document.getElementById('regionBadge').innerText = na ? 'North America' : 'Global';
            const names = { ecmwf_ifs025: 'ECMWF IFS (0.25°)', gfs_seamless: 'NOAA GFS Seamless', icon_seamless: 'DWD ICON Seamless', gem_seamless: 'Environment Canada GEM' };""",
   """            document.getElementById('regionBadge').innerText = reg.label;
            const names = MODEL_NAMES;""")
_r("""            const modelNames = {
                'ecmwf_ifs025': 'ECMWF IFS 0.25°',
                'gfs_seamless': 'NOAA GFS',
                'icon_seamless': 'DWD ICON',
                'gem_seamless': 'CMC GEM'
            };""", """            const modelNames = MODEL_NAMES;""")

# international METARs rarely carry precipitation amounts: "not reported" rather than a false 0.00"
_r("""                } else if (tObs.length >= 3) {
                    out.precip = 0;""", """                } else if (tObs.length >= 3 && !(nwsObs && nwsObs.intl)) {
                    out.precip = 0;""")
_r("""                } else {
                    out.precipSrc = 'No station observations available';""", """                } else {
                    out.precipSrc = (nwsObs && nwsObs.intl) ? `${stn} does not report precipitation amounts` : 'No station observations available';""")

# ---- wind & gusts: multi-model consensus, calibrated to what the station has actually measured ----
_r("&hourly=temperature_2m&models=", "&hourly=temperature_2m,wind_gusts_10m,wind_speed_10m&models=")
_r("""        function obsHourMap() {""", r"""        // Observed wind / gust per local hour (km/h). A METAR with no gust group means no gusts, so the hour's
        // effective gust is the sustained wind.
        function obsWindHourMap() {
            const out = {};
            if (!ensembleData || !nwsObsToday || !nwsObsToday.length) return out;
            const fmt = new Intl.DateTimeFormat('en-CA', { timeZone: ensembleData.timezone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' });
            const hourKey = d => { const p = Object.fromEntries(fmt.formatToParts(d).map(x => [x.type, x.value])); return `${p.year}-${p.month}-${p.day}T${p.hour}:00`; };
            const kmh = v => { if (!v || v.value === null || v.value === undefined || isNaN(v.value)) return null; return (v.unitCode && v.unitCode.includes('m_s')) ? v.value * 3.6 : v.value; };
            nwsObsToday.forEach(o => {
                if (!o.timestamp) return;
                const w = kmh(o.windSpeed); if (w === null) return;
                const g = Math.max(w, kmh(o.windGust) || 0);
                const k = hourKey(new Date(o.timestamp));
                const e = out[k] || (out[k] = { w: 0, g: 0 });
                e.w = Math.max(e.w, w); e.g = Math.max(e.g, g);
            });
            return out;
        }
        // model consensus (median of the individual models) for an hourly wind field at ensemble hour index j
        let _windIdx = null;
        function modelWindAt(field, j) {
            const h = ensembleData.hourly, mh = modelDataRaw && modelDataRaw.hourly;
            const own = h[field] ? h[field][j] : null;
            if (!mh || !mh.time) return own;
            if (!_windIdx || _windIdx.src !== mh) { _windIdx = { src: mh, m: {} }; mh.time.forEach((t, k) => { _windIdx.m[t] = k; }); }
            const k = _windIdx.m[h.time[j]];
            if (k === undefined) return own;
            const vals = Object.keys(getModelWeights()).map(m => mh[`${field}_${m}`] ? mh[`${field}_${m}`][k] : null).filter(v => v !== null && v !== undefined && !isNaN(v)).sort((a, b) => a - b);
            if (!vals.length) return own;
            const mid = Math.floor(vals.length / 2);
            return vals.length % 2 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
        }
        // ratio of measured to modelled wind over the last 12 hours (1 = models right; < 1 = models too windy)
        function windCalib(field) {
            const obs = obsWindHourMap(), h = ensembleData.hourly, cur = hourlyStart();
            let so = 0, sm = 0, n = 0;
            for (let j = Math.max(0, cur - 12); j <= cur; j++) {
                const o = obs[h.time[j]], m = modelWindAt(field, j);
                if (!o || m === null || m === undefined || m < 5) continue;
                so += field === 'wind_gusts_10m' ? o.g : o.w; sm += m; n++;
            }
            if (n < 4 || sm <= 0) return 1;
            return Math.max(0.35, Math.min(1.3, so / sm));
        }
        // calibrated forecast at hour j: the measured/modelled ratio applies fully now and fades over about a day
        function windForecastAt(field, j, ratio) {
            const m = modelWindAt(field, j);
            if (m === null || m === undefined || isNaN(m)) return null;
            const ahead = Math.max(0, j - hourlyStart());
            return m * (1 + (ratio - 1) * Math.exp(-ahead / 18));
        }

        function obsHourMap() {""")
# tonight
_r("""            let lo = nowT, hi = nowT, pp = 0, rain = 0, snowRaw = 0, gust = 0, wind = 0, code = 0, tsum = 0, tn = 0; const cl = [];""",
   """            let lo = nowT, hi = nowT, pp = 0, rain = 0, snowRaw = 0, gust = 0, wind = 0, code = 0, tsum = 0, tn = 0; const cl = [];
            const rG = windCalib('wind_gusts_10m'), rW = windCalib('wind_speed_10m');""")
_r("""                if (h.wind_gusts_10m && ok(h.wind_gusts_10m[j])) gust = Math.max(gust, h.wind_gusts_10m[j]);
                if (h.wind_speed_10m && ok(h.wind_speed_10m[j])) wind = Math.max(wind, h.wind_speed_10m[j]);
                if (h.weather_code && ok(h.weather_code[j])) code = Math.max(code, h.weather_code[j]);
                if (h.cloud_cover && ok(h.cloud_cover[j])) cl.push(h.cloud_cover[j]);
            }""", """                { const g = windForecastAt('wind_gusts_10m', j, rG); if (ok(g)) gust = Math.max(gust, g); }
                { const w = windForecastAt('wind_speed_10m', j, rW); if (ok(w)) wind = Math.max(wind, w); }
                if (h.weather_code && ok(h.weather_code[j])) code = Math.max(code, h.weather_code[j]);
                if (h.cloud_cover && ok(h.cloud_cover[j])) cl.push(h.cloud_cover[j]);
            }
            gust = Math.max(gust, wind);""")
# rest of today
_r("""                bestWind: peak(h.wind_speed_10m, bb.bestWind),
                bestGust: peak(h.wind_gusts_10m, bb.bestGust),""", """                ...(() => {
                    const rG = windCalib('wind_gusts_10m'), rW = windCalib('wind_speed_10m');
                    let g = 0, w = 0, any = false;
                    ids.forEach(j => { if (j <= cur) return; const gv = windForecastAt('wind_gusts_10m', j, rG), wv = windForecastAt('wind_speed_10m', j, rW); if (gv !== null) { g = Math.max(g, gv); any = true; } if (wv !== null) w = Math.max(w, wv); });
                    return any ? { bestWind: w, bestGust: Math.max(g, w) } : { bestWind: peak(h.wind_speed_10m, bb.bestWind), bestGust: peak(h.wind_gusts_10m, bb.bestGust) };
                })(),""")

# ===================== round: polish for the public site =====================
# ---- trim leftover wording ----
_r("""<span class="text-xs text-amber-400 bg-amber-950/40 border border-amber-500/30 px-2.5 py-1 rounded-md font-mono"><i class="fa-solid fa-bullseye text-[10px] mr-1"></i> Best Bet Active</span>""", "")
_r("""                            <span class="bg-gradient-to-r from-amber-500/20 to-rose-500/20 text-amber-300 font-bold text-[10px] px-2.5 py-0.5 rounded uppercase tracking-wider font-mono border border-amber-500/30">
                                Climate Engine
                            </span>
""", "")
_r("""                        <p class="text-xs text-slate-400 mt-1">
                            Empirical calculations calculated directly from ECMWF ERA5 hourly/daily atmospheric observations for this coordinate grid.
                        </p>
""", "")
_r("""<i class="fa-solid fa-chart-line text-rose-400"></i> All-Time Historical Records & Decadal Warming Trend""", """<i class="fa-solid fa-chart-line text-rose-400"></i> Long-Term Climate Trend""")

# ---- the 1940-present reanalysis download waits until the climate section is near (US); immediately elsewhere ----
_r("""                const histDone = getHistorical(lat, lon).then(hist => {""", """                const histDone = climateGate(inUS && !!cl).then(() => getHistorical(lat, lon)).then(hist => {""")
_r("""        async function getHistorical(lat, lon) {""", """        // resolves once the climate section is within ~1.5 screens of view (or right away when not deferring)
        function climateGate(defer) {
            const el = document.getElementById('sec-climate');
            if (!defer || !el || !('IntersectionObserver' in window)) return Promise.resolve();
            return new Promise(res => {
                const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); res(); } }, { rootMargin: '1500px 0px' });
                io.observe(el);
            });
        }

        async function getHistorical(lat, lon) {""")

# ---- locations: remember the last city, shareable ?city= links, "use my location" ----
_r("""                out.state = (props.relativeLocation && props.relativeLocation.properties && props.relativeLocation.properties.state) || null;""",
   """                out.state = (props.relativeLocation && props.relativeLocation.properties && props.relativeLocation.properties.state) || null;
                out.city = (props.relativeLocation && props.relativeLocation.properties && props.relativeLocation.properties.city) || null;""")
_r("""                nwsState = nws.state || null;""", """                nwsState = nws.state || null;
                if (currentLoc.mine && nws.city) { currentLoc.name = `${nws.city}${nws.state ? ', ' + nws.state : ''}`; cityInput.value = currentLoc.name; }
                saveLocation();""")
_r("""        window.onload = function() {
            fetchForecastData();
        };""", r"""        // ---------- where to start: a shared link, then the visitor's last city, then the default ----------
        function saveLocation() {
            const L = currentLoc; if (!L || !isFinite(L.lat) || !isFinite(L.lon)) return;
            try { localStorage.setItem('skyline:lastLoc', JSON.stringify({ name: L.name, lat: L.lat, lon: L.lon, ele: L.ele || 0 })); } catch (e) {}
            try {
                const q = new URLSearchParams({ city: L.name, lat: (+L.lat).toFixed(4), lon: (+L.lon).toFixed(4) });
                history.replaceState(null, '', `${location.pathname}?${q.toString()}`);
                document.title = `${L.name} · Skyline Weather`;
            } catch (e) {}
        }
        async function startLocation() {
            const q = new URLSearchParams(location.search);
            const lat = parseFloat(q.get('lat')), lon = parseFloat(q.get('lon')), city = (q.get('city') || '').trim();
            if (isFinite(lat) && isFinite(lon)) { currentLoc = { name: city || `${lat.toFixed(2)}, ${lon.toFixed(2)}`, lat, lon, ele: 0 }; return; }
            if (city) {
                try {
                    const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city.split(',')[0])}&count=1&language=en&format=json`);
                    const j = await r.json(), g = j.results && j.results[0];
                    if (g) { currentLoc = { name: [g.name, g.admin1, g.country].filter(Boolean).join(', '), lat: g.latitude, lon: g.longitude, ele: g.elevation || 0 }; return; }
                } catch (e) {}
            }
            try { const s = JSON.parse(localStorage.getItem('skyline:lastLoc') || 'null'); if (s && isFinite(s.lat) && isFinite(s.lon)) currentLoc = s; } catch (e) {}
        }
        function useMyLocation() {
            if (!navigator.geolocation) { showToast('Location is not available in this browser.'); return; }
            const btn = document.getElementById('myLocBtn'); if (btn) btn.classList.add('busy');
            navigator.geolocation.getCurrentPosition(p => {
                if (btn) btn.classList.remove('busy');
                currentLoc = { name: 'My location', lat: +p.coords.latitude.toFixed(4), lon: +p.coords.longitude.toFixed(4), ele: 0, mine: true };
                cityInput.value = currentLoc.name;
                fetchForecastData();
            }, err => {
                if (btn) btn.classList.remove('busy');
                showToast(err && err.code === 1 ? 'Location permission was denied.' : 'Could not get your location.');
            }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
        }

        window.onload = async function() {
            await startLocation();
            if (cityInput) cityInput.value = currentLoc.name;
            fetchForecastData();
        };""")

# ---- Open-Meteo request budget: the 1940-present archive (heavy) loads only when its section is near;
#      places without NWS climate data get light 1991-2020 normals right away ----
_r("""const histDone = climateGate(inUS && !!cl).then(""", """if (!cl) getClimLite(lat, lon).then(d => { if (token !== fetchToken || !d || historicalData) return; climLite = d; buildClimIndex(); renderDashboard(); renderDiscussion(); }).catch(() => {});
                const histDone = climateGate(true).then(""")
_r("""                historicalData = null; histLoading = true;""", """                historicalData = null; climLite = null; histLoading = true;""")
_r("""            climIndex = null;
            if (!historicalData) return;
            const { time, temperature_2m_max: mx, temperature_2m_min: mn } = historicalData.daily;""", """            climIndex = null;
            const src = historicalData || climLite;
            if (!src) return;
            const { time, temperature_2m_max: mx, temperature_2m_min: mn } = src.daily;""")
_r("""        let stationClim = null;""", """        let stationClim = null;
        let climLite = null;   // 1991-2020 daily max/min from the reanalysis: normals only (about a quarter of the full archive's cost)
        async function getClimLite(lat, lon) {
            const key = `climlite1:${lat}:${lon}`;
            const c = await idb.get(key);
            if (c && Date.now() - c.t < 180 * 864e5) return { daily: c.d };
            const r = await fetch(`https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=1991-01-01&end_date=2020-12-31&daily=temperature_2m_max,temperature_2m_min&timezone=auto`);
            if (!r.ok) return c ? { daily: c.d } : null;
            const j = await r.json();
            if (!(j && j.daily && j.daily.time && j.daily.time.length)) return null;
            await idb.set(key, { t: Date.now(), d: j.daily });
            return j;
        }""")
_r("""                if (token === fetchToken) showToast("Error retrieving forecast data for this location. Please try again.");""",
   """                if (token === fetchToken) showToast(/429/.test(String(err && err.message)) ? "The free forecast service (Open-Meteo) has hit its request limit for now. Try again in a few minutes." : `Error retrieving forecast data for this location (${esc(String((err && err.message) || 'unknown error'))}). Please try again.`);""")

# ---- rest-of-day wording follows the timing: "Overcast this morning and afternoon, then rain this evening" ----
_r("""        function precipExpected(p, amtMm) {""", r"""        // Rest-of-today wording, period by period, using the same hourly rule as the hourly forecast's rain icons
        // (a wet weather code with at least a 30% chance or measurable rain), so the two always agree.
        function restOfDayPhrase() {
            if (!ensembleData || !ensembleData.hourly || !ensembleData.daily) return null;
            const h = ensembleData.hourly, d = ensembleData.daily, cur = hourlyStart();
            const first = h.time.findIndex(t => t.startsWith(d.time[0]));
            if (first < 0) return null;
            const ok = v => v !== null && v !== undefined && !isNaN(v);
            const segs = [['this morning', 0, 12], ['this afternoon', 12, 18], ['this evening', 18, 24]];
            const parts = [];
            segs.forEach(([label, a, b]) => {
                const s = Math.max(first + a, cur), e = first + b;
                if (e - s < 2) return;                       // less than two hours of it left
                let cl = [], day = 0, n = 0, wetH = 0, wpp = 0, sn = 0, code = 0, amt = 0;
                for (let j = s; j < e && j < h.time.length; j++) {
                    n++;
                    if (h.cloud_cover && ok(h.cloud_cover[j])) cl.push(h.cloud_cover[j]);
                    if (h.is_day && h.is_day[j]) day++;
                    const hp = h.precipitation_probability && ok(h.precipitation_probability[j]) ? h.precipitation_probability[j] : 0;
                    const ha = h.precipitation && ok(h.precipitation[j]) ? h.precipitation[j] : 0, hc = h.weather_code ? h.weather_code[j] : 0;
                    if (hc >= 51 && hc <= 99 && (hp >= 30 || (ha >= 0.1 && hp >= 20))) {
                        wetH++; wpp = Math.max(wpp, hp); amt += ha; code = Math.max(code, hc);
                        if (h.snowfall && ok(h.snowfall[j])) sn += h.snowfall[j];
                    }
                }
                const sky = skyCondition(cl.length ? cl.reduce((x, y) => x + y, 0) / cl.length : null, day >= n / 2).text.toLowerCase();
                let state = sky;
                if (wetH) {
                    const kind = code >= 95 ? 'thunderstorms' : sn >= 0.5 ? 'snow showers' : 'showers';
                    const widespread = wetH >= Math.max(2, n / 2);
                    if (wpp >= 80 && widespread) state = code >= 95 ? 'thunderstorms' : sn >= 0.5 ? 'snow' : 'rain';
                    else if (wpp >= 60) state = `${sky} with ${kind} likely`;
                    else state = `${sky} with a ${Math.round(wpp / 10) * 10}% chance of ${kind}`;
                }
                const last = parts[parts.length - 1];
                if (last && last.state === state) last.labels.push(label.replace('this ', ''));
                else parts.push({ state, labels: [label] });
            });
            if (!parts.length) return null;
            const cap = t => t[0].toUpperCase() + t.slice(1);
            if (parts.length === 1) return `${cap(parts[0].state)} for the rest of today`;
            const bits = parts.map(p => `${p.state} ${p.labels.length > 1 ? p.labels.slice(0, -1).join(', ') + ' and ' + p.labels.slice(-1) : p.labels[0]}`);
            return cap(bits.length > 2 ? bits.slice(0, -1).join(', ') + ', then ' + bits.slice(-1) : bits.join(', then '));
        }

        function precipExpected(p, amtMm) {""")

# hourly icons use the same wet-hour rule as the summary text
_r("let cond = (wetCode && (hp >= 30 || ha >= 0.1)", "let cond = (wetCode && (hp >= 30 || (ha >= 0.1 && hp >= 20))")

# ---- refresh button ----
_r("""        function useMyLocation() {""", """        let refreshing = false;
        async function refreshData() {
            if (refreshing) return;
            refreshing = true; document.body.classList.add('refreshing');
            try { await fetchForecastData(); } finally { refreshing = false; document.body.classList.remove('refreshing'); }
        }
        function useMyLocation() {""")

# ---- Model Analysis: one collapsed section replaces the comparison table + weights panel ----
out = out.replace("        function renderDomainWeightPanel() {", "        function _oldRenderDomainWeightPanel() {", 1)
out = out.replace("        function renderModelComparisonTable() {", "        function _oldRenderModelComparisonTable() {", 1)
_r("""        function esc(s) {""", open('/home/claude/model_analysis.js').read() + """
        function esc(s) {""")

# ---- forecast continuity: small changes held, moderate changes move halfway, big changes / new day apply fully ----
_r("""                applyRemainingToday();
                floorTodayHigh();""", """                applyRemainingToday();
                applyContinuity();
                floorTodayHigh();""")
_r("""        function floorTodayHigh() {""", r"""        // Forecast continuity. The last forecast shown for this place is remembered (in this browser) for 6 hours.
        // A fresh run that differs only a little keeps the earlier number; a moderate change moves halfway toward the
        // new value; a large change (new guidance or changing conditions) is taken as is. Observed rain right now
        // always updates today's precipitation immediately.
        let continuityInfo = null;
        function applyContinuity() {
            if (!bestBetResults || !bestBetResults.length || !currentLoc) return;
            const key = `skyline:fc:${(+currentLoc.lat).toFixed(2)},${(+currentLoc.lon).toFixed(2)}`;
            let prev = null;
            try { prev = JSON.parse(localStorage.getItem(key) || 'null'); } catch (e) {}
            const fresh = prev && prev.t && Date.now() - prev.t < 6 * 3600e3;
            // per field: [hold below, take fully at or above]  (°C, mm, %, km/h)
            const RULE = { bestMax: [0.6, 2.2], bestMin: [0.6, 2.2], bestPrecip: [0.8, 5], bestRain: [0.8, 5], bestSnow: [0.5, 3], precipProb: [8, 25], bestWind: [3, 15], bestGust: [4, 18] };
            let held = 0, halved = 0, taken = 0;
            if (fresh) {
                bestBetResults.forEach((b, i) => {
                    const p = prev.days && prev.days[b.date];
                    if (!p || p.rem !== !!b.remaining) return;          // compare like with like (rest-of-today vs full day)
                    Object.keys(RULE).forEach(k => {
                        const o = p[k], v = b[k];
                        if (o === null || o === undefined || v === null || v === undefined || isNaN(o) || isNaN(v)) return;
                        if (i === 0 && (k === 'bestPrecip' || k === 'bestRain' || k === 'bestSnow' || k === 'precipProb') && b.nowcast && b.nowcast.wet) return;
                        const [lo, hi] = RULE[k], d = v - o;
                        const rel = (k === 'bestPrecip' || k === 'bestRain' || k === 'bestSnow') ? Math.abs(d) / Math.max(o, v, 0.1) : 1;
                        if (Math.abs(d) < lo) { b[k] = o; held++; }
                        else if (Math.abs(d) >= hi && rel >= 0.5) { taken++; }
                        else { b[k] = o + d / 2; halved++; }
                    });
                    if (b.bestPrecip !== undefined && b.bestRain !== undefined && b.bestSnow !== undefined) b.bestRain = Math.min(b.bestRain, b.bestPrecip);
                });
            }
            continuityInfo = fresh ? { held, halved, taken, ageMin: Math.round((Date.now() - prev.t) / 60000) } : null;
            // remember what is shown now; keep the original timestamp while consecutive updates are being smoothed
            const days = {};
            bestBetResults.forEach(b => { const o = { rem: !!b.remaining }; Object.keys(RULE).forEach(k => { o[k] = b[k]; }); days[b.date] = o; });
            try { localStorage.setItem(key, JSON.stringify({ t: fresh && (held + halved) > 0 ? prev.t : Date.now(), days })); } catch (e) {}
        }

        function floorTodayHigh() {""")

# ---- SPC severe weather + winter weather in alerts and the discussion panel ----
_a = out.index('        // ---------- Month / year to date precipitation')
out = out[:_a] + open('/home/claude/spc.js').read() + '\n' + out[_a:]
_r("""                <div id="afdBody" class="hidden border-t border-slate-800 p-5">
                    <div id="afdText\"""", """                <div id="afdBody" class="hidden border-t border-slate-800 p-5">
                    <div id="spcSection" class="afd text-[13px] md:text-sm leading-relaxed text-slate-200"></div>
                    <div id="afdText\"""")
_r("""NWS Area Forecast Discussion <span id="afdOffice" class="text-xs font-mono text-slate-400 font-normal"></span>""",
   """NWS Area Forecast Discussion <span id="afdOffice" class="text-xs font-mono text-slate-400 font-normal"></span><span id="afdSpcBadge" class="flex gap-1"></span>""")
_r("""            if (afdOpen) loadAFD(); else document.getElementById('afdText').innerHTML = '';""",
   """            refreshSPC();
            if (afdOpen) loadAFD(); else document.getElementById('afdText').innerHTML = '';""")
_r("""            }));
            if (bestBetResults.length > 0) {""", """            }));
            alerts.push(...spcAlerts());
            if (bestBetResults.length > 0) {""")
_r("""                nwsAlerts = nws.alerts || [];
""", """                nwsAlerts = nws.alerts || [];
                spcData = null;
""")
_r("""                loadStationClimate(token, nws, lat, lon);
            } catch (err) {""", """                loadStationClimate(token, nws, lat, lon);
                if (nwsOffice) loadSPC(token, lat, lon);
            } catch (err) {""")
_r(""".afd .afd-rule { border: 0; border-top: 1px solid rgba(148,163,184,.25); margin: 14px 0; }""",
""".afd .afd-rule { border: 0; border-top: 1px solid rgba(148,163,184,.25); margin: 14px 0; }
.afd .afd-h.spc-h { color: #fca5a5; } .afd .afd-h.spc-hw { color: #a5d8ff; }
.spc-days { display: flex; flex-direction: column; gap: 6px; margin: 0 0 10px; }
.spc-row { display: flex; align-items: center; gap: 8px; }
.spc-chip { display: inline-block; min-width: 42px; text-align: center; padding: 1px 6px; border-radius: 6px; font: 700 10.5px/1.6 ui-monospace, Menlo, monospace; color: #0f172a; white-space: nowrap; }
.spc-det { margin: 0 0 8px; border: 1px solid rgba(148,163,184,.25); border-radius: 10px; background: rgba(15,23,42,.35); }
.spc-det > summary { cursor: pointer; padding: 8px 12px; display: flex; flex-wrap: wrap; gap: 4px 10px; align-items: baseline; font-weight: 600; color: #e2e8f0; }
.spc-det .spc-meta { font-weight: 400; font-size: 11px; color: #94a3b8; }
.spc-det .spc-body { padding: 4px 12px 10px; max-height: 26rem; overflow-y: auto; }""")

# ---- one rule for a wet hour (hourly icons, rest-of-day wording, hero amount); SPC thunder wording ----
_r("""        function restOfDayPhrase() {""", """        // A forecast hour is wet when the chance is 40%+ (whatever the deterministic code says), or the code is wet with 30%+
        // (20%+ with a measurable amount). Returns the weather code to show, or 0 when dry.
        function spcThunderAt(t) {
            const d1 = spcData && spcData.days && spcData.days[0];
            if (!d1 || !d1.cat) return false;
            const end = d1.valid ? d1.valid.getTime() + 24 * 36e5 : Date.now() + 18 * 36e5;
            return t < end;
        }
        function hourWetCode(j) {
            const h = ensembleData && ensembleData.hourly;
            if (!h) return 0;
            const hp = h.precipitation_probability && h.precipitation_probability[j] != null ? h.precipitation_probability[j] : 0;
            const ha = h.precipitation && h.precipitation[j] != null ? h.precipitation[j] : 0, hc = h.weather_code ? h.weather_code[j] || 0 : 0;
            const wetCode = hc >= 51 && hc <= 99;
            if (!((wetCode && (hp >= 30 || (ha >= 0.1 && hp >= 20))) || hp >= 40)) return 0;
            const tC = h.temperature_2m ? h.temperature_2m[j] : null, snowy = (h.snowfall && h.snowfall[j] > 0) || (tC != null && tC <= 0.5);
            let code = wetCode ? hc : snowy ? 85 : 80;
            if (code < 95 && !snowy && (code >= 80 || !wetCode) && spcThunderAt(new Date(h.time[j]).getTime())) code = 95;
            return code;
        }
        function restOfDayPhrase() {""")
_r("""                    if (hc >= 51 && hc <= 99 && (hp >= 30 || (ha >= 0.1 && hp >= 20))) {
                        wetH++; wpp = Math.max(wpp, hp); amt += ha; code = Math.max(code, hc);""", """                    const wc = hourWetCode(j);
                    if (wc) {
                        wetH++; wpp = Math.max(wpp, hp); amt += ha; code = Math.max(code, wc);""")
_r("""                    const kind = code >= 95 ? 'thunderstorms' : sn >= 0.5 ? 'snow showers' : 'showers';""",
   """                    const kind = code >= 95 ? (spcThunderAt(Date.now()) && wpp < 80 ? 'showers and thunderstorms' : 'thunderstorms') : sn >= 0.5 ? 'snow showers' : 'showers';""")
_r("""                const wetCode = hc >= 51 && hc <= 99;
                let cond = (wetCode && (hp >= 30 || (ha >= 0.1 && hp >= 20)) || hc === 45 || hc === 48) ? getWeatherCondition(hc, isDay)""",
   """                const wc = hourWetCode(j);
                let cond = wc ? getWeatherCondition(wc, isDay) : (hc === 45 || hc === 48) ? getWeatherCondition(hc, isDay)""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/outlook.js').read() + '\n' + out[_a:]
_r("""            const d1 = spcData && spcData.days && spcData.days[0];
            if (!d1 || !d1.cat) return false;
            const end = d1.valid ? d1.valid.getTime() + 24 * 36e5 : Date.now() + 18 * 36e5;
            return t < end;""", """            if (!spcData || !spcData.days) return false;
            return spcData.days.some(d => {
                if (!d.cat) return false;
                if (!d.valid) return d.day === 1 && t < Date.now() + 18 * 36e5;
                const st = d.valid.getTime();
                return t >= st - 6 * 36e5 && t < st + 24 * 36e5;
            });""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        function _oldToggleQuickView() {
            const b = document.getElementById('quickBody'), open = b.classList.toggle('hidden') === false;
            document.getElementById('quickChevron').style.transform = open ? 'rotate(180deg)' : '';
            document.getElementById('quickToggle').setAttribute('aria-expanded', open);
        }
""" + out[_a:]
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        // alerts: very top of the page on phones and tablets, top of the main panel on computers
        function placeAlerts() {
            const a = document.getElementById('alertsContainer');
            const slot = document.getElementById(window.matchMedia('(min-width: 1024px)').matches ? 'heroAlertSlot' : 'topAlertSlot');
            if (a && slot && a.parentElement !== slot) slot.appendChild(a);
        }
        placeAlerts();
        try { window.matchMedia('(min-width: 1024px)').addEventListener('change', placeAlerts); } catch (e) { window.addEventListener('resize', placeAlerts); }
""" + out[_a:]
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        // record trophy: click to see what the record is
        function recPop(btn, ev) {
            if (ev) ev.stopPropagation();
            const old = document.querySelector('.rec-pop'), same = old && old._for === btn;
            if (old) old.remove();
            if (same) return;
            const d = document.createElement('div');
            d.className = 'rec-pop'; d.textContent = btn.dataset.info || ''; d._for = btn;
            document.body.appendChild(d);
            const r = btn.getBoundingClientRect(), w = d.offsetWidth, h = d.offsetHeight;
            d.style.left = Math.max(8, Math.min(window.innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + 'px';
            d.style.top = (r.top - h - 8 > 8 ? r.top - h - 8 : r.bottom + 8) + 'px';
        }
        document.addEventListener('click', () => { const o = document.querySelector('.rec-pop'); if (o) o.remove(); });
        window.addEventListener('scroll', () => { const o = document.querySelector('.rec-pop'); if (o) o.remove(); }, { passive: true });
""" + out[_a:]
_r("""        function toggleAFD() {""", """        function _oldToggleAFD() {""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/sections.js').read() + out[_a:]
# initialise once the page markup exists (script runs after the body)
_r(""".rec-btn { background: none;""", """.sec-card { border: 1px solid rgba(255,255,255,.09) !important; border-radius: 18px !important; padding: 18px 22px !important; background: rgba(15,23,42,.5) !important; overflow: hidden; }
.sec-head { display: flex !important; align-items: center !important; flex-wrap: wrap; gap: 6px 12px; cursor: pointer; user-select: none; padding: 0 !important; margin: 0 0 12px !important; border: 0 !important; background: none !important; width: 100%; text-align: left; }
.sec-head { flex-direction: row !important; justify-content: flex-start !important; text-align: left !important; }
.sec-head .sec-tw { flex: 1 1 auto; min-width: 0; text-align: left !important; align-items: flex-start; }
.sec-head .sec-title { justify-content: flex-start !important; text-align: left !important; }
.sec-card.collapsed > .sec-head { flex-wrap: nowrap !important; }
.sec-head:hover .sec-chev, .sec-head:focus-visible .sec-chev { color: #f1f5f9; }
.sec-head:focus-visible { outline: 2px solid rgba(125,211,252,.5); outline-offset: 4px; border-radius: 8px; }
.sec-title { font-family: 'Outfit', system-ui, sans-serif !important; font-size: 16px !important; font-weight: 700 !important; color: #f1f5f9 !important; letter-spacing: 0 !important; line-height: 1.3 !important; margin: 0 !important; display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; }
.sec-title > i:first-child { color: #7dd3fc !important; width: 18px; text-align: center; }
.sec-chev { margin-left: auto; color: #94a3b8; font-size: 13px; transition: transform .2s; }
.sec-card:not(.collapsed) > .sec-head .sec-chev { transform: rotate(180deg); }
.sec-card.collapsed > :not(.sec-head):not(#_) { display: none !important; }
.sec-card.collapsed > .sec-head { margin-bottom: 0 !important; }
.sec-card.collapsed .sec-x:not(#_) { display: none !important; }
.sec-card > #afdBody, .sec-card > #maBody { padding: 14px 0 0 !important; border-top: 1px solid rgba(255,255,255,.08) !important; }
.sec-card > #quickBody { margin-top: 0 !important; }
.rec-btn { background: none;""")
_r("""            grid.innerHTML = tiles.map(([ic, col, label, val, sub], i) => {
                const r = recFor(keys[i]);
                const ring = r ? (r.kind === 'high' ? 'border-rose-400/70 ring-1 ring-rose-400/40' : r.kind === 'low' ? 'border-sky-400/70 ring-1 ring-sky-400/40' : 'border-indigo-400/70 ring-1 ring-indigo-400/40') : 'border-slate-800';
                return `
                <div class="bg-slate-900/70 border ${ring} rounded-xl p-4">
                    <div class="text-[11px] text-slate-400 font-medium"><i class="fa-solid ${ic} ${col} mr-1"></i>${label}</div>
                    <div class="text-2xl font-bold text-slate-100 mt-1 font-mono">${val}</div>
                    <div class="text-[10px] text-slate-400 font-mono mt-1 leading-snug">${esc(sub)}</div>
                    ${r ? recordBadge(r) : ''}
                </div>`;
            }).join('');""", """            // peak wind so far today (station observations; gusts when reported)
            {
                const tz = ensembleData.timezone, d0 = ensembleData.daily.time[0];
                const clock = ts => new Date(ts).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', timeZone: tz });
                let g = null, gt = null, w = null, wt = null;
                (nwsObsToday || []).forEach(o => {
                    if (!o || !o.timestamp || new Date(o.timestamp).toLocaleDateString('en-CA', { timeZone: tz }) !== d0) return;
                    const gv = o.windGust && o.windGust.value, wv = o.windSpeed && o.windSpeed.value;
                    if (n(gv) && (g === null || gv > g)) { g = gv; gt = o.timestamp; }
                    if (n(wv) && (w === null || wv > w)) { w = wv; wt = o.timestamp; }
                });
                const stn = (nwsObs && nwsObs.stationId) || '';
                if (g !== null) tiles.push(['fa-wind', 'text-teal-300', 'Peak gust', formatSpeed(g), `at ${clock(gt)}${stn ? ', ' + stn : ''}`]);
                else if (w !== null) tiles.push(['fa-wind', 'text-teal-300', 'Peak wind', formatSpeed(w), `at ${clock(wt)}${stn ? ', ' + stn : ''}, no gusts`]);
                else tiles.push(['fa-wind', 'text-teal-300', 'Peak gust', '--', 'No station wind reports']);
            }
            const short = { 'High So Far': 'High', 'Low So Far': 'Low', 'Precipitation So Far': 'Precipitation' };
            grid.innerHTML = tiles.map(([ic, col, label, val, sub], i) => {
                const r = keys[i] ? recFor(keys[i]) : null;
                const ring = r ? (r.kind === 'high' ? 'rec-hi' : r.kind === 'low' ? 'rec-lo' : 'rec-pr') : '';
                return `<div class="${ring}"><div class="mlabel"><i class="fa-solid ${ic} ${col}"></i> ${short[label] || label}</div><div class="mval">${val}</div><div class="msub">${esc(sub)}</div>${r ? recordBadge(r) : ''}</div>`;
            }).join('');""")
_r(""".rec-btn { background: none;""", """.metric-strip > .rec-hi { border-color: rgba(251,113,133,.7); box-shadow: 0 0 0 1px rgba(251,113,133,.35); }
.metric-strip > .rec-lo { border-color: rgba(56,189,248,.7); box-shadow: 0 0 0 1px rgba(56,189,248,.35); }
.metric-strip > .rec-pr { border-color: rgba(129,140,248,.7); box-shadow: 0 0 0 1px rgba(129,140,248,.35); }
.rec-btn { background: none;""")
_r("""document.getElementById('todaySoFarSource').innerText = `${d} · midnight to now (${tz})`;""", """document.getElementById('todaySoFarSource').innerText = `${d}, since midnight`;""")

# ---- hero layout adapts to how many alerts there are ----
_r("""                        <p class="leading-relaxed opacity-90">${esc(a.text.slice(0, 320))}</p>
                    </div>`).join('');""", """                        <p class="leading-relaxed opacity-90">${esc(a.text.slice(0, 320))}</p>
                    </div>`).join('');
            heroAlertCount = alerts.length;
            try { layoutHeroAlerts(); } catch (e) {}""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        // none: a small 'no alerts' pill, conditions and today-so-far sit beside the temperature (3 columns on wide screens)
        // few:  alerts fill the space beside the temperature
        // many: alerts get a full-width row above (cards two across), the rest sits below in one row
        let heroAlertCount = 0;
        function layoutHeroAlerts() {
            const g = document.querySelector('.hero-grid'), box = document.getElementById('alertsContainer'), pill = document.getElementById('alertPill');
            if (!g || !box) return;
            const n = heroAlertCount, wide = window.matchMedia('(min-width: 1024px)').matches;
            g.classList.remove('al-none', 'al-few', 'al-many');
            box.classList.toggle('hidden', n === 0);
            if (pill) pill.classList.toggle('hidden', n !== 0);
            if (n === 0) { g.classList.add('al-none'); return; }
            if (!wide) { g.classList.add('al-few'); return; }
            g.classList.add('al-few');
            const main = g.querySelector('.hero-main');
            const tooTall = n >= 3 || (main && box.scrollHeight > main.offsetHeight + 90);
            if (tooTall) { g.classList.remove('al-few'); g.classList.add('al-many'); }
        }
        window.addEventListener('resize', () => { try { layoutHeroAlerts(); } catch (e) {} });
""" + out[_a:]
# ---- a new location starts at the top of the page ----
_r("""        async function fetchForecastData() {
            const token = ++fetchToken;""", """        let lastLocKey = null;
        try { if ('scrollRestoration' in history) history.scrollRestoration = 'manual'; } catch (e) {}
        async function fetchForecastData() {
            const token = ++fetchToken;
            {
                const k = currentLoc && currentLoc.lat != null ? `${(+currentLoc.lat).toFixed(3)},${(+currentLoc.lon).toFixed(3)}` : null;
                if (k !== lastLocKey) { if (lastLocKey !== null || window.scrollY > 0) window.scrollTo({ top: 0, behavior: lastLocKey === null ? 'auto' : 'smooth' }); lastLocKey = k; }
            }""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        function toggleDcTable() {
            const w = document.getElementById('dcTableWrap'), b = document.getElementById('dcTableToggle');
            const open = w.classList.toggle('hidden') === false;
            b.setAttribute('aria-expanded', String(open)); b.classList.toggle('open', open);
            document.getElementById('dcTableHint').innerText = open ? 'Hide table' : 'Show table';
        }
""" + out[_a:]
_r(""".rec-btn { background: none;""", """.dc-tt { width: 100%; display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 12px; background: rgba(8,16,34,.34); border: 1px solid rgba(255,255,255,.1); text-align: left; cursor: pointer; }
.dc-tt:hover { border-color: rgba(125,211,252,.4); }
.dc-tt .dc-tt-chev { transition: transform .2s; } .dc-tt.open .dc-tt-chev { transform: rotate(180deg); }
.rec-btn { background: none;""")
# ---- observation history: when the NWS feed returns little or nothing, fill from IEM's ASOS archive for the same station ----
_r("""                                const t = await (await fetch(`https://api.weather.gov/stations/${out.obs.stationId}/observations?start=${since}&limit=500`)).json();
                                out.obsToday = (t.features || []).map(f => f.properties);
                            } catch (e) {}""", """                                const t = await (await fetch(`https://api.weather.gov/stations/${out.obs.stationId}/observations?start=${since}&limit=500`)).json();
                                out.obsToday = (t.features || []).map(f => f.properties);
                            } catch (e) {}
                            try {
                                const recent = out.obsToday.filter(o => o && o.timestamp && o.temperature && o.temperature.value != null && Date.now() - new Date(o.timestamp) < 24 * 3600e3).length;
                                const sid = out.obs.stationId || '', st = out.state;
                                if (recent < 8 && st && /^K[A-Z0-9]{3}$/.test(sid)) {
                                    const day = n => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
                                    const get = d => fetch(`https://mesonet.agron.iastate.edu/api/1/obhistory.json?station=${sid.slice(1)}&network=${st}_ASOS&date=${d}&full=1`)
                                        .then(r => r.ok ? r.json() : { data: [] }).then(j => Array.isArray(j.data) ? j.data : []).catch(() => []);
                                    const rows = (await Promise.all([day(2), day(1), day(0), day(-1)].map(get))).flat();
                                    const iem = rows.map(iemToObs).filter(o => o.timestamp && o.temperature.value !== null).map(o => { delete o.intl; return o; });
                                    const have = new Set(out.obsToday.filter(o => o && o.timestamp).map(o => Math.round(new Date(o.timestamp) / 120000)));
                                    const add = iem.filter(o => !have.has(Math.round(new Date(o.timestamp) / 120000)));
                                    if (add.length) out.obsToday = [...out.obsToday, ...add].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                                }
                            } catch (e) {}""")
# ---- climate station must represent the location: reject a climate site more than 300 m higher or lower ----
_r("""        function nearestCliSite(lat, lon, obsIcao) {""", """        // terrain elevation (m) for points, from Open-Meteo's 90 m DEM; cached per point
        async function ptElev(pts) {
            const keys = pts.map(([a, b]) => `elev1:${(+a).toFixed(3)},${(+b).toFixed(3)}`);
            const out = await Promise.all(keys.map(k => idb.get(k).catch(() => null)));
            const miss = pts.map((p, i) => out[i] == null ? i : -1).filter(i => i >= 0);
            if (miss.length) {
                const r = await fetch(`https://api.open-meteo.com/v1/elevation?latitude=${miss.map(i => (+pts[i][0]).toFixed(4)).join(',')}&longitude=${miss.map(i => (+pts[i][1]).toFixed(4)).join(',')}`);
                if (!r.ok) throw new Error('elevation HTTP ' + r.status);
                const j = await r.json();
                miss.forEach((i, n) => { const v = j.elevation && j.elevation[n]; if (v != null && isFinite(v)) { out[i] = v; idb.set(keys[i], v).catch(() => {}); } });
            }
            return out;
        }
        async function representative(lat, lon, sLat, sLon) {
            try { const [a, b] = await ptElev([[lat, lon], [sLat, sLon]]); return a == null || b == null || Math.abs(a - b) <= 300; }
            catch (e) { return true; }
        }
        function nearestCliSite(lat, lon, obsIcao) {
            return _nearestCliSite(lat, lon, obsIcao).then(async s => (s && !(await representative(lat, lon, s.lat, s.lon))) ? null : s);
        }
        function _nearestCliSite(lat, lon, obsIcao) {""")
_r("""                            const r = await fetch(`${ACIS}/StnMeta?bbox=${bb}&elems=pcpn&sdate=${sd}&edate=${e}&meta=name,sids,state,ll&output=json`);
                            if (!r.ok) continue;
                            const j = await r.json();
                            const cands = (j.meta || []).map(parseAcisMeta).filter(m => m.ghcn && m.lat != null)""", """                            const r = await fetch(`${ACIS}/StnMeta?bbox=${bb}&elems=pcpn&sdate=${sd}&edate=${e}&meta=name,sids,state,ll,elev&output=json`);
                            if (!r.ok) continue;
                            const j = await r.json();
                            let locE = null; try { locE = (await ptElev([[lat, lon]]))[0]; } catch (e2) {}
                            const cands = (j.meta || []).map(m => ({ ...parseAcisMeta(m), elevM: m.elev != null && isFinite(+m.elev) ? +m.elev * 0.3048 : null }))
                                .filter(m => m.ghcn && m.lat != null && (locE == null || m.elevM == null || Math.abs(m.elevM - locE) <= 300))""")
_r("""                const key = `climstn2:${k}`;""", """                const key = `climstn3:${k}`;""")
_r("""                live.forEach(s => { const km = distKm(+lat, +lon, s.lat, s.lon); if (km <= 75 && (!best || km < best.km)) best = { ...s, km }; });""",
   """                live.forEach(s => { const km = distKm(+lat, +lon, s.lat, s.lon); if (km <= 40 && (!best || km < best.km)) best = { ...s, km }; });""")
_r("""                const site = await nearestCliSite(lat, lon, obsIcao);
                const icao = site ? site.id : obsIcao;""", """                const site = await nearestCliSite(lat, lon, obsIcao);
                const icao = site ? site.id : null;   // no representative climate-report site: find the nearest long-record gauge at a similar elevation""")
_r("""                const key = `climstn3:${k}`;""", """                const key = `climstn4:${k}`;""")
_r("""                const icao = site ? site.id : null;   // no representative climate-report site: find the nearest long-record gauge at a similar elevation""",
   """                const icao = site ? site.id : obsIcao;   // no representative climate-report site: use the observing station shown at the top""")
_r("""                const key = `climstn4:${k}`;""", """                const key = `climstn5:${k}`;""")
_r("""            const est = await fetchPrecipEstimates(lat, lon, today);""", """            // the observing airport's own daily precipitation (IEM summaries of its reports)
            try {
                const sid = nws && nws.obs && nws.obs.stationId, st = nws && nws.state;
                const rows = await iemDailyObs(+today.slice(0, 4), null, sid, st);
                const daily = {};
                (rows || []).forEach(o => { if (o.valid >= yStart && o.valid <= yest && o.precip !== 'M') daily[o.valid] = o.precip === 'T' ? 0 : parseFloat(o.precip) * 25.4; });
                const n = Object.keys(daily).length, need = Math.round((new Date(yest) - new Date(yStart)) / 864e5) + 1;
                if (n >= Math.max(1, need * 0.8)) return { daily, yStart, errors: [], sources: ['station'], failed: false, gauge: { label: sid, name: (nws.obs && nws.obs.stationName) || sid, km: null, filled: 0 } };
            } catch (e) {}
            const est = await fetchPrecipEstimates(lat, lon, today);""")
# ---- climate station override + trust rule ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/climstations.js').read() + out[_a:]
_r("""            if (!climStnPromises[k]) climStnPromises[k] = (async () => {
                const site = await nearestCliSite(lat, lon, obsIcao);""", """            { const ov = climOverride(lat, lon); if (ov) return Promise.resolve(ov); }
            if (!climStnPromises[k]) climStnPromises[k] = (async () => {
                const site = await nearestCliSite(lat, lon, obsIcao);""")
_r("""        async function fetchCLI(nws, today, lat, lon) {""", """        async function fetchCLI(nws, today, lat, lon) {
            if (lat != null && climOverride(lat, lon)) return null;   // the user picked a station: its own record is used""")
_r("""            const key = `stnclim3:${icao}`;""", """            const ovS = climOverride(lat, lon);
            const key = `stnclim4:${icao}:${ovS ? ovS.ids[0] : 'auto'}`;""")
_r("""            const st = rawHistoricalStatsForDate(targetDateStr);
            if (!st) return st;""", """            const st = rawHistoricalStatsForDate(targetDateStr);
            if (!st) return st;
            if (!climTrusted()) return Object.assign({}, st, { normMax: null, normMin: null, recHigh: null, recHighYr: '', recLow: null, recLowYr: '' });""")
_r(""".rec-btn { background: none;""", """.dc-near { font-size: 11px; color: #7dd3fc; border: 1px solid rgba(125,211,252,.35); border-radius: 999px; padding: 2px 10px; background: rgba(125,211,252,.08); }
.dc-near:hover { background: rgba(125,211,252,.16); }
.dc-stns { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px; }
.dc-stns.hidden { display: none; }
.dc-stn { display: flex; flex-direction: column; gap: 2px; text-align: left; padding: 10px 12px; border-radius: 12px; background: rgba(8,16,34,.34); border: 1px solid rgba(255,255,255,.1); font-size: 13px; }
.dc-stn:hover { border-color: rgba(125,211,252,.45); } .dc-stn.on { border-color: rgba(125,211,252,.8); box-shadow: 0 0 0 1px rgba(125,211,252,.4); }
.rec-btn { background: none;""")
# ---- NWS heat index / wind chill ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        // NWS formulas. Heat index: Rothfusz regression with the NWS adjustments (simple Steadman form when the result is below 80 F),
        // reported when the temperature is 80 F or higher. Wind chill: 2001 NWS formula, temperature 50 F or lower and wind above 3 mph.
        function nwsFeels(tC, rh, windKmh) {
            if (tC == null || isNaN(tC)) return null;
            const T = tC * 9 / 5 + 32;
            if (T >= 80 && rh != null && !isNaN(rh)) {
                const R = rh;
                let hi = 0.5 * (T + 61 + (T - 68) * 1.2 + R * 0.094);
                if ((hi + T) / 2 >= 80) {
                    hi = -42.379 + 2.04901523 * T + 10.14333127 * R - 0.22475541 * T * R - 0.00683783 * T * T - 0.05481717 * R * R
                        + 0.00122874 * T * T * R + 0.00085282 * T * R * R - 0.00000199 * T * T * R * R;
                    if (R < 13 && T >= 80 && T <= 112) hi -= ((13 - R) / 4) * Math.sqrt((17 - Math.abs(T - 95)) / 17);
                    else if (R > 85 && T >= 80 && T <= 87) hi += ((R - 85) / 10) * ((87 - T) / 5);
                }
                return { kind: 'Heat index', c: (hi - 32) * 5 / 9 };
            }
            const V = windKmh != null && !isNaN(windKmh) ? windKmh * 0.621371 : null;
            if (T <= 50 && V != null && V > 3) {
                const wc = 35.74 + 0.6215 * T - 35.75 * Math.pow(V, 0.16) + 0.4275 * T * Math.pow(V, 0.16);
                return { kind: 'Wind chill', c: (Math.min(wc, T) - 32) * 5 / 9 };
            }
            return null;
        }
""" + out[_a:]
_r("""                $('currentApparentTemp').innerText = formatTemp(cc.apparent);""", """                { const fx = nwsFeels(cc.temp, cc.rh, cc.wind);
                  $('feelsLine').style.display = fx ? '' : 'none';
                  if (fx) { $('feelsLbl').innerText = fx.kind; $('currentApparentTemp').innerText = formatTemp(fx.c); } }""")
_r("""['fa-temperature-half', 'text-rose-400', 'Temperature', formatTemp(cc.temp, 1), `Feels like ${formatTemp(cc.apparent, 1)}`],""", """['fa-temperature-half', 'text-rose-400', 'Temperature', formatTemp(cc.temp, 1), (fx => fx ? `${fx.kind} ${formatTemp(fx.c, 1)}` : '')(nwsFeels(cc.temp, cc.rh, cc.wind))],""")
# ---- precip chance chart: show 0% hours, and say so when the whole day is dry ----
_r("""                        y: { min: 0, max: 100, grid: { color: 'rgba(255, 255, 255, 0.07)' }, ticks: { color: '#c7d2fe', font: { size: 12, weight: '600' }, stepSize: 25, callback: v => v + '%' } }
                    }
                }
            });""", """                        y: { min: 0, max: 100, grid: { color: 'rgba(255, 255, 255, 0.07)' }, ticks: { color: '#c7d2fe', font: { size: 12, weight: '600' }, stepSize: 25, callback: v => v + '%' } }
                    }
                },
                plugins: [{ id: 'zeroPrecip', afterDatasetsDraw(ch) {
                    if (!ch.getDatasetMeta || !ch.scales || !ch.scales.y) return;
                    const g = ch.ctx, meta = ch.getDatasetMeta(0), y0 = ch.scales.y.getPixelForValue(0), { left, right, top, bottom } = ch.chartArea;
                    g.save();
                    // a short dash on the baseline marks each 0% hour
                    g.fillStyle = 'rgba(199,210,254,.55)';
                    meta.data.forEach((bar, i) => { if (!(precipProbs[i] > 0)) { const w = Math.max(4, (bar.width || 8) * 0.7); g.fillRect(bar.x - w / 2, y0 - 2, w, 2); } });
                    if (!precipProbs.some(v => v > 0)) {
                        const cx = (left + right) / 2, cy = top + (bottom - top) * 0.42;
                        g.textAlign = 'center'; g.textBaseline = 'middle';
                        g.fillStyle = 'rgba(15,23,42,.55)';
                        const msg = '0% chance of precipitation', sub = 'every hour for the next 24 hours';
                        g.font = "600 14px Outfit, system-ui, sans-serif"; const w1 = g.measureText(msg).width;
                        g.font = "500 11.5px Outfit, system-ui, sans-serif"; const w2 = g.measureText(sub).width;
                        const bw = Math.max(w1, w2) + 28, bh = 50;
                        if (g.roundRect) { g.beginPath(); g.roundRect(cx - bw / 2, cy - bh / 2, bw, bh, 12); g.fill(); } else g.fillRect(cx - bw / 2, cy - bh / 2, bw, bh);
                        g.fillStyle = '#e0e7ff'; g.font = "600 14px Outfit, system-ui, sans-serif"; g.fillText(msg, cx, cy - 9);
                        g.fillStyle = '#a5b4fc'; g.font = "500 11.5px Outfit, system-ui, sans-serif"; g.fillText(sub, cx, cy + 11);
                    }
                    g.restore();
                } }]
            });""")
# ---- alerts collapse to a one-line bar with chips; click to open ----
_r("""            heroAlertCount = alerts.length;""", """            heroAlertCount = alerts.length;
            heroAlertItems = alerts.map(a => ({ type: a.type, title: a.title }));
            try { alertBar(); } catch (e) {}""")
_r("""        let heroAlertCount = 0;""", """        let heroAlertCount = 0, heroAlertItems = [], alertsOpen = false;
        function alertBar() {
            const box = document.getElementById('alertsContainer'), head = document.getElementById('alertsHeader');
            if (!box || !head) return;
            box.classList.toggle('al-open', alertsOpen);
            if (!head._bar) {
                head._bar = true;
                head.classList.add('al-head');
                head.setAttribute('role', 'button'); head.tabIndex = 0;
                const chips = document.createElement('div'); chips.id = 'alertChips'; chips.className = 'al-chips';
                head.insertBefore(chips, head.lastElementChild);
                const chev = document.createElement('i'); chev.className = 'fa-solid fa-chevron-down al-chev'; head.appendChild(chev);
                const tg = () => { alertsOpen = !alertsOpen; alertBar(); try { layoutHeroAlerts(); } catch (e) {} };
                head.addEventListener('click', tg);
                head.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tg(); } });
            }
            const chips = document.getElementById('alertChips');
            if (chips) chips.innerHTML = alertsOpen ? '' : heroAlertItems.map(a => `<span class="al-chip ${a.type === 'danger' ? 'al-d' : 'al-w'}">${esc(a.title)}</span>`).join('');
            head.setAttribute('aria-expanded', String(alertsOpen));
        }""")
_r("""            const tooTall = n >= 3 || (main && box.scrollHeight > main.offsetHeight + 90);""", """            const tooTall = !alertsOpen || n >= 3 || (main && box.scrollHeight > main.offsetHeight + 90);""")
_r(""".rec-btn { background: none;""", """#alertsContainer .al-head { cursor: pointer; user-select: none; flex-wrap: wrap; gap: 6px 10px; }
#alertsContainer:not(.al-open) .al-head { border-bottom: 0 !important; padding-bottom: 0 !important; margin-bottom: 0 !important; }
#alertsContainer:not(.al-open) #alertsList { display: none !important; }
#alertsContainer:not(.al-open) { padding-top: 12px !important; padding-bottom: 12px !important; }
.al-chips { display: flex; flex-wrap: wrap; gap: 6px; flex: 1 1 auto; min-width: 0; }
.al-chip { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 999px; white-space: nowrap; max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.al-chip.al-d { background: rgba(244,63,94,.18); border: 1px solid rgba(251,113,133,.55); color: #fecdd3; }
.al-chip.al-w { background: rgba(245,158,11,.15); border: 1px solid rgba(251,191,36,.5); color: #fde68a; }
.al-chev { color: #94a3b8; font-size: 12px; transition: transform .2s; } .al-open .al-chev { transform: rotate(180deg); }
#alertsList > :last-child:nth-child(odd) { }
@media (min-width: 1024px) { .hero-grid.al-many #alertsList > :last-child:nth-child(odd) { grid-column: 1 / -1; justify-self: center; width: calc(50% - 4px); } }
.rec-btn { background: none;""")
# ---- links from alerts to their discussions ----
_r("""                title: a.event, tag: 'NWS Official',
                text: (a.headline || '') + (a.areaDesc ? ` — ${a.areaDesc}` : '')
            }));""", """                title: a.event, tag: 'NWS Official',
                text: (a.headline || '') + (a.areaDesc ? ` — ${a.areaDesc}` : ''),
                full: [a.description, a.instruction].filter(Boolean).join('\\n\\n'),
                links: (() => {
                    const L = [];
                    const vt = (a.parameters && Array.isArray(a.parameters.VTEC) ? a.parameters.VTEC : []).join(' ');
                    const w = vt.match(/\\.(SV|TO)\\.A\\.(\\d{4})\\./);
                    if (w) L.push({ label: `SPC watch ${+w[2]}`, href: `https://www.spc.noaa.gov/products/watch/ww${w[2]}.html` });
                    if (nwsOffice) L.push({ label: 'Area forecast discussion', fn: 'openAFDPanel()' });
                    if (/thunder|tornado|severe/i.test(a.event || '')) L.push({ label: 'Severe weather discussion', fn: 'openSevere()' });
                    return L;
                })()
            }));""")
_r("""                        <p class="leading-relaxed opacity-90">${esc(a.text.slice(0, 320))}</p>
                    </div>`).join('');""", """                        <p class="leading-relaxed opacity-90">${esc(a.text.slice(0, 320))}</p>
                        ${a.full ? `<details class="al-more"><summary>Full alert text</summary><div class="al-full">${esc(a.full)}</div></details>` : ''}
                        ${a.links && a.links.length ? `<div class="al-links">${a.links.map(l => l.href ? `<a href="${l.href}" target="_blank" rel="noopener">${esc(l.label)} <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i></a>` : `<button type="button" onclick="${l.fn}">${esc(l.label)} <i class="fa-solid fa-arrow-down text-[9px]"></i></button>`).join('')}</div>` : ''}
                    </div>`).join('');""")
_r(""".rec-btn { background: none;""", """.al-links { display: flex; flex-wrap: wrap; gap: 6px 14px; margin-top: 8px; }
.al-links a, .al-links button { font-size: 11.5px; font-weight: 600; color: #bae6fd; text-decoration: underline; text-underline-offset: 2px; background: none; border: 0; padding: 0; cursor: pointer; }
.al-links a:hover, .al-links button:hover { color: #fff; }
.al-more { margin-top: 6px; } .al-more > summary { cursor: pointer; font-size: 11.5px; font-weight: 600; color: #e2e8f0; opacity: .85; }
.al-full { margin-top: 6px; white-space: pre-wrap; font-size: 11.5px; line-height: 1.5; color: #e2e8f0; max-height: 18rem; overflow-y: auto; }
.rec-btn { background: none;""")
_r("""            document.getElementById('obsMetar').innerHTML = cc.metar
                ? `<div class="mt-3 text-[11px] font-mono text-slate-300 bg-slate-950/60 border border-slate-800 rounded-lg p-2 break-all"><span class="text-slate-500 mr-1">METAR</span>${esc(cc.metar)}</div>` : '';""", """            document.getElementById('obsMetar').innerHTML = '';   // raw METAR not shown""")
# ---- thunderstorm chance (NWS gridded probabilityOfThunder) ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/thunder.js').read() + out[_a:]
_r("""                    fetch(props.forecast).then(r => r.ok ? r.json() : null).then(j => { out.forecast = j; }).catch(() => {}),""",
   """                    fetch(props.forecast).then(r => r.ok ? r.json() : null).then(j => { out.forecast = j; }).catch(() => {}),
                    (props.forecastGridData ? fetch(props.forecastGridData).then(r => r.ok ? r.json() : null).then(j => { const P = j && j.properties; out.thunder = parseNwsSeries(P && P.probabilityOfThunder); out.pop = parseNwsSeries(P && P.probabilityOfPrecipitation); out.sky = parseNwsSeries(P && P.skyCover); }).catch(() => {}) : Promise.resolve()),""")
_r("""                nwsAlerts = nws.alerts || [];
                spcData = null;""", """                nwsAlerts = nws.alerts || [];
                nwsThunder = nws.thunder || null;
                spcData = null;""")
_r("""                floorTodayHigh();
                renderDashboard();""", """                floorTodayHigh();
                try { annotateThunder(); } catch (e) {}
                try { raiseTodayHigh(); } catch (e) {}
                renderDashboard();""")
# hourly wet rule: thunder 40%+ means a thunderstorm hour
_r("""            if (!((wetCode && (hp >= 30 || (ha >= 0.1 && hp >= 20))) || hp >= 40)) return 0;""", """            const th = thunderAt(j);
            if (th != null && th >= 40) return 95;
            if (!((wetCode && (hp >= 30 || (ha >= 0.1 && hp >= 20))) || hp >= 40)) return 0;""")
_r("""            let code = wetCode ? hc : snowy ? 85 : 80;
            if (code < 95 && !snowy && (code >= 80 || !wetCode) && spcThunderAt(new Date(h.time[j]).getTime())) code = 95;""",
   """            let code = wetCode ? hc : snowy ? 85 : 80;
            if (code < 95 && !snowy && (code >= 80 || !wetCode) && (th != null ? th >= 20 : spcThunderAt(new Date(h.time[j]).getTime()))) code = 95;""")
# hourly tiles: thunder chance under the precip chance
_r("""                        <span class="text-[10px] font-mono mt-1 ${pp >= 10 ? 'text-blue-300' : 'text-transparent'}"><i class="fa-solid fa-droplet"></i> ${pp !== null ? pp : 0}%</span>
                    </div>`;""", """                        <span class="text-[10px] font-mono mt-1 ${pp >= 10 ? 'text-blue-300' : 'text-transparent'}"><i class="fa-solid fa-droplet"></i> ${pp !== null ? pp : 0}%</span>
                        ${(t => t != null && t >= 15 ? `<span class="text-[10px] font-mono text-amber-300"><i class="fa-solid fa-bolt"></i> ${Math.round(t)}%</span>` : '')(thunderAt(j))}
                    </div>`;""")
# daily icon: thunder chance 40%+ gets the lightning icon
_r("""            const likely = precipExpected(p, amt); // the chance must be high; model amounts alone never trigger a wet icon""", """            if ((bb.thunder || 0) >= 40 && snow < 0.5) return { text: 'Thunderstorms', icon: 'fa-cloud-bolt', color: 'text-amber-400' };
            const likely = precipExpected(p, amt); // the chance must be high; model amounts alone never trigger a wet icon""")
# forecast cards: thunder chance under the condition text
_r("""${iconHtml(cond, pv.precipProb, 'text-3xl')}<span class="text-[10px] leading-tight text-slate-400 mt-0.5">${cond.text}</span></div>""",
   """${iconHtml(cond, pv.precipProb, 'text-3xl')}<span class="text-[10px] leading-tight text-slate-400 mt-0.5">${cond.text}</span>${ni ? '' : tstmTag(bb.thunder)}</div>""")
_r(""".rec-btn { background: none;""", """.tstm { display: inline-flex; align-items: center; gap: 3px; font: 700 10px/1.4 ui-monospace, Menlo, monospace; color: #fcd34d; background: rgba(245,158,11,.14); border: 1px solid rgba(251,191,36,.45); border-radius: 999px; padding: 1px 7px; margin-top: 2px; }
.rec-btn { background: none;""")
# ---- graph high/low: label the window's extreme even when it falls at the edge of the day (falling or rising all day) ----
_r("""                        const p = fcT[best - 1], q = fcT[best + 1];                                    // must be a true turning point of the curve
                        if (p === null || p === undefined || q === null || q === undefined) return -1;
                        if (hi ? (fcT[best] < p || fcT[best] < q) : (fcT[best] > p || fcT[best] > q)) return -1;
                        return best;""", """                        return best;""")
# ---- hourly curve agrees with the forecast high: the daytime peak of the hourly temperatures is mapped onto the best-bet high ----
_r("""            const ck = `${h.time[0]}|${cc.temp}|${cc.dew}|${(nwsObsToday || []).length}|${todayModelSkill ? JSON.stringify(todayModelSkill.weights) : ''}`;""",
   """            const ck = `${h.time[0]}|${cc.temp}|${cc.dew}|${(nwsObsToday || []).length}|${todayModelSkill ? JSON.stringify(todayModelSkill.weights) : ''}|${(bestBetResults || []).slice(0, 3).map(b => b.bestMax).join(',')}`;""")
_r("""            const v = { T, D, bT, bD, cur, trend };
            _adjCache = { k: ck, v };""", """            // the next two days: the daytime peak equals the forecast high
            (bestBetResults || []).slice(0, 3).forEach((b, di) => {
                if (!b || !ok(b.bestMax)) return;
                const idx = [];
                for (let j = Math.max(cur + 1, 0); j < T.length; j++) { const t = h.time[j]; if (t.startsWith(b.date) && +t.slice(11, 13) >= 6 && +t.slice(11, 13) <= 21 && T[j] !== null) idx.push(j); }
                if (idx.length < 3) return;
                const vals = idx.map(j => T[j]), M = Math.max(...vals), base = Math.min(...vals), H = di === 0 ? todayCurveTarget : b.bestMax;
                if (di === 0 && todayCurveTarget == null) return;   // today: mapped only to the final blended high (raiseTodayHigh)
                if (Math.abs(M - H) < 0.15) return;
                const delta = {};
                idx.forEach(j => {
                    const nv = (M - base > 0.5 && H > base) ? base + (T[j] - base) * (H - base) / (M - base) : T[j] + (H - M);
                    delta[j] = nv - T[j];
                });
                const last = idx[idx.length - 1], dl = delta[last];
                idx.forEach(j => { T[j] += delta[j]; });
                for (let k = 1; k <= 3; k++) { const j = last + k; if (j < T.length && T[j] !== null) T[j] += dl * (1 - k / 4); }
            });
            for (let j = cur + 1; j < D.length; j++) if (D[j] !== null && T[j] !== null) D[j] = Math.min(D[j], T[j]);
            const v = { T, D, bT, bD, cur, trend };
            _adjCache = { k: ck, v };""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        // Today's high. 1) The observation-corrected hourly curve (latest obs + measured warming trend) sets a floor on the
        // model blend. 2) The official NWS forecast for today's daytime period is weighted in (40%) while that period is still
        // ahead. 3) Never below what has already been measured. The hourly curve is then mapped so its peak matches.
        let todayCurveTarget = null;
        function raiseTodayHigh() {
            const b = bestBetResults && bestBetResults[0];
            if (!b || b.bestMax == null) return;
            todayCurveTarget = null; _adjCache = null;
            const a = obsAdjustedHourly(), h = ensembleData && ensembleData.hourly;
            let M = null, nLeft = 0;
            if (a && h) for (let j = a.cur + 1; j < a.T.length; j++) { const t = h.time[j]; if (!t || !t.startsWith(b.date)) continue; const hr = +t.slice(11, 13); if (hr < 6 || hr > 21 || a.T[j] == null) continue; nLeft++; if (M === null || a.T[j] > M) M = a.T[j]; }
            let H = b.bestMax;
            if (M !== null && M > H) H = M;
            const periods = nwsForecastData && nwsForecastData.properties && nwsForecastData.properties.periods;
            const dayP = nLeft >= 3 && periods && periods.find(p => p.isDaytime && p.startTime.substring(0, 10) === b.date && p.temperature != null && Date.parse(p.endTime) > Date.now());
            if (dayP) { const nC = dayP.temperatureUnit === 'C' ? dayP.temperature : (dayP.temperature - 32) / 1.8; H = H * 0.6 + nC * 0.4; b.nwsBlendApplied = true; }
            const mh = typeof measuredHighAfterLow === 'function' ? measuredHighAfterLow() : null;
            if (mh !== null && mh > H) H = mh;
            b.bestMax = H;
            if (M !== null && Math.abs(M - H) >= 0.15) todayCurveTarget = H;
            _adjCache = null;
        }
""" + out[_a:]
_r("""                                <span><i class="fa-solid fa-umbrella text-blue-400 mr-1"></i>${pv.precipProb}%</span>""",
   """                                <span>${WET_ICONS.includes(cond.icon) ? `<i class="fa-solid fa-umbrella text-blue-400 mr-1"></i>${Math.round(pv.precipProb)}%` : ''}</span>""")
_r("""<span class="text-[10px] leading-tight text-slate-400 mt-0.5">${cond.text}</span>${ni ? '' : tstmTag(bb.thunder)}</div>""",
   """<span class="text-[10px] leading-tight text-slate-400 mt-0.5">${cond.text}</span>${ni || !WET_ICONS.includes(cond.icon) ? '' : tstmTag(bb.thunder)}</div>""")
_r("""                                <span>${WET_ICONS.includes(cond.icon) ? `<i class="fa-solid fa-umbrella text-blue-400 mr-1"></i>${Math.round(pv.precipProb)}%` : ''}</span>""",
   """                                <span></span>""")
# ---- forecast cards: wind moves into the temperature column; the separate wind row goes ----
_r("""                                    <div class="text-xs text-slate-400" title="Overnight low into the next morning">${formatTemp(bb.bestMin)} <span class="text-[10px] text-slate-500">overnight</span></div>`}
                                </div>
                            </div>

                            <div class="flex justify-between items-center text-[11px] text-slate-300 font-mono mb-2.5 px-0.5">
                                <span></span>
                                <span><i class="fa-solid fa-wind text-slate-400 mr-1"></i>${compass(bb.windDir) ? compass(bb.windDir) + ' ' : ''}${formatSpeed(pv.bestWind)}</span>
                            </div>""", """                                    <div class="text-xs text-slate-400" title="Overnight low into the next morning">${formatTemp(bb.bestMin)} <span class="text-[10px] text-slate-500">overnight</span></div>`}
                                    <div class="text-[11px] text-slate-300 font-mono mt-1"><i class="fa-solid fa-wind text-slate-400 mr-1"></i>${compass(bb.windDir) ? compass(bb.windDir) + ' ' : ''}${formatSpeed(pv.bestWind)}</div>
                                </div>
                            </div>""")
# ---- climate reports: one failed request no longer drops the station's records ----
_r("""            let rows = [], prev = [];
            try { [rows, prev] = await Promise.all([get(y), getPrev().catch(() => [])]); } catch (e) { return null; }""",
   """            let rows = [], prev = [];
            const curKey = `clicur1:${icao}:${y}`;
            const [r1, p1] = await Promise.all([
                get(y).catch(() => new Promise(res => setTimeout(res, 1200)).then(() => get(y))).catch(() => null),
                getPrev().catch(() => new Promise(res => setTimeout(res, 1200)).then(getPrev)).catch(() => [])
            ]);
            prev = p1 || [];
            if (r1) { rows = r1; idb.set(curKey, { t: Date.now(), rows: r1 }).catch(() => {}); }
            else { const c = await idb.get(curKey); rows = (c && c.rows) || []; }
            if (!r1 && !rows.length && !prev.length) return null;""")
# ---- climate reports: try the best representative sites in order until one delivers ----
_r("""        async function fetchCLI(nws, today, lat, lon) {
            if (lat != null && climOverride(lat, lon)) return null;   // the user picked a station: its own record is used
            const site = (lat != null) ? await nearestCliSite(lat, lon, nws && nws.obs && nws.obs.stationId) : null;
            const icao = site ? site.id : (nws && nws.obs && nws.obs.stationId);
            if (!icao) return null;
            const y = +today.slice(0, 4);""", """        // climate-report sites near a point, best first: the observing station's own site, then the nearest ones within 40 km,
        // each within 300 m of the location's elevation
        async function cliCandidates(lat, lon, obsIcao) {
            try {
                await _nearestCliSite(lat, lon, obsIcao);   // loads and caches the site list
                const list = await cliNetPromise;
                const live = list.filter(s => !s.end || s.end >= new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10));
                const out = [];
                const own = live.find(s => s.id === obsIcao);
                if (own && distKm(+lat, +lon, own.lat, own.lon) <= 60) out.push({ ...own, km: distKm(+lat, +lon, own.lat, own.lon) });
                live.filter(s => s !== own).map(s => ({ ...s, km: distKm(+lat, +lon, s.lat, s.lon) })).filter(s => s.km <= 40).sort((a, b) => a.km - b.km).forEach(s => out.push(s));
                const ok = [];
                for (const s of out.slice(0, 4)) if (await representative(lat, lon, s.lat, s.lon)) ok.push(s);
                return ok;
            } catch (e) { return []; }
        }
        async function fetchCLI(nws, today, lat, lon) {
            if (lat != null && climOverride(lat, lon)) return null;   // the user picked a station: its own record is used
            const obsId = nws && nws.obs && nws.obs.stationId;
            const cands = lat != null ? await cliCandidates(lat, lon, obsId) : [];
            const ids = cands.length ? cands.map(s => s.id) : (obsId ? [obsId] : []);
            for (const icao of ids.slice(0, 3)) {
                const r = await fetchCLIFor(icao, today).catch(() => null);
                if (r && ((r.rows && r.rows.length) || (r.prevRows && r.prevRows.length))) return r;
            }
            return null;
        }
        async function fetchCLIFor(icao, today) {
            if (!icao) return null;
            const y = +today.slice(0, 4);""")
# station period-of-record: one retry per id so a slow request does not blank the records
_r("""                    const r = await fetch(`https://data.rcc-acis.org/StnData?sid=${encodeURIComponent(sid)}&sdate=por&edate=${yest}&elems=maxt,mint,pcpn,snow&meta=name&output=json`);
                    if (!r.ok) continue;""", """                    const u = `https://data.rcc-acis.org/StnData?sid=${encodeURIComponent(sid)}&sdate=por&edate=${yest}&elems=maxt,mint,pcpn,snow&meta=name&output=json`;
                    let r = await fetch(u).catch(() => null);
                    if (!r || !r.ok) { await new Promise(res => setTimeout(res, 1500)); r = await fetch(u).catch(() => null); }
                    if (!r || !r.ok) continue;""")
# ---- climate-report site = the nearest qualifying one (not the observing station by default) ----
_r("""                const own = live.find(s => s.id === obsIcao);
                if (own && distKm(+lat, +lon, own.lat, own.lon) <= 60) out.push({ ...own, km: distKm(+lat, +lon, own.lat, own.lon) });
                live.filter(s => s !== own).map(s => ({ ...s, km: distKm(+lat, +lon, s.lat, s.lon) })).filter(s => s.km <= 40).sort((a, b) => a.km - b.km).forEach(s => out.push(s));""",
   """                live.map(s => ({ ...s, km: distKm(+lat, +lon, s.lat, s.lon) })).filter(s => s.km <= 40 || (s.id === obsIcao && s.km <= 60)).sort((a, b) => a.km - b.km).forEach(s => out.push(s));""")
_r("""                const own = live.find(s => s.id === obsIcao);
                if (own && distKm(+lat, +lon, own.lat, own.lon) <= 60) return { ...own, km: distKm(+lat, +lon, own.lat, own.lon) };
                let best = null;""", """                let best = null;""")
_r("""                const key = `climstn5:${k}`;""", """                const key = `climstn6:${k}`;""")
_r("""            const key = `stnclim4:${icao}:${ovS ? ovS.ids[0] : 'auto'}`;""", """            const key = `stnclim5:${(+lat).toFixed(2)},${(+lon).toFixed(2)}:${ovS ? ovS.ids[0] : 'auto'}`;""")
# ---- observed sky wording follows NWS day/night convention (Sunny/Mostly Sunny by day, Clear/Mostly Clear at night) ----
_r("""                r.text = o.textDescription || null;""", """                r.text = skyWording(o.textDescription || null, r.isDay === 1 || r.isDay === true);""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        function skyWording(t, day) {
            if (!t) return t;
            const pairs = day ? [[/^mostly clear$/i, 'Mostly Sunny'], [/^(clear|fair)$/i, 'Sunny'], [/^partly clear$/i, 'Partly Sunny']]
                              : [[/^mostly sunny$/i, 'Mostly Clear'], [/^(sunny|fair)$/i, 'Clear'], [/^partly sunny$/i, 'Partly Cloudy']];
            const s = String(t).trim();
            for (const [re, w] of pairs) if (re.test(s)) return w;
            return t.replace(day ? /\\bfair\\b/i : /\\bsunny\\b/i, day ? 'Sunny' : 'Clear');
        }
""" + out[_a:]
# ---- NWS gridded PoP/sky blend + radar nowcast ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/radar.js').read() + out[_a:]
_r("""                nwsThunder = nws.thunder || null;""", """                nwsThunder = nws.thunder || null;
                try { blendNwsGrid(nws); } catch (e) {}
                radarInfo = null;""")
_r("""                if (nwsOffice) loadSPC(token, lat, lon);""", """                if (nwsOffice) loadSPC(token, lat, lon);
                if (nwsOffice) loadRadar(token, lat, lon);""")
# ---- self-verification / learning ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/learning.js').read() + open('/home/claude/learning_hourly.js').read() + out[_a:]
# main pipeline and recompute: learn after the blend, save the uncorrected forecast
_r("""                try { annotateThunder(); } catch (e) {}
                try { raiseTodayHigh(); } catch (e) {}
                renderDashboard();""", """                try { annotateThunder(); } catch (e) {}
                try { raiseTodayHigh(); } catch (e) {}
                try { applyLearning(); } catch (e) {}
                renderDashboard();
                (async () => { try { await updateLearning(); if (token !== fetchToken) return; recomputeForecast(); saveForecastSnapshot(); } catch (e) {} })();""")
_r("""                annotateThunder(); raiseTodayHigh();
                _adjCache = null;""", """                annotateThunder(); raiseTodayHigh(); applyLearning();
                _adjCache = null;""")
_r("""                try { blendNwsGrid(nws); } catch (e) {}
                radarInfo = null;""", """                try { blendNwsGrid(nws); } catch (e) {}
                radarInfo = null; radarNow = null; learnState = null;""")
# ---- icons: a yellow sun behind a light cloud (single-colour glyphs painted the sun blue) ----
_css = r"""
        i.fa-cloud-sun, i.fa-cloud-sun-rain { position: relative; isolation: isolate; }
        i.fa-cloud-sun::before, i.fa-cloud-sun-rain::before { content: "\f0c2"; color: #cbd5e1; position: relative; z-index: 1; }
        i.fa-cloud-sun-rain::before { content: "\f73d"; color: #93c5fd; }
        i.fa-cloud-sun::after, i.fa-cloud-sun-rain::after { content: "\f185"; color: #fbbf24; position: absolute; z-index: 0; font-size: .7em; top: -.22em; right: -.14em; font-family: inherit; font-weight: inherit; }
"""
_i = out.index('</style>')
out = out[:_i] + _css + out[_i:]
# ---- day / night for each forecast hour from the actual sunrise and sunset: an hour shows the sun only if the sun is up at that time ----
_r("""                ensembleData = base;
""", """                ensembleData = base;
                try { setHourlyDaylight(base); } catch (e) {}
""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + r"""        function setHourlyDaylight(d) {
            const h = d && d.hourly, dl = d && d.daily;
            if (!h || !h.time || !dl || !dl.sunrise || !dl.sunset) return;
            const sun = {};
            dl.time.forEach((t, i) => { if (dl.sunrise[i] && dl.sunset[i]) sun[t] = [Date.parse(dl.sunrise[i]), Date.parse(dl.sunset[i])]; });
            h.is_day = h.time.map((t, j) => {
                const s = sun[t.slice(0, 10)];
                if (!s) return h.is_day ? h.is_day[j] : 0;
                const at = Date.parse(t);   // the sun is up at the card's time
                return at >= s[0] && at < s[1] ? 1 : 0;
            });
        }
""" + out[_a:]

# ---- current conditions: the station can lag or miss precipitation; radar right over the location decides ----
_r("""            return r;
        }

        function conditionFromText(""", """            radarWeather(r);
            return r;
        }
        // light / moderate / heavy by reflectivity over the location (within the last 20 minutes)
        function radarWeather(r) {
            if (!radarNow || Date.now() - radarNow.t > 20 * 60e3) return;
            const wetTxt = /rain|shower|drizzle|snow|sleet|thunder|storm|freezing|ice pellets|flurr/i;
            const z = radarNow.z || 0;   // the location's own sample, not neighbouring cells
            // the station still reports precipitation, but newer radar shows the location clear with nothing on the way
            if (z < 15 && !radarNow.drizzle && r.text && wetTxt.test(r.text) && radarNow.clearAhead && nwsObs && nwsObs.timestamp && radarNow.t - Date.parse(nwsObs.timestamp) > 10 * 60e3) {
                const amt = (r.layers || []).reduce((m, l) => Math.max(m, { FEW: 1, SCT: 2, BKN: 3, OVC: 4, VV: 4 }[l.amount] || 0), 0);
                const day = r.isDay === 1 || r.isDay === true;
                r.text = amt >= 4 || !amt ? 'Cloudy' : amt === 3 ? 'Mostly Cloudy' : amt === 2 ? 'Partly Cloudy' : (day ? 'Mostly Sunny' : 'Mostly Clear');
                r.code = amt >= 4 || !amt ? 3 : amt === 3 ? 3 : 2; r.wx = []; r.radarWx = true;
                return;
            }
            if (z < 20 && radarNow.drizzle && !(r.text && wetTxt.test(r.text))) {   // light echoes overhead in a saturated layer
                const frz = r.temp !== null && r.temp !== undefined && r.temp <= 0.5;
                r.text = frz ? 'Flurries' : 'Light Drizzle'; r.code = frz ? 71 : 51; r.radarWx = true; return;
            }
            if (z < 20 || (r.text && wetTxt.test(r.text))) return;
            const snow = r.temp !== null && r.temp !== undefined && r.temp <= 0.5;
            const kind = snow ? 'Snow' : 'Rain';
            r.text = z >= 45 ? (snow ? 'Heavy Snow' : 'Heavy Rain') : z >= 30 ? kind : 'Light ' + kind;
            r.code = snow ? (z >= 30 ? 73 : 71) : (z >= 45 ? 65 : z >= 30 ? 63 : 61);
            r.radarWx = true;
        }

        function conditionFromText(""")

# ---- hourly learning: raw copy for verification, corrections applied once per load before the forecast is built ----
_r("""        function modelWindAt(field, j) {
            const h = ensembleData.hourly, mh""", """        function _modelWindAtRaw(field, j) {
            const h = ensembleData.hourly, mh""")
_r("""                radarInfo = null; radarNow = null; learnState = null;""", """                radarInfo = null; radarNow = null; learnState = null; hourlyLearn = null;
                try { snapHourlyRaw(); } catch (e) {}""")

# ---- today's curve is stretched to the forecast high only while the afternoon peak is still ahead ----
_r("""                if (di === 0 && todayCurveTarget == null) return;   // today: mapped only to the final blended high (raiseTodayHigh)""", """                if (di === 0 && todayCurveTarget == null) return;   // today: mapped only to the final blended high (raiseTodayHigh)
                if (di === 0) {   // once the day's peak hour has passed (or the sun is down) the evening is never lifted to the high
                    let jp = -1, pv = -Infinity;
                    for (let j = 0; j < T.length; j++) { const t = h.time[j]; if (t.startsWith(b.date) && +t.slice(11, 13) >= 10 && +t.slice(11, 13) <= 18 && ok(baseT[j]) && baseT[j] > pv) { pv = baseT[j]; jp = j; } }
                    if (jp < 0 || jp <= cur || !(cc.isDay === 1 || cc.isDay === true)) return;
                }""")
# tonight: a rise is only a rise when the warmest hour comes after the coolest one
_r("""            const rising = hi > nowT + 0.8;   // temperatures climb overnight (e.g. warm advection)""", """            let jLo = -1, jHi = -1, vLo = Infinity, vHi = -Infinity;
            for (let j = cur + 1; j <= endIdx; j++) { const t = adj && ok(adj.T[j]) ? adj.T[j] : h.temperature_2m[j]; if (!ok(t)) continue; if (t < vLo) { vLo = t; jLo = j; } if (t > vHi) { vHi = t; jHi = j; } }
            const rising = hi > nowT + 0.8 && jHi > jLo && vHi - vLo >= 1;   // temperatures climb overnight (e.g. warm advection)""")

# ---- regional observations ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/regional.js').read() + out[_a:]
_r("""const sl = await (await fetch(props.observationStations)).json();""", """const sl = await (await fetch(props.observationStations)).json();
                        out.stationList = sl.features || null;""")
_r("""                nwsThunder = nws.thunder || null;""", """                nwsThunder = nws.thunder || null;
                nwsStationList = nws.stationList || null; regionalAdj = null; regionalInfo = null;""")
_r("""                if (nwsOffice) loadRadar(token, lat, lon);""", """                if (nwsOffice) loadRadar(token, lat, lon);
                if (nwsOffice) loadRegional(token, lat, lon);
                loadHourlyLearning(token, lat, lon);""")
_r("""            const v = { T, D, bT, bD, cur, trend };""", """            for (let j = cur + 1; j <= cur + 9 && j < T.length; j++) {
                if (T[j] !== null) T[j] += regionalDelta('t', j);
                if (D[j] !== null) D[j] = Math.min(D[j] + regionalDelta('td', j), T[j] ?? Infinity);
            }
            const v = { T, D, bT, bD, cur, trend };""")
_r("""(bestBetResults || []).slice(0, 3).map(b => b.bestMax).join(',')}`;
            if (_adjCache""", """(bestBetResults || []).slice(0, 3).map(b => b.bestMax).join(',')}|${regionalAdj ? regionalAdj.at : 0}`;
            if (_adjCache""")
_r("""
            $h('heroNarrative').innerText = parts.join(' ');
            $h('heroNarrLbl').innerText = 'Today';""", """            if (regionalInfo && regionalInfo.msg) parts.splice(1, 0, regionalInfo.msg);

            $h('heroNarrative').innerText = parts.join(' ');
            $h('heroNarrLbl').innerText = 'Today';""")

# ---- station observation: the location's own station first (NWS API, then the same reports from IEM), then the next station ----
_r("""                        for (const f of feats) {
                            const o = await (await fetch(`https://api.weather.gov/stations/${f.properties.stationIdentifier}/observations/latest`)).json();
                            const v = o && o.properties;""", """                        // the same airport reports from the Iowa Environmental Mesonet, for when the NWS API has nothing recent
                        const iemLatest = async (f) => {
                            const sid = f.properties.stationIdentifier || '', st = out.state;
                            if (!st || !/^K[A-Z0-9]{3}$/.test(sid)) return null;
                            const day = n => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
                            const rows = (await Promise.all([day(0), day(-1)].map(d => fetch(`https://mesonet.agron.iastate.edu/api/1/obhistory.json?station=${sid.slice(1)}&network=${st}_ASOS&date=${d}&full=1`)
                                .then(r => r.ok ? r.json() : { data: [] }).then(j => Array.isArray(j.data) ? j.data : []).catch(() => [])))).flat();
                            const obs = rows.map(iemToObs).filter(o => o.timestamp && o.temperature && o.temperature.value !== null && Date.now() - new Date(o.timestamp) < 3 * 3600e3)
                                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).map(o => { delete o.intl; return o; });
                            return obs.length ? obs : null;
                        };
                        for (const f of feats) {
                            let o = null;
                            try { const rr = await fetch(`https://api.weather.gov/stations/${f.properties.stationIdentifier}/observations/latest`); o = rr.ok ? await rr.json() : null; } catch (e) { o = null; }
                            let v = o && o.properties;
                            if (!(v && v.temperature && v.temperature.value != null && v.timestamp && (Date.now() - new Date(v.timestamp)) < 3 * 3600e3)) {
                                // nothing recent from the NWS for this station: same station from IEM before moving to another station
                                try {
                                    const io = await iemLatest(f);
                                    if (io) { v = { ...io[0], viaIEM: true }; out.obsToday = io; }
                                } catch (e) {}
                            }""")
_r("""                                out.obsToday = (t.features || []).map(f => f.properties);""", """                                const nwsRows = (t.features || []).map(f => f.properties);
                                if (out.obs.viaIEM) {   // keep the IEM reports and add any the NWS has that IEM does not
                                    const have = new Set(out.obsToday.filter(o => o && o.timestamp).map(o => Math.round(new Date(o.timestamp) / 120000)));
                                    out.obsToday = [...out.obsToday, ...nwsRows.filter(o => o && o.timestamp && !have.has(Math.round(new Date(o.timestamp) / 120000)))].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                                } else out.obsToday = nwsRows;""")
# ---- current conditions use the same station the verification uses for each tracked city ----
_r("""        function preferredStation(lat, lon) {
            if (Math.abs(Number(lat) - 39.0437) < 0.2 && Math.abs(Number(lon) + 77.4875) < 0.2)
                return { id: 'KIAD', name: 'Washington/Dulles International Airport', elev: 95, lat: 38.9348, lon: -77.4473 };
            return null;
        }""", """        // tracked cities (data/locations.json): the station their forecasts are verified against; elevation comes from the report
        const VERIFY_STATIONS = [
            [39.0437, -77.4875, 'KIAD', 'Washington Dulles International Airport', 38.9348, -77.4473],
            [38.9846, -77.5397, 'KIAD', 'Washington Dulles International Airport', 38.9348, -77.4473],
            [38.8015, -77.2664, 'KDAA', 'Davison Army Airfield', 38.7150, -77.1810],
            [38.8951, -77.0364, 'KDCA', 'Washington Reagan National Airport', 38.8483, -77.0342],
            [40.7143, -74.0060, 'KLGA', 'New York LaGuardia Airport', 40.7769, -73.8740],
            [39.7392, -104.9903, 'KDEN', 'Denver International Airport', 39.8466, -104.6562],
            [41.8500, -87.6500, 'KMDW', 'Chicago Midway Airport', 41.7861, -87.7524],
            [47.6062, -122.3321, 'KSEA', 'Seattle-Tacoma International Airport', 47.4447, -122.3144],
            [37.6485, -118.9721, 'KMMH', 'Mammoth Yosemite Airport', 37.6241, -118.8378],
            [61.2181, -149.9003, 'PANC', 'Anchorage Ted Stevens International Airport', 61.1744, -149.9964],
            [25.7617, -80.1918, 'KMIA', 'Miami International Airport', 25.7881, -80.3169],
            [34.0522, -118.2437, 'KBUR', 'Burbank Hollywood Burbank Airport', 34.2007, -118.3585],
            [33.4484, -112.0740, 'KPHX', 'Phoenix Sky Harbor International Airport', 33.4278, -112.0037],
            [38.6270, -90.1994, 'KSTL', 'St. Louis Lambert International Airport', 38.7525, -90.3734],
            [21.3069, -157.8583, 'PHNL', 'Honolulu International Airport', 21.3245, -157.9251],
            [42.3601, -71.0589, 'KBOS', 'Boston Logan International Airport', 42.3606, -71.0097],
            [32.7767, -96.7970, 'KDAL', 'Dallas Love Field', 32.8471, -96.8518],
            [44.9778, -93.2650, 'KMSP', 'Minneapolis-St. Paul International Airport', 44.8831, -93.2289]
        ];
        function preferredStation(lat, lon) {
            let best = null;
            VERIFY_STATIONS.forEach(([la, lo, id, name, sla, slo]) => { const km = distKm(+lat, +lon, la, lo); if (km <= 12 && (!best || km < best.km)) best = { km, id, name, lat: sla, lon: slo, elev: null }; });
            return best;
        }""")

# radar shows the hour clear (rain passed, nothing on the way): no wet or thunder code from older guidance
_r("""            const th = thunderAt(j);
            if (th != null && th >= 40) return 95;""", """            if (typeof radarDry !== 'undefined' && radarDry[j]) return 0;
            const th = thunderAt(j);
            if (th != null && th >= 40) return 95;""")

# the last station report says rain, but newer radar shows the location clear with nothing on the way: the rain has ended
_r("""            if (nowKind) return { wet: true, kind: nowKind, lastHourMm };""", """            const obsMs = nwsObs.timestamp ? Date.parse(nwsObs.timestamp) : 0;
            if (nowKind && radarNow && radarNow.clearAhead && (radarNow.z || 0) < 15 && radarNow.t - obsMs > 10 * 60e3 && Date.now() - radarNow.t < 20 * 60e3)
                return { wet: false, kind: nowKind, endedAgo: 0, lastHourMm, persist: 20 };
            if (nowKind) return { wet: true, kind: nowKind, lastHourMm };""")
_r("""                                  persist: Math.round(60 * Math.exp(-Math.max(0, lastWet.ago) / 1.5)) };   // showers often redevelop soon after they end""", """                                  persist: radarNow && radarNow.clearAhead && Date.now() - radarNow.t < 20 * 60e3 ? 20   // radar: nothing on the way
                                         : Math.round(60 * Math.exp(-Math.max(0, lastWet.ago) / 1.5)) };   // showers often redevelop soon after they end""")
# ---- precipitation falling now: when it ends (radar) and the chance of MORE afterwards, never a 100% for the whole period ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + r"""        // first hour after the current precipitation ends (radar estimate when available, else the next hour)
        function rainEndIdx() {
            const cur = hourlyStart(), ct = ensembleData.current && ensembleData.current.time, mm = ct ? (parseInt(ct.slice(14, 16)) || 0) : 0;
            if (radarNow && radarNow.endMin != null && Date.now() - radarNow.t < 25 * 60e3) return cur + Math.max(1, Math.ceil((mm + radarNow.endMin + 5) / 60));
            return cur + 1;
        }
        // chance of more precipitation after the current rain ends, through hour toIdx
        function laterChance(toIdx) {
            const h = ensembleData.hourly; let m = 0;
            for (let j = rainEndIdx(); j <= toIdx && j < h.time.length; j++) { const v = h.precipitation_probability[j]; if (v != null && !isNaN(v)) m = Math.max(m, v); }
            return Math.round(m);
        }
        function rainEndText() {
            if (!radarNow || radarNow.endMin == null || Date.now() - radarNow.t > 25 * 60e3) return null;
            const t = new Date(Math.round((radarNow.t + radarNow.endMin * 60e3) / 9e5) * 9e5);
            if (t - Date.now() < 10 * 60e3) return 'ending';
            if (!radarNow.timeSure || radarNow.endMin > 90) {   // not sure enough for a clock time: part of the day
                const hr = +t.toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: ensembleData.timezone }) % 24;
                return 'ending ' + (hr < 5 ? 'overnight' : hr < 12 ? 'this morning' : hr < 17 ? 'this afternoon' : hr < 21 ? 'this evening' : 'tonight');
            }
            return 'ending around ' + t.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: ensembleData.timezone });
        }
        function moreText(p, when) {
            if (p < 20) return '';
            const an = p === 8 || p === 11 || p === 18 || (p >= 80 && p < 90) ? 'an' : 'a';
            return p <= 30 ? `Then ${an} ${p}% chance of a passing shower.` : `Then ${an} ${p}% chance of more ${when}.`;
        }
""" + out[_a:]
_r("""            return { early, end, low: lo, high: rising ? hi : null, pp: Math.round(pp), rain: sn.rain, snow: sn.snow, wind, gust, cond, nowcast: ncT.nowcast || null };""",
   """            return { early, end, low: lo, high: rising ? hi : null, pp: Math.round(pp), rain: sn.rain, snow: sn.snow, wind, gust, cond, nowcast: ncT.nowcast || null, laterPP: laterChance(endIdx) };""")
_r("""                const parts = [ni.nowcast && ni.nowcast.wet ? `${NOWCAST_WORD[ni.nowcast.kind]} falling now; low tonight near ${formatTemp(ni.low)}.` :""",
   """                const parts = [ni.nowcast && ni.nowcast.wet ? `${NOWCAST_WORD[ni.nowcast.kind]} ${rainEndText() || 'falling now'}; low tonight near ${formatTemp(ni.low)}.` :""")
_r("""                if (precipExpected(ni.pp, ni.rain + ni.snow)) parts.push(`${ni.pp}% chance of precipitation""",
   """                if (ni.nowcast && ni.nowcast.wet) { const mt = moreText(ni.laterPP, 'tonight'); if (mt) parts.push(mt); }
                else if (precipExpected(ni.pp, ni.rain + ni.snow)) parts.push(`${ni.pp}% chance of precipitation""")
_r("""                bb.precipProb = Math.round(o.pp); bb.weatherCode = o.code; bb.nowcast = o.nowcast || null; bb.laterProb = modelProb;""",
   """                bb.precipProb = Math.round(o.pp); bb.weatherCode = o.code; bb.nowcast = o.nowcast || null; bb.laterProb = laterChance(ids[ids.length - 1]);""")
_r("""                parts.push(`${NOWCAST_WORD[nc.kind]} falling now, with a high near ${formatTemp(bb.bestMax)}.`);
                if (bb.bestPrecip >= 0.25) parts.push(`About ${formatPrecip(bb.bestPrecip)} more today.`);
                if (bb.laterProb != null) parts.push(`Once it ends, ${bb.laterProb}% chance of more later today.`);""",
   """                parts.push(`${NOWCAST_WORD[nc.kind]} ${rainEndText() || 'falling now'}, with a high near ${formatTemp(bb.bestMax)}.`);
                if (bb.bestPrecip >= 0.25 && bb.laterProb >= 40) parts.push(`About ${formatPrecip(bb.bestPrecip)} more today.`);
                if (bb.laterProb != null) { const mt = moreText(bb.laterProb, 'later today'); if (mt) parts.push(mt); }""")
# ---- a forecast card's chance and icon come from its own periods, so the card and its period icons always agree ----
_r("""                const cond = ni ? ni.cond : dailyCondition(bb);
                const pv = ni ? { precipProb: ni.pp, bestRain: ni.rain, bestSnow: ni.snow, bestWind: ni.wind } : bb;   // values shown on the card""",
   """                let cond = ni ? ni.cond : dailyCondition(bb);
                const pv = ni ? { precipProb: ni.pp, bestRain: ni.rain, bestSnow: ni.snow, bestWind: ni.wind } : { ...bb };   // values shown on the card
                {
                    const segs = ((ni ? tonightPeriods() : periodsFor(i)) || []).filter(p => p && !p.past);
                    if (segs.length) {
                        const sp = Math.round(Math.max(...segs.map(p => p.pp || 0)));
                        const wetSeg = segs.find(p => WET_ICONS.includes(p.cond.icon));
                        pv.precipProb = sp;
                        if (wetSeg && !WET_ICONS.includes(cond.icon)) cond = wetSeg.cond;
                        else if (!wetSeg && WET_ICONS.includes(cond.icon))
                            cond = ni ? segs.reduce((a, b) => (b.pp || 0) > (a.pp || 0) ? b : a).cond : dailyCondition({ ...bb, precipProb: sp, thunder: 0 });
                    }
                }""")
# with fresh radar, radar decides whether more is coming; the redevelopment guess is only for places without radar
_r("""                                  persist: radarNow && radarNow.clearAhead && Date.now() - radarNow.t < 20 * 60e3 ? 20   // radar: nothing on the way""",
   """                                  persist: radarNow && Date.now() - radarNow.t < 25 * 60e3 ? (radarNow.clearAhead ? 0 : 20)   // radar decides what is on the way""")
_r("""            const pp = ni ? ni.pp : b.precipProb, rain = ni ? ni.rain : b.bestRain, snow = ni ? ni.snow : b.bestSnow;""",
   """            let pp = ni ? ni.pp : b.precipProb; const rain = ni ? ni.rain : b.bestRain, snow = ni ? ni.snow : b.bestSnow;
            { const segs = ((ni ? tonightPeriods() : periodsFor(i)) || []).filter(p => p && !p.past); if (segs.length) pp = Math.round(Math.max(...segs.map(p => p.pp || 0))); }   // same chance as the card""")
# ---- past 24 hours of hourly station reports (Observed Climate) ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/obs24.js').read() + out[_a:]
_r("""            renderClimateAnalytics();

            // Render Hourly & Precip Charts""", """            renderClimateAnalytics();
            try { renderObs24(); } catch (e) {}

            // Render Hourly & Precip Charts""")
# ---- an hour shows precipitation only when its chance is 40%+ (the icon follows the number shown under it) ----
_r("""            if (!((wetCode && (hp >= 30 || (ha >= 0.1 && hp >= 20))) || hp >= 40)) return 0;""", """            if (hp < 40) return 0;""")
_r("""            if (th != null && th >= 40) return 95;""", """            if (th != null && th >= 40 && hp >= 40) return 95;""")
out = out.replace("// A forecast hour is wet when the chance is 40%+ (whatever the deterministic code says), or the code is wet with 30%+\n        // (20%+ with a measurable amount).", "// A forecast hour is wet when its chance is 40%+ (the icon follows the number shown with it).", 1)
# ---- first view as soon as the forecast and station data are in; climate records, totals and air quality fill in after ----
_r("""                const [models, nws, aq, pt, sn, cl, intl] = await Promise.all([modelsP, nwsP, aqP, ptP, snP, clP, intlP]);""",
   """                const [models, nws, intl] = await Promise.all([modelsP, nwsP, intlP]);
                const aq = null, pt = null, sn = null, cl = null;   // these arrive after the first view (below)""")
_r("""                (async () => { try { await updateLearning(); if (token !== fetchToken) return; recomputeForecast(); saveForecastSnapshot(); } catch (e) {} })();
                renderDiscussion();

                // Climate history (large request) loads last, then the dashboard re-renders with records and normals
                if (!cl) getClimLite(""", """                renderDiscussion();
                aqP.then(a => { if (token !== fetchToken) return; airQuality = (a && a.current) ? a.current : null; try { renderDashboard(); } catch (e) {} }).catch(() => {});
                Promise.all([ptP.catch(() => null), snP.catch(() => null), clP]).then(([pt2, sn2, cl2]) => {
                    if (token !== fetchToken) return;
                    precipTotals = pt2; snowTotals = sn2; cliTotals = cl2;
                    if (!cl2) getClimLite(lat, lon).then(d => { if (token !== fetchToken || !d || historicalData) return; climLite = d; buildClimIndex(); renderDashboard(); renderDiscussion(); }).catch(() => {});
                    try { renderDashboard(); renderDiscussion(); } catch (e) {}
                    (async () => { try { await updateLearning(); if (token !== fetchToken) return; recomputeForecast(); saveForecastSnapshot(); } catch (e) {} })();
                });

                // Climate history (large request) loads last, then the dashboard re-renders with records and normals
                if (false) getClimLite(""")

# ---- continuity between loads (hourly) and the last radar result on a quick reload ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/continuity_hourly.js').read() + out[_a:]
_r("""                try { snapHourlyRaw(); } catch (e) {}""", """                try { snapHourlyRaw(); } catch (e) {}
                radarDry = {};
                try { hourlyContinuity(); } catch (e) {}
                try { restoreRadarState(); } catch (e) {}""")
# ---- Radar map section, below Detailed Current Observations (starts closed) ----
_r("""            </div>
            <div id="sec-hourly">""", """            </div>
""" + open('/home/claude/radar_map.html').read() + """            <div id="sec-hourly">""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/radar_map.js').read() + out[_a:]
_r(""".rec-btn { background: none;""", """#radarMap { height: 440px; background: #0b0f17; }
@media (max-width: 767px) { #radarMap { height: 360px; } }
.rm-ctl { position: absolute; top: 10px; right: 10px; z-index: 600; display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; align-items: center; max-width: calc(100% - 60px); }
.rm-ctl select.rm-btn { appearance: none; -webkit-appearance: none; padding-right: 9px; }
.rm-chk, .rm-btn { background: rgba(8,16,34,.85); border: 1px solid rgba(255,255,255,.15); color: #e2e8f0; font-size: 12px; border-radius: 8px; padding: 5px 9px; display: flex; gap: 6px; align-items: center; cursor: pointer; }
.rm-time { position: absolute; left: 10px; bottom: 26px; z-index: 600; background: rgba(8,16,34,.85); color: #e2e8f0; font: 12px ui-monospace, monospace; border-radius: 6px; padding: 3px 8px; }
.rm-legend { position: absolute; right: 10px; bottom: 26px; z-index: 600; display: flex; align-items: center; gap: 5px; color: #cbd5e1; font: 10px ui-monospace, monospace; background: rgba(8,16,34,.85); border-radius: 6px; padding: 3px 7px; }
.rm-bar { width: 120px; height: 7px; border-radius: 3px; background: linear-gradient(90deg, rgb(52,96,120), rgb(2,200,30) 18%, rgb(0,140,0) 27%, rgb(235,225,0) 36%, rgb(250,110,0) 55%, rgb(225,0,0) 64%, rgb(165,0,0) 73%, rgb(240,0,240) 82%, rgb(150,60,220) 91%, #fff); }
#radarMap .leaflet-control-attribution { font-size: 9px; background: rgba(8,16,34,.7); color: #94a3b8; }
#radarMap .leaflet-control-attribution a { color: #94a3b8; }
#radarMap .leaflet-popup-content-wrapper, #radarMap .leaflet-popup-tip { background: #0f172a; color: #e2e8f0; }
.rec-btn { background: none;""")
_r("""                if (nwsOffice) loadRadar(token, lat, lon);
""", """                if (nwsOffice) loadRadar(token, lat, lon);
                if (typeof RM !== 'undefined' && RM.map) { radarMapCenter(true); if (document.getElementById('rmWarn').checked) radarMapWarnings(true); }
""")
# ---- radar section opens at start-up when precipitation is falling or expected later today ----
_r("""                renderDashboard();
                renderDiscussion();
                aqP.then(""", """                renderDashboard();
                renderDiscussion();
                try { radarAutoOpen(false); } catch (e) {}
                aqP.then(""")
_r("""                radarNow = { z: rn.here, z3: rn.here3, t: rn.t, clearAhead: rn.passed || rn.arrive === null || rn.clearUpstream, endMin: rn.endMin, timeSure: rn.timeSure };""",
   """                radarNow = { z: rn.here, z3: rn.here3, t: rn.t, clearAhead: rn.passed || rn.arrive === null || rn.clearUpstream, endMin: rn.endMin, timeSure: rn.timeSure };
                setTimeout(() => { try { radarAutoOpen(true); } catch (e) {} }, 0);""")
# ---- period wording: precipitation ranges near the end, full wind sentence (hero today / tonight and the outlook rows) ----
_r("""snowfall,wind_gusts_10m&daily=weather_code""", """snowfall,wind_gusts_10m,wind_direction_10m&daily=weather_code""")
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/period_text.js').read() + out[_a:]
# tonight
_r("""                if (ni.nowcast && ni.nowcast.wet) { const mt = moreText(ni.laterPP, 'tonight'); if (mt) parts.push(mt); }
                else if (precipExpected(ni.pp, ni.rain + ni.snow)) parts.push(`${ni.pp}% chance of precipitation${ni.rain >= 0.05 ? `, about ${formatPrecip(ni.rain)}` : ''}${ni.snow >= 0.05 ? ` (${formatSnow(ni.snow)} of snow)` : ''}.`);
                else if (ni.pp >= 20) parts.push(`A ${ni.pp}% chance of a passing shower.`);
                if (ni.gust >= 40) parts.push(`Gusts to ${formatSpeed(ni.gust)}.`);""", """                { const tsg = tonightSegs(ni); periodExtras(tsg, radarInfo && radarInfo.arrive).forEach(x => parts.push(x)); }""")
# today
_r("""                if (bb.bestPrecip >= 0.25 && bb.laterProb >= 40) parts.push(`About ${formatPrecip(bb.bestPrecip)} more today.`);
                if (bb.laterProb != null) { const mt = moreText(bb.laterProb, 'later today'); if (mt) parts.push(mt); }""", "")
_r("""                if (/shower|rain|storm|snow|drizzle|sleet|mix/i.test(ph) && bb.bestPrecip >= 0.25) parts.push(`About ${formatPrecip(bb.bestPrecip)} possible.`);
            }
            if (bb.bestGust >= 40) parts.push(`Gusts to ${formatSpeed(bb.bestGust)}.`);""", """            }
            periodExtras(todaySegs(), radarInfo && radarInfo.arrive).forEach(x => parts.push(x));""")
# outlook rows
_r("""                const amt = periodAmount(s, e);
                if (ph.wet && amt >= 2.5) bits.push(`About ${formatPrecip(amt)} possible.`);
                const sv = ph.wet && /thunder/.test(ph.text) ? thunderRisk(s, e) : null;
                if (sv) bits.push(sv.n >= 3 ? 'Severe storms possible.' : 'A few storms could be severe.');
                const g = periodGust(s, e);
                if (g >= 40) bits.push(`Gusts to ${formatSpeed(g)}.`);""", """                const sv = ph.wet && /thunder/.test(ph.text) ? thunderRisk(s, e) : null;
                if (sv) bits.push(sv.n >= 3 ? 'Severe storms possible.' : 'A few storms could be severe.');
                bits.push(...periodExtras(p.segs.map(([l, a, b]) => [l, a, b])));""")
# ---- start-up: saved home, else the device location when already allowed, else the intro page; home button ----
_r("""                    <h2 id="displayLocationName" class="text-2xl md:text-3xl font-black tracking-tight text-white">Location Name</h2>""",
   """                    <div class="flex items-center gap-2"><h2 id="displayLocationName" class="text-2xl md:text-3xl font-black tracking-tight text-white">Location Name</h2><button type="button" id="homeBtn" class="home-btn" onclick="toggleHome()" title="Make this my home location" aria-label="Make this my home location"><i class="fa-solid fa-house"></i></button></div>""")
_r("""            document.getElementById('displayLocationName').innerText = currentLoc.name;""",
   """            document.getElementById('displayLocationName').innerText = currentLoc.name;
            try { updateHomeBtn(); } catch (e) {}""")
_r("""            try { const s = JSON.parse(localStorage.getItem('skyline:lastLoc') || 'null'); if (s && isFinite(s.lat) && isFinite(s.lon)) currentLoc = s; } catch (e) {}
        }""", """            const home = getHome();
            if (home) { currentLoc = { ...home }; return 'home'; }
            // the device's location, only when the visitor has already allowed it (no permission prompt at start-up)
            try {
                if (navigator.permissions && navigator.geolocation) {
                    const st = await navigator.permissions.query({ name: 'geolocation' });
                    if (st.state === 'granted') {
                        const p = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, { enableHighAccuracy: false, timeout: 8000, maximumAge: 600000 }));
                        currentLoc = { name: 'My location', lat: +p.coords.latitude.toFixed(4), lon: +p.coords.longitude.toFixed(4), ele: 0, mine: true };
                        return 'device';
                    }
                }
            } catch (e) {}
            return 'intro';
        }
        function getHome() { try { const h = JSON.parse(localStorage.getItem('skyline:home') || 'null'); return h && isFinite(h.lat) && isFinite(h.lon) ? h : null; } catch (e) { return null; } }
        function isHome() { const h = getHome(); return !!(h && currentLoc && Math.abs(h.lat - currentLoc.lat) < 0.01 && Math.abs(h.lon - currentLoc.lon) < 0.01); }
        function updateHomeBtn() {
            const b = document.getElementById('homeBtn'); if (!b) return;
            const on = isHome(); b.classList.toggle('on', on);
            b.title = on ? 'Home location (tap to remove)' : 'Make this my home location'; b.setAttribute('aria-label', b.title);
        }
        function toggleHome() {
            try {
                if (isHome()) { localStorage.removeItem('skyline:home'); showToast('Home location removed.'); }
                else { localStorage.setItem('skyline:home', JSON.stringify({ name: currentLoc.name, lat: +currentLoc.lat, lon: +currentLoc.lon, ele: currentLoc.ele || 0 })); showToast(`${currentLoc.name} is now your home location.`); }
            } catch (e) {}
            updateHomeBtn();
        }""")
_r("""            if (isFinite(lat) && isFinite(lon)) { currentLoc = { name: city || `${lat.toFixed(2)}, ${lon.toFixed(2)}`, lat, lon, ele: 0 }; return; }""",
   """            if (isFinite(lat) && isFinite(lon)) {
                currentLoc = { name: city || `${lat.toFixed(2)}, ${lon.toFixed(2)}`, lat, lon, ele: 0 };
                if (q.get('home') === '1') { try { localStorage.setItem('skyline:home', JSON.stringify({ name: currentLoc.name, lat, lon, ele: 0 })); } catch (e) {} }   // a link that sets home
                return 'link';
            }""")
_r("""                    if (g) { currentLoc = { name: [g.name, g.admin1, g.country].filter(Boolean).join(', '), lat: g.latitude, lon: g.longitude, ele: g.elevation || 0 }; return; }""",
   """                    if (g) { currentLoc = { name: [g.name, g.admin1, g.country].filter(Boolean).join(', '), lat: g.latitude, lon: g.longitude, ele: g.elevation || 0 }; return 'link'; }""")
_r("""        window.onload = async function() {
            await startLocation();
            if (cityInput) cityInput.value = currentLoc.name;
            fetchForecastData();
        };""", """        window.onload = async function() {
            const how = await startLocation();
            if (how === 'intro') { if (cityInput) { cityInput.value = ''; if (window.innerWidth >= 1024) cityInput.focus(); } return; }   // wait for a town to be chosen
            if (cityInput) cityInput.value = currentLoc.name;
            fetchForecastData();
        };""")
_r(""".rec-btn { background: none;""", """.home-btn { width: 32px; height: 32px; border-radius: 999px; border: 1px solid rgba(255,255,255,.15); background: rgba(255,255,255,.06); color: #94a3b8; display: grid; place-items: center; font-size: 13px; cursor: pointer; flex-shrink: 0; }
.home-btn:hover { color: #e2e8f0; border-color: rgba(255,255,255,.3); }
.home-btn.on { color: #1a1205; background: linear-gradient(135deg, #ffc062, #ff7a59); border-color: transparent; }
.rec-btn { background: none;""")
# ---- the opening sentence describes the sky; the one precipitation sentence carries chance, amount and timing ----
_r("""                if (wetH) {
                    wetAll = true; codeAll = Math.max(codeAll, code);
                    const kind = code >= 95 ? (thunderOK && wpp < 80 ? 'showers and thunderstorms' : 'thunderstorms') : sn >= 0.5 ? 'snow showers' : 'showers';
                    const widespread = wetH >= Math.max(2, n / 2);
                    if (wpp >= 80 && widespread) state = code >= 95 ? 'thunderstorms' : sn >= 0.5 ? 'snow' : 'rain';
                    else if (wpp >= 60) state = `${sky} with ${kind} likely`;
                    else state = `${sky} with a ${Math.round(wpp / 10) * 10}% chance of ${kind}`;
                }""", """                if (wetH) { wetAll = true; codeAll = Math.max(codeAll, code); }   // precipitation is described once, in the precipitation sentence""")
_r("""                if (wetH) {
                    const kind = code >= 95 ? (spcThunderAt(Date.now()) && wpp < 80 ? 'showers and thunderstorms' : 'thunderstorms') : sn >= 0.5 ? 'snow showers' : 'showers';
                    const widespread = wetH >= Math.max(2, n / 2);
                    if (wpp >= 80 && widespread) state = code >= 95 ? 'thunderstorms' : sn >= 0.5 ? 'snow' : 'rain';
                    else if (wpp >= 60) state = `${sky} with ${kind} likely`;
                    else state = `${sky} with a ${Math.round(wpp / 10) * 10}% chance of ${kind}`;
                }""", "")

# ---- breezy / windy / very windy in the wording, the day cards and the hourly cells ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/wind_level.js').read() + out[_a:]
assert out.count("                let state = sky;") == 2
out = out.replace("                let state = sky;", "                let state = sky; const wlv = windLevel(s, e);")
# a part with the same sky as the one before differs only in wind: 'Mostly cloudy, becoming windy this afternoon'
_r("""                const last = parts[parts.length - 1];
                if (last && last.state === state) last.labels.push(label.replace('this ', ''));
                else parts.push({ state, labels: [label] });""", """                const last = parts[parts.length - 1];
                if (last && last.sky === sky && last.lv === wlv) last.labels.push(label.replace('this ', ''));
                else parts.push({ sky, lv: wlv, state: skyWindState(last, sky, wlv), labels: [label] });""")
_r("""                const last = parts[parts.length - 1];
                if (last && last.state === state) last.labels.push(label);
                else parts.push({ state, labels: [label] });""", """                const last = parts[parts.length - 1];
                if (last && last.sky === sky && last.lv === wlv) last.labels.push(label);
                else parts.push({ sky, lv: wlv, state: skyWindState(last, sky, wlv), labels: [label] });""")
_r("""            return cap(bits.length > 2 ? bits.slice(0, -1).join(', ') + ', then ' + bits.slice(-1) : bits.join(', then '));""",
   """            return cap(bits.length > 2 ? bits.slice(0, -1).join(', ') + ', then ' + bits.slice(-1) : bits.join(', then ')).replace(/, then (becoming|less windy)/g, ', $1');""")
_r("""                : cap(parts.map((p, i) => `${p.state} ${p.labels.length > 1 ? 'through the ' + p.labels[p.labels.length - 1].replace(/^in the |^after /, '') : p.labels[0]}`).join(', then '));""",
   """                : cap(parts.map((p, i) => `${p.state} ${p.labels.length > 1 ? 'through the ' + p.labels[p.labels.length - 1].replace(/^in the |^after /, '') : p.labels[0]}`).join(', then ')).replace(/, then (becoming|less windy)/g, ', $1');""")
_r("""(ni.cond.text.split(' · ')[0])} tonight with a low near""", """((() => { const ts = tonightSegs(ni); return windPhrase(ni.cond.text.split(' · ')[0], ts[0][1], ts[ts.length - 1][2]); })())} tonight with a low near""")
_r("""${cond.text}</span>${ni || !WET_ICONS.includes(cond.icon) ? '' : tstmTag(bb.thunder)}""", """${cond.text}</span>${ni || !WET_ICONS.includes(cond.icon) ? '' : tstmTag(bb.thunder)}${windTag(i, ni)}""")
_r("""(t => t != null && t >= 15 ? `<span class="text-[10px] font-mono text-amber-300"><i class="fa-solid fa-bolt"></i> ${Math.round(t)}%</span>` : '')(thunderAt(j))}""", """(t => t != null && t >= 15 ? `<span class="text-[10px] font-mono text-amber-300"><i class="fa-solid fa-bolt"></i> ${Math.round(t)}%</span>` : '')(thunderAt(j))}${j === s ? '' : hourWindTag(j)}""")
_r(""".rec-btn { background: none;""", """.wtag { display: inline-flex; align-items: center; gap: 4px; font: 700 10px/1.4 ui-monospace, Menlo, monospace; border-radius: 999px; padding: 1px 7px; margin-top: 2px; border: 1px solid; }
.wtag.wl1 { color: #cbd5e1; background: rgba(148,163,184,.10); border-color: rgba(148,163,184,.30); }
.wtag.wl2 { color: #fcd34d; background: rgba(245,158,11,.14); border-color: rgba(251,191,36,.45); }
.wtag.wl3 { color: #fda4af; background: rgba(244,63,94,.16); border-color: rgba(251,113,133,.55); }
.hwind { font: 10px ui-monospace, Menlo, monospace; margin-top: 2px; }
.hwind.wl1 { color: #94a3b8; } .hwind.wl2 { color: #fcd34d; } .hwind.wl3 { color: #fb7185; font-weight: 700; }
.rec-btn { background: none;""")

# ---- tropical cyclones (NHC / CPHC) in the alerts ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + open('/home/claude/tropical.js').read() + out[_a:]
_r("""                if (nwsOffice) loadRegional(token, lat, lon);""", """                if (nwsOffice) loadRegional(token, lat, lon);
                loadTropical(token, lat, lon);""")
_r("""            alerts.push(...spcAlerts());""", """            try { alerts.push(...tropicalAlerts()); } catch (e) {}
            alerts.push(...spcAlerts());""")

# notices hide themselves after a few seconds
_r("""            document.getElementById('toastMessage').innerText = msg;
            container.classList.remove('hidden');""", """            document.getElementById('toastMessage').innerText = msg;
            container.classList.remove('hidden');
            clearTimeout(window._toastT); window._toastT = setTimeout(closeToast, Math.min(12000, 4000 + String(msg).length * 45));""")

# one wind word when the same level spans several sky changes
assert out.count("            if (!parts.length) return null;") == 2
out = out.replace("            if (!parts.length) return null;", "            if (!parts.length) return null;\n            const wSum = windSummary(parts);")
_r("""            if (parts.length === 1) return `${cap(parts[0].state)} for the rest of today`;""", """            if (parts.length === 1) return `${cap(parts[0].state)} for the rest of today`;
            if (wSum) { const b2 = parts.map(p => `${p.state} ${p.labels.length > 1 ? p.labels.slice(0, -1).join(', ') + ' and ' + p.labels.slice(-1) : p.labels[0]}`);
                return cap(b2.length > 2 ? b2.slice(0, -1).join(', ') + ', then ' + b2.slice(-1) : b2.join(', then ')).replace(/, then (becoming|less windy)/g, ', $1') + '. ' + wSum.replace(/\.$/, ''); }""")
_r("""            return { text, wet: wetAll };""", """            return { text: wSum ? text + '. ' + wSum.replace(/\.$/, '') : text, wet: wetAll };""")

# ---- search placeholder fits the box: the full wording only when there is room ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        function fitSearchPh() {
            const i = document.getElementById('cityInput'); if (!i) return;
            const full = 'Search any city in the world', short = 'Search any city';
            const c = document.createElement('canvas').getContext('2d'), cs = getComputedStyle(i);
            c.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
            const room = i.clientWidth - (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0) - 4;
            i.placeholder = [full, short, 'Search a city', 'Search'].find(t => c.measureText(t).width <= room) || 'Search';
        }
        fitSearchPh();
        window.addEventListener('resize', fitSearchPh);
        try { document.fonts && document.fonts.ready.then(fitSearchPh); } catch (e) {}
""" + out[_a:]

# ---- header rail: section tabs first, city shortcuts behind a Places button (always shown on wide screens) ----
_a = out.index('        function restOfDayPhrase() {')
out = out[:_a] + """        function togglePlaces(force) {
            const c = document.getElementById('placeChips'), b = document.getElementById('placesToggle'), r = document.getElementById('navRail'); if (!c || !b) return;
            const open = force !== undefined ? force : !c.classList.contains('open');
            c.classList.toggle('open', open); b.setAttribute('aria-expanded', open);
            if (open && r) r.scrollTo({ left: Math.max(0, b.offsetLeft - 12), behavior: 'smooth' });
        }
        // picking a place closes the list again
        document.addEventListener('click', e => { if (e.target.closest && e.target.closest('#placeChips .chip')) setTimeout(() => togglePlaces(false), 150); });
        // a tab for a collapsed section opens it
        document.addEventListener('click', e => {
            const a = e.target.closest && e.target.closest('.navpill'); if (!a) return;
            try {
                const id = a.getAttribute('href').slice(1);
                const cfg = SECTIONS.find(s => s._panel && (s._panel.id === id || (s._panel.closest && s._panel.closest('#' + id) && s._panel.parentElement && s._panel.parentElement.id === id)));
                if (cfg && cfg._panel.classList.contains('collapsed')) setSecOpen(cfg, true, false);
            } catch (x) {}
        });
""" + out[_a:]

# ---- location header: the badge row is never shown, so it takes no space ----
_r("""                <div class="flex flex-wrap items-center gap-2">
                    <span id="nwsStatusBadge\"""", """                <div class="hidden">
                    <span id="nwsStatusBadge\"""")
