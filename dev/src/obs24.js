        // ---------- Past 24 hours: one station report per hour (the routine hourly report when there is one) ----------
        function toggleObs24() {
            const w = document.getElementById('obs24Wrap'), b = document.getElementById('obs24Toggle');
            const open = w.classList.toggle('hidden') === false;
            b.setAttribute('aria-expanded', String(open)); b.classList.toggle('open', open);
            document.getElementById('obs24Hint').innerText = open ? 'Hide' : 'Show hourly observations';
            if (open) renderObs24();
        }
        function renderObs24() {
            const w = document.getElementById('obs24Wrap');
            if (!w || w.classList.contains('hidden')) return;
            const n = v => v !== null && v !== undefined && !isNaN(v);
            const val = q => q && n(q.value) ? q.value : null;
            const kmh = q => { const v = val(q); return v === null ? null : (q.unitCode && /m_s/.test(q.unitCode) ? v * 3.6 : v); };
            const tz = ensembleData && ensembleData.timezone, now = Date.now();
            const obs = (nwsObsToday || []).filter(o => o && o.timestamp && o.temperature && n(o.temperature.value) && now - Date.parse(o.timestamp) <= 24.5 * 36e5);
            if (!obs.length) { w.innerHTML = '<div class="text-xs text-slate-400 p-2">No station reports in the last 24 hours.</div>'; return; }
            // US airport reports: the routine hourly METAR carries the sea-level pressure remark (SLPnnn), a special (SPECI)
            // does not, and the automated 5-minute readings have no report text. (Raw text from the NWS has no METAR/SPECI word.)
            const rawOf = o => String(o.rawMessage || '').trim();
            const hasSLP = r => /\bSLP(\d{3}|NO)\b/.test(r);
            const slpMode = obs.some(o => hasSLP(rawOf(o)));
            const byHour = {};
            obs.forEach(o => {
                const t = Date.parse(o.timestamp), mins = new Date(t).getUTCMinutes(), k = Math.floor(t / 36e5), r = rawOf(o);
                const score = /^METAR\b/.test(r) || (slpMode && hasSLP(r)) ? 1000 + mins : slpMode ? -1 : mins >= 45 ? 100 + mins : mins;
                if (score < 0) return;
                if (!byHour[k] || score > byHour[k].score) byHour[k] = { o, score, t };
            });
            const routine = new Set(Object.values(byHour).map(x => x.o));
            const isSpeci = o => { const r = rawOf(o); return /^SPECI\b/.test(r) || (slpMode && r && !hasSLP(r) && !/^METAR\b/.test(r)); };
            const wetOf = o => /rain|drizzle|snow|thunder|shower|sleet|freezing|ice|hail/i.test(o.textDescription || '') || (Array.isArray(o.presentWeather) && o.presentWeather.some(w => /(RA|DZ|SN|TS|PL|GR|GS|SG|UP)/.test(w.rawString || '')));
            const visBand = o => { const v = o.visibility && n(o.visibility.value) ? o.visibility.value : null; return v === null ? null : v < 1609 ? 0 : v < 4828 ? 1 : 2; };
            const chron = obs.map(o => ({ o, t: Date.parse(o.timestamp) })).sort((a, b) => a.t - b.t);
            const keep = []; let prev = null, lastExtra = 0;
            chron.forEach(r => {
                let show = routine.has(r.o), special = false;
                if (!show && isSpeci(r.o)) { show = true; special = true; }
                else if (!show && !rawOf(r.o) && prev && r.t - lastExtra >= 15 * 60e3) {
                    // automated reading with no report: only a significant change (precipitation start/stop, thunder, gust 25 mph+, visibility drop)
                    const g = kmh(r.o.windGust);
                    const sig = wetOf(r.o) !== wetOf(prev) || (/thunder/i.test(r.o.textDescription || '') && !/thunder/i.test(prev.textDescription || ''))
                        || (g !== null && g >= 40) || (visBand(r.o) !== null && visBand(prev) !== null && visBand(r.o) < visBand(prev));
                    if (sig) { show = true; special = true; lastExtra = r.t; }
                }
                if (show) keep.push({ ...r, special });
                prev = r.o;
            });
            const seen = new Set(), rows = keep.sort((a, b) => b.t - a.t).filter(r => { const k = Math.round(r.t / 120000); if (seen.has(k)) return false; seen.add(k); return true; });
            const td = (x, c = '') => `<td class="p-2 whitespace-nowrap ${c}">${x}</td>`;
            const th = x => `<th class="p-2 whitespace-nowrap">${x}</th>`;
            const body = rows.map(({ o, t, special }) => {
                const time = new Date(t).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: tz });
                const T = val(o.temperature), D = val(o.dewpoint), RH = val(o.relativeHumidity);
                const ws = kmh(o.windSpeed), wg = kmh(o.windGust), wd = val(o.windDirection);
                const wind = ws === null ? '--' : ws < 1 ? 'Calm' : `${n(wd) ? compass(wd) + ' ' : ''}${formatSpeed(ws)}`;
                const vis = val(o.visibility), visTxt = vis === null ? '--' : isImperial ? `${(vis / 1609.34) >= 9.95 ? '10' : (vis / 1609.34).toFixed(vis / 1609.34 < 3 ? 1 : 0)} mi` : `${(vis / 1000).toFixed(vis < 5000 ? 1 : 0)} km`;
                const slp = val(o.seaLevelPressure), alt = val(o.barometricPressure), pr = n(slp) ? slp / 100 : n(alt) ? alt / 100 : null;
                const p1 = val(o.precipitationLastHour);
                const day = (() => { const d = ensembleData && ensembleData.daily; if (!d) return true; const ds = new Date(t).toLocaleDateString('en-CA', { timeZone: tz }), i = d.time.indexOf(ds); return i < 0 || !d.sunrise[i] ? true : (t >= Date.parse(d.sunrise[i] + ':00Z') - (ensembleData.utc_offset_seconds || 0) * 1000 && t < Date.parse(d.sunset[i] + ':00Z') - (ensembleData.utc_offset_seconds || 0) * 1000); })();
                const sky = o.textDescription ? skyWording(o.textDescription, day) : '--';
                const wet = /rain|drizzle|snow|thunder|shower|sleet|freezing|ice/i.test(sky);
                return `<tr class="border-t border-white/5${special ? ' bg-sky-950/30' : ''}">${td(time + (special ? ' <span class="text-[9px] text-sky-300 font-sans font-semibold ml-1">SPECIAL</span>' : ''), 'text-slate-200')}${td(n(T) ? formatTemp(T) : '--', 'text-amber-200')}${td(n(D) ? formatTemp(D) : '--', 'text-emerald-200')}${td(n(RH) ? Math.round(RH) + '%' : '--')}${td(wind)}${td(n(wg) ? formatSpeed(wg) : '')}${td(esc(sky), wet ? 'text-sky-300' : '')}${td(visTxt)}${td(pr !== null ? formatPressure(pr) : '--')}${td(n(p1) ? formatPrecip(p1) : '', p1 > 0 ? 'text-sky-300' : '')}</tr>`;
            }).join('');
            const sid = nwsObs && nwsObs.stationId ? nwsObs.stationId : '';
            w.innerHTML = `<table class="dclim w-full text-xs text-left text-slate-300 font-mono"><thead class="text-[11px] text-slate-400 uppercase bg-slate-800/80"><tr>${th('Time')}${th('Temp')}${th('Dewpt')}${th('RH')}${th('Wind')}${th('Gust')}${th('Sky / weather')}${th('Vis')}${th('Pressure')}${th('Precip')}</tr></thead><tbody>${body}</tbody></table>
                <div class="text-[11px] text-slate-400 mt-2">${esc(sid)} reports, newest first. Specials are extra reports issued between the hourly ones for significant changes. Hourly precipitation is for the hour ending at that time; a special's is since the last hourly report.</div>`;
        }
