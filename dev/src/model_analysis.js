        // ---------- Model Analysis (collapsed by default): one place for models, weights, skill and spread ----------
        let maOpen = false;
        function _oldToggleModelAnalysis() {
            maOpen = !maOpen;
            const b = document.getElementById('maBody'), c = document.getElementById('maChevron'), t = document.getElementById('maToggle');
            if (b) b.classList.toggle('hidden', !maOpen);
            if (c) c.style.transform = maOpen ? 'rotate(180deg)' : '';
            if (t) t.setAttribute('aria-expanded', String(maOpen));
            if (maOpen) renderModelAnalysis();
        }
        function renderDomainWeightPanel() { if (maOpen) renderModelAnalysis(); }
        function renderModelComparisonTable() { if (maOpen) renderModelAnalysis(); }
        function renderModelAnalysis() {
            const el = document.getElementById('maBody');
            if (!el || !ensembleData) return;
            const n = v => v !== null && v !== undefined && !isNaN(v);
            const reg = modelRegion(), base = getModelWeights(), tw = weightsForDay(0), sk = todayModelSkill;
            const models = Object.keys(base);
            const dU = isImperial ? 1.8 : 1, u = isImperial ? '°F' : '°C';
            const stn = nwsObs ? nwsObs.stationId : null;
            const th = t => `<th class="p-2 text-[10px] uppercase tracking-wide text-slate-400 font-semibold whitespace-nowrap">${t}</th>`;
            const td = (t, c = '') => `<td class="p-2 whitespace-nowrap ${c}">${t}</td>`;

            // 1) today: every model's raw numbers, its weight, and how it is doing against the station
            const fullBB = bestBetResults[0] ? (typeof fullOf === 'function' ? fullOf(bestBetResults[0]) : bestBetResults[0]) : null;
            const rows = models.map(m => {
                const d0 = modelComparisonDay0[m];
                const r = sk && sk.res[m];
                const am = d0 ? adjustSnow(d0.precip, d0.snow, d0.max, d0.min) : null;
                return `<tr class="border-t border-white/5">
                    ${td(`<b class="text-slate-100">${MODEL_NAMES[m] || m}</b>`)}
                    ${td(`<b class="text-amber-300">${Math.round((tw[m] || 0) * 100)}%</b> <span class="text-slate-500">/ ${Math.round(base[m] * 100)}%</span>`)}
                    ${td(r ? `±${(r.rmse * dU).toFixed(1)}${u}` : '—', 'text-slate-300')}
                    ${td(r ? `<span class="${r.bias >= 0 ? 'text-rose-300' : 'text-sky-300'}">${r.bias >= 0 ? '+' : '−'}${Math.abs(r.bias * dU).toFixed(1)}${u}</span>` : '—')}
                    ${td(d0 && n(d0.max) ? formatTemp(d0.max) : '—', 'text-amber-200')}
                    ${td(d0 && n(d0.min) ? formatTemp(d0.min) : '—', 'text-sky-200')}
                    ${td(am ? formatPrecip(am.rain) : '—', 'text-indigo-200')}
                    ${td(am ? formatSnow(am.snow) : '—', 'text-cyan-200')}
                    ${td(d0 && n(d0.wind) ? formatSpeed(d0.wind) : '—')}
                    ${td(d0 && n(d0.gust) ? formatSpeed(d0.gust) : '—')}
                </tr>`;
            }).join('');
            const bbRow = fullBB ? `<tr class="border-t-2 border-amber-400/70 bg-amber-500/10">
                    ${td('<b class="text-amber-200">Best Bet</b>')}${td('')}${td('')}${td('')}
                    ${td(`<b>${formatTemp(fullBB.bestMax)}</b>`, 'text-amber-200')}${td(`<b>${formatTemp(fullBB.calMin ?? fullBB.bestMin)}</b>`, 'text-sky-200')}
                    ${td(`<b>${formatPrecip(fullBB.bestRain)}</b>`, 'text-indigo-200')}${td(`<b>${formatSnow(fullBB.bestSnow)}</b>`, 'text-cyan-200')}
                    ${td(`<b>${formatSpeed(fullBB.bestWind)}</b>`)}${td(`<b>${formatSpeed(fullBB.bestGust)}</b>`)}
                </tr>` : '';

            // 2) the next 12 days: each model's high / low and how far apart they are
            const md = modelDataRaw && modelDataRaw.daily ? modelDataRaw.daily : null;
            const days = bestBetResults.slice(0, 12);
            const dayRows = days.map((b, i) => {
                const hi = [], lo = [];
                const cells = models.map(m => {
                    const h = md && md[`temperature_2m_max_${m}`] ? md[`temperature_2m_max_${m}`][i] : null, l = md && md[`temperature_2m_min_${m}`] ? md[`temperature_2m_min_${m}`][i] : null;
                    if (n(h)) hi.push(h); if (n(l)) lo.push(l);
                    return td(n(h) || n(l) ? `<span class="text-amber-200">${n(h) ? Math.round(isImperial ? cToF(h) : h) : '–'}</span><span class="text-slate-500">/</span><span class="text-sky-200">${n(l) ? Math.round(isImperial ? cToF(l) : l) : '–'}</span>` : '<span class="text-slate-600">—</span>');
                }).join('');
                const sp = a => a.length >= 2 ? ((Math.max(...a) - Math.min(...a)) * dU).toFixed(1) : '—';
                const spH = hi.length >= 2 ? Math.max(...hi) - Math.min(...hi) : null;
                const conf = spH === null ? '' : spH < 1.5 ? 'text-emerald-300' : spH < 3 ? 'text-amber-300' : 'text-rose-300';
                const name = i === 0 ? 'Today' : new Date(b.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                return `<tr class="border-t border-white/5">${td(`<b class="text-slate-200">${name}</b>`)}${cells}
                    ${td(`<b class="text-amber-200">${Math.round(isImperial ? cToF(b.bestMax) : b.bestMax)}</b><span class="text-slate-500">/</span><b class="text-sky-200">${Math.round(isImperial ? cToF(b.bestMin) : b.bestMin)}</b>`)}
                    ${td(`<span class="${conf}">${sp(hi)}° / ${sp(lo)}°</span>`)}${td(`${b.nModels || hi.length}`, 'text-slate-400')}</tr>`;
            }).join('');

            // 3) how today's numbers were adjusted
            const rG = typeof windCalib === 'function' && nwsObsToday && nwsObsToday.length ? windCalib('wind_gusts_10m') : null;
            const rW = typeof windCalib === 'function' && nwsObsToday && nwsObsToday.length ? windCalib('wind_speed_10m') : null;
            const adj = typeof obsAdjustedHourly === 'function' ? obsAdjustedHourly() : null;
            const facts = [
                `<b>Region:</b> ${esc(reg.label)} — ${models.length} models blended (${models.map(m => MODEL_NAMES[m] || m).join(', ')}).`,
                sk ? `<b>Skill weighting:</b> today's weights are ${Math.round(sk.conf * 100)}% driven by how well each model has matched ${esc(stn || 'the station')} since midnight (hourly temperature error); tomorrow uses half of that adjustment, later days the base weights.` : `<b>Skill weighting:</b> not active — needs at least 4 hours of station observations today.`,
                stn ? `<b>Observation correction:</b> the hourly forecast starts from the latest ${esc(stn)} reading, and the model bias carries forward and fades over the following hours.` : `<b>Observation correction:</b> off — no nearby station observations.`,
                (rG !== null && rG !== 1) || (rW !== null && rW !== 1) ? `<b>Wind calibration:</b> over the last 12 h the station measured ${rW !== null ? Math.round(rW * 100) + '% of the modelled wind' : '—'} and ${rG !== null ? Math.round(rG * 100) + '% of the modelled gusts' : '—'}; near-term wind forecasts are scaled by that ratio, fading back to the models over about a day.` : `<b>Wind calibration:</b> models and measured wind agree (no scaling).`,
                bestBetResults[0] && bestBetResults[0].nwsBlendApplied ? `<b>NWS blend:</b> the official NWS point forecast is blended in at 40% for highs and lows.` : '',
                regionalInfo && regionalInfo.stations ? `<b>Regional observations:</b> ${regionalInfo.stations} nearby stations compared with the model at their own sites and elevations; low-level flow ${Math.round(regionalInfo.flow * 0.621)} mph. ${regionalAdj ? `Where the models are off upstream, that error is carried here over the next 9 hours (70%, fading); largest change ${(() => { const a = regionalAdj.adj.t; const m = a.reduce((x, y) => Math.abs(y) > Math.abs(x) ? y : x, 0); return `${m > 0 ? '+' : m < 0 ? '−' : ''}${Math.abs(m * dU).toFixed(1)}${u}`; })()}.` : 'Flow too light to carry errors in.'}` : `<b>Regional observations:</b> not available for this location.`,
                continuityInfo ? `<b>Continuity:</b> compared with the forecast shown ${continuityInfo.ageMin} min ago, ${continuityInfo.held} values were held (change too small to matter), ${continuityInfo.halved} moved halfway toward the new guidance, and ${continuityInfo.taken} large changes were taken as is.` : `<b>Continuity:</b> no recent forecast to compare with; this is a fresh forecast.`,
                `<b>Precipitation:</b> amounts are the weighted model blend; snow is converted from model water equivalent with a temperature-dependent snow-to-liquid ratio (8:1 near freezing up to 18:1 in deep cold).`
            ].filter(Boolean);

            el.innerHTML = `
                <div>
                    <div class="text-xs font-semibold text-slate-300 mb-2">Today · each model, its weight, and its error against ${esc(stn || 'observations')}</div>
                    <div class="overflow-x-auto -mx-1 px-1"><table class="w-full text-xs font-mono text-slate-300">
                        <thead><tr>${th('Model')}${th('Weight now / base')}${th('Typical error')}${th('Running bias')}${th('High')}${th('Low')}${th('Rain')}${th('Snow')}${th('Wind')}${th('Gust')}</tr></thead>
                        <tbody>${rows}${bbRow}</tbody></table></div>
                </div>
                <div>
                    <div class="text-xs font-semibold text-slate-300 mb-2">Next 12 days · model highs / lows (${u}) and spread</div>
                    <div class="overflow-x-auto -mx-1 px-1"><table class="w-full text-xs font-mono text-slate-300">
                        <thead><tr>${th('Day')}${models.map(m => th(MODEL_NAMES[m] || m)).join('')}${th('Best Bet')}${th('Spread H / L')}${th('Models')}</tr></thead>
                        <tbody>${dayRows}</tbody></table></div>
                    <div class="text-[11px] text-slate-400 mt-2">Spread under 1.5° = high agreement (green), under 3° = moderate (amber), above = low (red). Some regional models stop after a few days.</div>
                </div>
                <div>
                    <div class="text-xs font-semibold text-slate-300 mb-2">Method</div>
                    <ul class="text-xs text-slate-300 space-y-1.5 leading-relaxed list-disc pl-4">${facts.map(f => `<li>${f}</li>`).join('')}</ul>
                </div>
                <div>
                    <div class="text-xs font-semibold text-slate-300 mb-2">Learning from past forecasts: daily highs, lows and rain</div>
                    ${typeof learningHTML === 'function' ? learningHTML() : ''}
                </div>
                <div>
                    <div class="text-xs font-semibold text-slate-300 mb-2">Hour by hour: temperature, dewpoint, wind, cloud and rain</div>
                    ${typeof hourlyLearningHTML === 'function' ? hourlyLearningHTML() : ''}
                </div>`;
        }
