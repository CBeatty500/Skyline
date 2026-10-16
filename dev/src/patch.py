import re
src = open('/mnt/user-data/uploads/the_weather-8.html', encoding='utf-8').read()

def rep(old, new):
    global src
    assert src.count(old) == 1, ("not unique/found", old[:60], src.count(old))
    src = src.replace(old, new)

def between(start, end, new):
    global src
    assert src.count(start) == 1, ("start", start)
    a = src.index(start)
    b = src.index(end, a)
    src = src[:a] + new + src[b:]

# ---------- Head / CSS / small HTML fixes ----------
rep('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>')
rep('''            background-color: #0b0f19;
            color: #f3f4f6;
        }''', '''            background: radial-gradient(1100px 560px at 8% -10%, rgba(59,130,246,.20), transparent 60%),
                        radial-gradient(900px 480px at 100% 0%, rgba(245,158,11,.10), transparent 55%), #0b0f19;
            background-attachment: fixed;
            color: #f3f4f6;
        }
        .glass-panel { box-shadow: 0 12px 32px -14px rgba(0,0,0,.65); }
        #dashboardContent > * { animation: fadeUp .5s ease both; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
        #hourlyContainer { scroll-snap-type: x proximity; }
        #hourlyContainer > div { scroll-snap-align: start; }
        @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }''')
rep('onclick="fetchForecastData()" class="bg-gradient-to-r', 'onclick="searchAndFetch()" class="bg-gradient-to-r')
rep('<i class="fa-solid fa-satellite mr-1"></i> Live Observation', '<i class="fa-solid fa-satellite mr-1"></i> <span id="currentObsSource">Current Conditions</span>')
rep('Departure: <span id="climateAnomalyText">', 'Today vs Normal: <span id="climateAnomalyText">')
rep('<i class="fa-solid fa-mountain text-indigo-400"></i> Elevation Lapse Correction', '<i class="fa-solid fa-mountain text-indigo-400"></i> Terrain Downscaling')
rep('<span>Grid Model Height:</span>', '<span>Site Elevation:</span>')
rep('<span>City Altitude:</span>', '<span>Elevation Data:</span>')
rep('<span>Lapse Rate Delta (-6.5°C/km):</span>', '<span>Temp Correction:</span>')
rep('Hourly Best Bet Curve vs Raw Models (24 Hours)', 'Hourly Temperature (Next 24 Hours)')
rep('font-mono">Ensemble Spread</span>', 'font-mono">Best-Match Model</span>')
rep('''<li><strong>Warming Slope ($m$):</strong> Calculated via $\\frac{\\sum(x - \\bar{x})(y - \\bar{y})}{\\sum(x - \\bar{x})^2}$.</li>''',
    '''<li><strong>Warming Slope:</strong> Σ(x − x̄)(y − ȳ) / Σ(x − x̄)², fitted to complete calendar years only (partial years are excluded to avoid seasonal bias).</li>''')
rep('Linear Fit $R^2$:', 'Linear Fit R²:')
rep('<span>Standard Error: <strong', '<span>Residual Std Dev: <strong')
rep('Calculated directly', 'Calculated directly') if False else None

# ---------- State + helpers ----------
rep('let geminiApiKey = "";', 'let geminiApiKey = "";\n        let nwsObs = null, nwsAlerts = [], climIndex = null, fetchToken = 0;')
rep('''if (dpF < 50) return "Comfortable";
            if (dpF < 55) return "Dry";''', '''if (dpF < 50) return "Dry";
            if (dpF < 55) return "Comfortable";''')
rep('if (ensembleData) renderDashboard();\n        }', 'if (ensembleData) { renderDashboard(); if (!geminiApiKey) fetchAISynopticDiscussion(); }\n        }')
rep('let searchTimeout = null;', '''let searchTimeout = null;
        cityInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { clearTimeout(searchTimeout); searchAndFetch(); }
        });''')

# ---------- Fetch + best bet ----------
between('// Main Data Fetcher', '// Render Dashboard Controls & Layout', r'''// Search-then-fetch: typing a city and pressing Fetch/Enter now actually loads that city
        async function searchAndFetch() {
            const q = cityInput.value.trim();
            if (q && q !== currentLoc.name) {
                try {
                    const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=1&language=en&format=json`);
                    const data = await res.json();
                    if (!data.results || !data.results[0]) { showToast(`No location found for "${q}".`); return; }
                    const r = data.results[0];
                    currentLoc = { name: [r.name, r.admin1, r.country].filter(Boolean).join(', '), lat: r.latitude, lon: r.longitude, ele: r.elevation || 0 };
                    cityInput.value = currentLoc.name;
                } catch (e) { showToast("Location search failed. Check your connection."); return; }
            }
            autocompleteResults.classList.add('hidden');
            fetchForecastData();
        }

        // NWS: official forecast, latest station observation and active alerts (US only; never throws)
        async function fetchNWS(lat, lon) {
            const out = { forecast: null, obs: null, alerts: [] };
            try {
                const p = await (await fetch(`https://api.weather.gov/points/${lat},${lon}`)).json();
                const props = p && p.properties;
                if (!props || !props.forecast) return out;
                await Promise.all([
                    fetch(props.forecast).then(r => r.ok ? r.json() : null).then(j => { out.forecast = j; }).catch(() => {}),
                    fetch(`https://api.weather.gov/alerts/active?point=${lat},${lon}`).then(r => r.ok ? r.json() : null)
                        .then(j => { if (j && j.features) out.alerts = j.features.map(f => f.properties); }).catch(() => {}),
                    (async () => {
                        const sl = await (await fetch(props.observationStations)).json();
                        for (const f of (sl.features || []).slice(0, 3)) {
                            const o = await (await fetch(`https://api.weather.gov/stations/${f.properties.stationIdentifier}/observations/latest`)).json();
                            const v = o && o.properties;
                            if (v && v.temperature && v.temperature.value != null && v.timestamp && (Date.now() - new Date(v.timestamp)) < 3 * 3600e3) {
                                out.obs = { ...v, stationId: f.properties.stationIdentifier };
                                break;
                            }
                        }
                    })().catch(() => {})
                ]);
            } catch (e) { console.warn("NWS unavailable:", e); }
            return out;
        }

        async function fetchForecastData() {
            const token = ++fetchToken;
            const btnText = document.getElementById('generateBtnText');
            const loader = document.getElementById('generateLoader');
            btnText.innerText = "Loading Data...";
            loader.classList.remove('hidden');
            closeToast();

            const lat = currentLoc.lat.toFixed(4), lon = currentLoc.lon.toFixed(4);
            const getJSON = async (url) => { const r = await fetch(url); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); };

            try {
                const baseUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,is_day,precipitation,weather_code,pressure_msl,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,uv_index,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max&timezone=auto&forecast_days=7`;
                const modelsUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,wind_speed_10m_max,wind_gusts_10m_max&models=ecmwf_ifs025,gfs_seamless,icon_seamless,gem_seamless&timezone=auto&forecast_days=7`;
                const endStr = new Date(Date.now() - 6 * 864e5).toISOString().split('T')[0]; // ERA5 archive lag
                const histUrl = `https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=1940-01-01&end_date=${endStr}&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean&timezone=auto`;
                const inUS = currentLoc.lat >= 17 && currentLoc.lat <= 72 && currentLoc.lon >= -180 && currentLoc.lon <= -65;

                const baseP = getJSON(baseUrl);
                const modelsP = getJSON(modelsUrl).catch(() => null);
                const nwsP = inUS ? fetchNWS(lat, lon) : Promise.resolve({ forecast: null, obs: null, alerts: [] });
                const histP = getJSON(histUrl).catch(() => null);

                const base = await baseP;
                const [models, nws, hist] = await Promise.all([modelsP, nwsP, histP]);
                if (token !== fetchToken) return; // a newer request superseded this one

                ensembleData = base;
                modelDataRaw = models;
                nwsForecastData = nws.forecast;
                nwsObs = nws.obs;
                nwsAlerts = nws.alerts || [];
                historicalData = (hist && hist.daily && hist.daily.time && hist.daily.time.length > 0) ? hist : null;
                if (ensembleData.elevation !== undefined) currentLoc.ele = ensembleData.elevation;
                buildClimIndex();

                document.getElementById('statusMessage').classList.add('hidden');
                document.getElementById('dashboardContent').classList.remove('hidden');

                computeBestBetPredictions();
                renderDashboard();
                fetchAISynopticDiscussion();
            } catch (err) {
                console.error("Fetch operational data failed:", err);
                if (token === fetchToken) showToast("Error retrieving forecast data for this location. Please try again.");
            } finally {
                if (token === fetchToken) {
                    btnText.innerText = "Fetch Weather";
                    loader.classList.add('hidden');
                }
            }
        }

        function buildClimIndex() {
            climIndex = null;
            if (!historicalData) return;
            const { time, temperature_2m_max: mx, temperature_2m_min: mn } = historicalData.daily;
            const ok = v => (v !== null && v !== undefined && !isNaN(v)) ? v : null;
            const idx = {};
            for (let i = 0; i < time.length; i++) {
                if (!time[i]) continue;
                (idx[time[i].substring(5, 10)] ||= []).push([parseInt(time[i].substring(0, 4)), ok(mx[i]), ok(mn[i])]);
            }
            climIndex = idx;
        }

        // Index of the current hour inside the hourly arrays (so "next 24h" really starts now)
        function hourlyStart() {
            const h = ensembleData && ensembleData.hourly, c = ensembleData && ensembleData.current;
            if (!h || !c || !c.time) return 0;
            const i = h.time.findIndex(t => t >= c.time.substring(0, 13) + ':00');
            return Math.max(0, Math.min(i === -1 ? 0 : i, h.time.length - 24));
        }

        // Merge NWS station observation (when available) over Open-Meteo model analysis
        function getCurrentConditions() {
            const c = ensembleData && ensembleData.current;
            if (!c) return null;
            const tzA = ensembleData.timezone_abbreviation || '';
            const pick = (a, b) => (a !== null && a !== undefined && !isNaN(a)) ? a : b;
            const num = v => (v && v.value !== null && v.value !== undefined) ? v.value : null;
            const r = {
                sourceLabel: 'Model Analysis',
                timeLabel: `As of ${new Date(c.time).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} ${tzA}`,
                temp: c.temperature_2m, apparent: c.apparent_temperature, dew: c.dew_point_2m, rh: c.relative_humidity_2m,
                wind: c.wind_speed_10m, pressure: c.pressure_msl, code: c.weather_code, isDay: c.is_day, text: null
            };
            const o = nwsObs;
            if (o) {
                r.temp = num(o.temperature);
                r.dew = pick(num(o.dewpoint), r.dew);
                r.rh = pick(num(o.relativeHumidity), r.rh);
                let w = num(o.windSpeed);
                if (w !== null && o.windSpeed.unitCode && o.windSpeed.unitCode.includes('m_s')) w *= 3.6;
                r.wind = pick(w, r.wind);
                const p = num(o.seaLevelPressure);
                r.pressure = p !== null ? p / 100 : r.pressure;
                r.apparent = pick(num(o.heatIndex), pick(num(o.windChill), r.temp + (c.apparent_temperature - c.temperature_2m)));
                r.text = o.textDescription || null;
                r.sourceLabel = `Observed · ${o.stationId}`;
                r.timeLabel = `As of ${new Date(o.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', timeZone: ensembleData.timezone })} ${tzA}`;
            }
            return r;
        }

        function conditionFromText(t, isDay) {
            const s = t.toLowerCase(), mk = (icon, color) => ({ text: t, icon, color });
            if (/thunder/.test(s)) return mk('fa-bolt', 'text-amber-400');
            if (/snow|sleet|flurr|freezing|ice pellets/.test(s)) return mk('fa-snowflake', 'text-teal-200');
            if (/rain|shower|drizzle/.test(s)) return mk('fa-cloud-showers-heavy', 'text-blue-400');
            if (/fog|mist|haze|smoke/.test(s)) return mk('fa-smog', 'text-slate-400');
            if (/overcast/.test(s)) return mk('fa-cloud', 'text-slate-400');
            if (/cloud/.test(s)) return mk(isDay ? 'fa-cloud-sun' : 'fa-cloud-moon', 'text-blue-300');
            if (/clear|fair|sunny/.test(s)) return isDay ? mk('fa-sun', 'text-amber-400') : mk('fa-moon', 'text-indigo-300');
            return null;
        }

        function getModelWeights() {
            const na = currentLoc.lat >= 15 && currentLoc.lat <= 75 && currentLoc.lon >= -170 && currentLoc.lon <= -50;
            return na ? { ecmwf_ifs025: 0.35, gfs_seamless: 0.35, icon_seamless: 0.15, gem_seamless: 0.15 }
                      : { ecmwf_ifs025: 0.40, gfs_seamless: 0.30, icon_seamless: 0.15, gem_seamless: 0.15 };
        }

        function modelSpread() {
            const v = Object.values(modelComparisonDay0).map(m => m.max).filter(x => x !== null && x !== undefined);
            return v.length >= 2 ? Math.max(...v) - Math.min(...v) : null;
        }

        function updateConfidenceBadge() {
            const el = document.getElementById('bestBetConfidenceBadge');
            const sp = modelSpread();
            if (sp === null) { el.innerText = 'Single-Model Data'; el.className = 'text-xs bg-slate-500/20 text-slate-300 border border-slate-500/40 px-2.5 py-1 rounded font-medium'; return; }
            const [t, c] = sp < 1.5 ? ['High Model Consensus', 'emerald'] : sp < 3 ? ['Moderate Consensus', 'amber'] : ['Low Consensus', 'rose'];
            el.innerText = `${t} · ${(isImperial ? sp * 1.8 : sp).toFixed(1)}° spread`;
            el.className = `text-xs bg-${c}-500/20 text-${c}-300 border border-${c}-500/40 px-2.5 py-1 rounded font-medium`;
        }

        // Skill-Weighted Best Bet Engine
        function computeBestBetPredictions() {
            bestBetResults = [];
            modelComparisonDay0 = {};
            if (!ensembleData || !ensembleData.daily) return;

            const d = ensembleData.daily;
            const md = (modelDataRaw && modelDataRaw.daily) ? modelDataRaw.daily : {};
            const weights = getModelWeights();
            const vars = { max: 'temperature_2m_max', min: 'temperature_2m_min', precip: 'precipitation_sum', snow: 'snowfall_sum', wind: 'wind_speed_10m_max', gust: 'wind_gusts_10m_max' };
            const val = (arr, i) => (arr && arr[i] !== undefined && arr[i] !== null && !isNaN(arr[i])) ? arr[i] : null;
            const periods = nwsForecastData && nwsForecastData.properties && nwsForecastData.properties.periods;
            const nwsC = p => p.temperatureUnit === 'C' ? p.temperature : fToC(p.temperature); // NWS reports °F
            const cc = getCurrentConditions();
            const n = Math.min(5, d.time.length);

            for (let i = 0; i < n; i++) {
                const acc = {};
                Object.keys(vars).forEach(k => acc[k] = { s: 0, w: 0 });
                Object.keys(weights).forEach(m => {
                    const row = {};
                    Object.keys(vars).forEach(k => {
                        const v = val(md[`${vars[k]}_${m}`], i);
                        row[k] = v;
                        if (v !== null) { acc[k].s += v * weights[m]; acc[k].w += weights[m]; }
                    });
                    if (i === 0 && Object.values(row).some(v => v !== null)) modelComparisonDay0[m] = row;
                });
                const pick = (k) => acc[k].w > 0 ? acc[k].s / acc[k].w : (val(d[vars[k]], i) ?? 0);
                let bestMax = pick('max'), bestMin = pick('min');
                const bestPrecip = pick('precip'), bestSnow = pick('snow'), bestWind = pick('wind'), bestGust = pick('gust');

                // Blend official NWS highs/lows by matching calendar dates (never mixes up days)
                let nwsBlendApplied = false;
                if (periods) {
                    const day = d.time[i];
                    const dayP = periods.find(p => p.isDaytime && p.startTime.substring(0, 10) === day && p.temperature != null);
                    const nightP = periods.find(p => !p.isDaytime && p.endTime.substring(0, 10) === day && p.startTime.substring(0, 10) !== day && p.temperature != null);
                    if (dayP) { bestMax = bestMax * 0.6 + nwsC(dayP) * 0.4; nwsBlendApplied = true; }
                    if (nightP) { bestMin = bestMin * 0.6 + nwsC(nightP) * 0.4; nwsBlendApplied = true; }
                }

                // Today's range must include what is already observed
                if (i === 0 && cc && cc.temp !== null && cc.temp !== undefined) {
                    bestMax = Math.max(bestMax, cc.temp);
                    bestMin = Math.min(bestMin, cc.temp);
                }

                bestBetResults.push({
                    date: d.time[i], bestMax, bestMin, bestPrecip, bestSnow, bestWind, bestGust,
                    weatherCode: d.weather_code ? d.weather_code[i] : 0,
                    precipProb: d.precipitation_probability_max && d.precipitation_probability_max[i] != null ? d.precipitation_probability_max[i] : 0,
                    nwsBlendApplied
                });
            }
        }

''')

# ---------- Current conditions render ----------
between('// Current Conditions', '// Best Bet Today Headline Card', r'''// Current Conditions
            const cc = getCurrentConditions();
            if (cc) {
                const $ = id => document.getElementById(id);
                $('currentTempDisplay').innerText = formatTemp(cc.temp);
                $('currentApparentTemp').innerText = formatTemp(cc.apparent);
                $('currentDewPoint').innerText = formatTemp(cc.dew);
                $('currentDewPointCategory').innerText = getDewPointCategory(cc.dew);
                $('currentHumidity').innerText = (cc.rh !== null && cc.rh !== undefined) ? `${Math.round(cc.rh)}%` : '--';
                $('currentWind').innerText = formatSpeed(cc.wind);
                $('currentPressure').innerText = formatPressure(cc.pressure);

                let uv = '--';
                const hh = ensembleData.hourly;
                if (hh && hh.uv_index) {
                    const v = hh.uv_index[hourlyStart()];
                    if (v !== null && v !== undefined) uv = `${v.toFixed(1)} · ${v < 3 ? 'Low' : v < 6 ? 'Moderate' : v < 8 ? 'High' : v < 11 ? 'Very High' : 'Extreme'}`;
                }
                $('currentUV').innerText = uv;
                $('currentObsSource').innerText = cc.sourceLabel;
                $('currentObsTime').innerText = cc.timeLabel;

                const cond = (cc.text && conditionFromText(cc.text, cc.isDay)) || getWeatherCondition(cc.code, cc.isDay);
                $('currentWeatherConditionText').innerText = cc.text || cond.text;
                $('currentWeatherIcon').className = `fa-solid ${cond.icon} text-5xl ${cond.color}`;
            }
            updateConfidenceBadge();

            ''')

# ---------- Hourly slider + domain panel ----------
between('// Hourly Slider', '// Model Comparison Table', r'''// Hourly Slider (starts at the current hour)
        function renderHourlySlider() {
            if (!ensembleData || !ensembleData.hourly) return;
            const h = ensembleData.hourly;
            const container = document.getElementById('hourlyContainer');
            const s = hourlyStart();
            let html = '';
            for (let j = s; j < s + 24 && j < h.time.length; j++) {
                const t = new Date(h.time[j]);
                const hr = t.getHours();
                const label = j === s ? 'Now' : `${hr === 0 ? t.toLocaleDateString('en-US', { weekday: 'short' }) + ' ' : ''}${t.toLocaleTimeString([], { hour: 'numeric', hour12: true })}`;
                const isDay = h.is_day ? h.is_day[j] : (hr > 6 && hr < 20 ? 1 : 0);
                const cond = getWeatherCondition(h.weather_code[j], isDay);
                const pp = h.precipitation_probability ? h.precipitation_probability[j] : null;
                html += `
                    <div class="bg-slate-900/80 border ${j === s ? 'border-blue-500/60' : 'border-slate-800'} p-3 rounded-xl min-w-[85px] text-center flex flex-col justify-between shrink-0 shadow-md">
                        <span class="text-[11px] font-medium text-slate-400 font-mono">${label}</span>
                        <i class="fa-solid ${cond.icon} text-xl my-2 ${cond.color}"></i>
                        <span class="text-xs font-bold text-white font-mono">${formatTemp(h.temperature_2m[j])}</span>
                        <span class="text-[10px] font-mono mt-1 ${pp >= 10 ? 'text-blue-300' : 'text-transparent'}"><i class="fa-solid fa-droplet"></i> ${pp !== null ? pp : 0}%</span>
                    </div>`;
            }
            container.innerHTML = html;
        }

        // Domain & Elevation Panel (weights now reflect what the engine really uses)
        function renderDomainWeightPanel() {
            const w = getModelWeights();
            const na = w.gfs_seamless === 0.35;
            document.getElementById('modelElevVal').innerText = `${Math.round(currentLoc.ele || 0)} m`;
            document.getElementById('actualElevVal').innerText = '90 m DEM';
            document.getElementById('lapseRateBiasVal').innerText = 'Applied by API';
            document.getElementById('regionBadge').innerText = na ? 'North America' : 'Global';
            const names = { ecmwf_ifs025: 'ECMWF IFS (0.25°)', gfs_seamless: 'NOAA GFS Seamless', icon_seamless: 'DWD ICON Seamless', gem_seamless: 'Environment Canada GEM' };
            document.getElementById('weightsContainer').innerHTML = Object.keys(w).map(m => `
                <div class="flex justify-between items-center p-2 rounded bg-slate-900/80 border border-slate-800">
                    <span class="font-bold text-blue-300">${names[m]}</span>
                    <span class="font-mono text-amber-400 font-bold">${Math.round(w[m] * 100)}%</span>
                </div>`).join('');
        }

        ''')

# ---------- Alerts, AI discussion, history helpers, climate analytics ----------
between('// Active Alerts Engine', '// OLS Math', r'''function esc(s) {
            return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
        }

        // Alerts: official NWS alerts (US) + clearly-labelled model-derived flags
        function renderActiveAlerts() {
            const container = document.getElementById('alertsList');
            const badge = document.getElementById('alertCountBadge');
            const alerts = nwsAlerts.map(a => ({
                type: (a.severity === 'Extreme' || a.severity === 'Severe') ? 'danger' : 'warning',
                title: a.event, tag: 'NWS Official',
                text: (a.headline || '') + (a.areaDesc ? ` — ${a.areaDesc}` : '')
            }));
            if (bestBetResults.length > 0) {
                const bb = bestBetResults[0];
                const m = 'Model-derived';
                if (bb.bestMax >= 35) alerts.push({ type: 'danger', tag: m, title: 'Extreme Heat Potential', text: `High near ${formatTemp(bb.bestMax)}. Stay hydrated and limit outdoor exertion.` });
                if (bb.bestMin <= -5) alerts.push({ type: 'warning', tag: m, title: 'Hard Freeze Potential', text: `Low near ${formatTemp(bb.bestMin)}. Protect sensitive plants and exposed plumbing.` });
                if (bb.bestGust >= 60) alerts.push({ type: 'warning', tag: m, title: 'Strong Wind Potential', text: `Peak gusts near ${formatSpeed(bb.bestGust)}. Secure loose items.` });
                if (bb.bestPrecip >= 25) alerts.push({ type: 'warning', tag: m, title: 'Heavy Rain Potential', text: `About ${formatPrecip(bb.bestPrecip)} expected today.` });
                if (bb.bestSnow >= 10) alerts.push({ type: 'warning', tag: m, title: 'Significant Snow Potential', text: `About ${formatSnow(bb.bestSnow)} expected today.` });
            }
            badge.innerText = `${alerts.length} Active`;
            container.innerHTML = alerts.length === 0
                ? `<div class="text-xs text-slate-400 italic py-1"><i class="fa-solid fa-circle-check text-emerald-400 mr-1.5"></i> No active watches or warnings for this location${nwsAlerts.length === 0 && !nwsForecastData ? ' (official NWS alerts cover the US only)' : ''}.</div>`
                : alerts.map(a => `
                    <div class="p-3 rounded-xl border ${a.type === 'danger' ? 'bg-rose-950/40 border-rose-500/50 text-rose-200' : 'bg-amber-950/40 border-amber-500/50 text-amber-200'} text-xs">
                        <strong class="font-bold text-sm block mb-1"><i class="fa-solid fa-triangle-exclamation mr-1.5"></i>${esc(a.title)} <span class="ml-1 text-[10px] font-mono font-normal opacity-70">[${a.tag}]</span></strong>
                        <p class="leading-relaxed opacity-90">${esc(a.text.slice(0, 320))}</p>
                    </div>`).join('');
        }

        // Data-driven discussion (built only from real numbers; no invented synoptic features)
        function buildLocalDiscussion() {
            const bb = bestBetResults;
            if (!bb.length) return '<p class="text-slate-400 italic">No forecast data available.</p>';
            const t = bb[0], cc = getCurrentConditions(), st = getHistoricalStatsForDate(t.date);
            const dayName = b => new Date(b.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long' });
            let now = '';
            if (cc) {
                const cond = (cc.text || getWeatherCondition(cc.code, cc.isDay).text).toLowerCase();
                now = `Currently <strong>${formatTemp(cc.temp)}</strong> (feels like ${formatTemp(cc.apparent)}) and ${cond}, with wind near ${formatSpeed(cc.wind)}, dew point ${formatTemp(cc.dew)} and humidity ${cc.rh != null ? Math.round(cc.rh) : '--'}%.`;
            }
            const dep = st && st.normMax !== null ? t.bestMax - st.normMax : null;
            const depTxt = dep === null ? '' : Math.abs(dep) < 1 ? ', close to the seasonal normal'
                : `, ${formatTempDiff(Math.abs(dep), 1).replace('+', '')} ${dep > 0 ? 'above' : 'below'} the 1991–2020 normal high of ${formatTemp(st.normMax)}`;
            const precipTxt = t.bestPrecip >= 0.2
                ? `Expect about ${formatPrecip(t.bestPrecip)} of precipitation${t.bestSnow >= 0.2 ? ` including ${formatSnow(t.bestSnow)} of snow` : ''} (${t.precipProb}% chance).`
                : `Little or no precipitation is expected (${t.precipProb}% chance).`;
            const highs = bb.map(b => b.bestMax), dT = bb[bb.length - 1].bestMax - t.bestMax;
            const trend = Math.abs(dT) < 2 ? 'little net temperature change' : dT > 0 ? 'a warming trend' : 'a cooling trend';
            const wet = bb.filter(b => b.bestPrecip >= 1 || b.bestSnow >= 1).map(b => b === t ? 'today' : dayName(b));
            const sp = modelSpread();
            const conf = sp === null ? 'Only one model source was available.' : `Model highs for today differ by ${(isImperial ? sp * 1.8 : sp).toFixed(1)}° — ${sp < 1.5 ? 'high' : sp < 3 ? 'moderate' : 'low'} agreement.`;
            return `<div class="space-y-3 text-xs md:text-sm leading-relaxed text-slate-300">
                <p><strong>NOW:</strong> ${now}</p>
                <p><strong>TODAY:</strong> High near <strong>${formatTemp(t.bestMax)}</strong>${depTxt}; low around ${formatTemp(t.bestMin)}. ${precipTxt} Peak gusts near ${formatSpeed(t.bestGust)}.</p>
                <p><strong>OUTLOOK:</strong> Highs over the next ${bb.length} days range from ${formatTemp(Math.min(...highs))} to ${formatTemp(Math.max(...highs))}, showing ${trend}. ${wet.length ? `Measurable precipitation is most likely ${wet.join(', ')}.` : 'No significant precipitation is forecast.'} ${conf}</p>
                <p class="text-[11px] text-slate-500 italic">Generated from live multi-model data. Add a Gemini API key for an AI-written discussion.</p>
            </div>`;
        }

        async function fetchAISynopticDiscussion() {
            const container = document.getElementById('aiAnalysisContent');
            const badge = document.getElementById('aiStatusBadge');
            const local = buildLocalDiscussion();
            container.innerHTML = local;
            if (!geminiApiKey || !bestBetResults.length) return;
            badge.classList.remove('hidden');
            try {
                const cc = getCurrentConditions();
                const lines = bestBetResults.map(b => `${b.date}: high ${b.bestMax.toFixed(1)}C, low ${b.bestMin.toFixed(1)}C, precip ${b.bestPrecip.toFixed(1)}mm, snow ${b.bestSnow.toFixed(1)}cm, gust ${b.bestGust.toFixed(0)}km/h, precip chance ${b.precipProb}%`).join('\n');
                const prompt = `Write a concise 3-paragraph forecast discussion in NWS style for ${currentLoc.name}. Use ONLY the data below; do not invent fronts, pressure systems or numbers.\nCurrent: ${cc ? cc.temp.toFixed(1) + 'C, ' + (cc.text || getWeatherCondition(cc.code, cc.isDay).text) : 'n/a'}\n${lines}`;
                const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${encodeURIComponent(geminiApiKey)}`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
                });
                const data = await res.json();
                const txt = data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts[0].text;
                if (txt) {
                    container.innerHTML = `<div class="text-xs md:text-sm leading-relaxed text-slate-300">${esc(txt).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}</div>`;
                } else {
                    showToast('Gemini: ' + ((data.error && data.error.message) || 'no response') + ' — showing built-in summary.');
                }
            } catch (e) {
                showToast('Gemini request failed — showing built-in summary.');
            } finally {
                badge.classList.add('hidden');
            }
        }

        // Historical records (exact day) and normals (1991–2020, ±7-day window like NOAA smoothing)
        function getHistoricalStatsForDate(targetDateStr) {
            if (!climIndex) return null;
            const key = targetDateStr.substring(5, 10);
            const rows = climIndex[key];
            if (!rows) return null;
            let recHigh = -Infinity, recHighYr = '', recLow = Infinity, recLowYr = '';
            for (const [yr, mx, mn] of rows) {
                if (mx !== null && mx > recHigh) { recHigh = mx; recHighYr = String(yr); }
                if (mn !== null && mn < recLow) { recLow = mn; recLowYr = String(yr); }
            }
            const base = Date.UTC(2001, parseInt(key.slice(0, 2)) - 1, parseInt(key.slice(3, 5)));
            let sM = 0, nM = 0, sN = 0, nN = 0;
            for (let o = -7; o <= 7; o++) {
                const dt = new Date(base + o * 864e5);
                const k = `${String(dt.getUTCMonth() + 1).padStart(2, '0')}-${String(dt.getUTCDate()).padStart(2, '0')}`;
                (climIndex[k] || []).forEach(([yr, mx, mn]) => {
                    if (yr < 1991 || yr > 2020) return;
                    if (mx !== null) { sM += mx; nM++; }
                    if (mn !== null) { sN += mn; nN++; }
                });
            }
            return {
                recHigh: isFinite(recHigh) ? recHigh : null, recHighYr,
                recLow: isFinite(recLow) ? recLow : null, recLowYr,
                normMax: nM > 0 ? sM / nM : null, normMin: nN > 0 ? sN / nN : null
            };
        }

        // ERA5 Climate Analytics Engine
        function renderClimateAnalytics() {
            const $ = id => document.getElementById(id);
            const todayStats = bestBetResults[0] ? getHistoricalStatsForDate(bestBetResults[0].date) : null;
            $('climateAnomalyText').innerText = (todayStats && todayStats.normMax !== null)
                ? `${formatTempDiff(bestBetResults[0].bestMax - todayStats.normMax, 1)} (High)` : '--';

            if (!historicalData) {
                ['decadalTrendDisplay', 'totalWarmingDisplay', 'nighttimeTrendDisplay', 'normalTempDisplay', 'rSquaredValue', 'stdErrValue'].forEach(id => $(id).innerText = 'N/A');
                $('dailyRecordsTableBody').innerHTML = `<tr><td colspan="4" class="p-3 text-slate-400 italic">ERA5 archive is unavailable right now (offline or rate-limited). Press Fetch Weather to retry.</td></tr>`;
                if (chartInstances.trend) { chartInstances.trend.destroy(); delete chartInstances.trend; }
                return;
            }

            const { time, temperature_2m_mean: tMean, temperature_2m_min: tMin } = historicalData.daily;
            const startYr = parseInt(activeTrendPeriod.split('-')[0]);
            const annual = {};
            for (let i = 0; i < time.length; i++) {
                if (!time[i]) continue;
                const yr = parseInt(time[i].substring(0, 4));
                if (yr < startYr) continue;
                const a = (annual[yr] ||= { m: [], n: [] });
                if (tMean[i] != null && !isNaN(tMean[i])) a.m.push(tMean[i]);
                if (tMin[i] != null && !isNaN(tMin[i])) a.n.push(tMin[i]);
            }

            // Complete years only (>=360 days) so a partial current year can't bias the trend
            const years = [], yMean = [], yMin = [];
            Object.keys(annual).map(Number).sort((a, b) => a - b).forEach(yr => {
                const a = annual[yr];
                if (a.m.length >= 360 && a.n.length >= 360) {
                    years.push(yr);
                    yMean.push(a.m.reduce((x, y) => x + y, 0) / a.m.length);
                    yMin.push(a.n.reduce((x, y) => x + y, 0) / a.n.length);
                }
            });
            if (years.length < 3) return;

            const olsMean = computeOLS(years, yMean), olsMin = computeOLS(years, yMin);
            let bs = 0, bc = 0;
            years.forEach((y, i) => { if (y >= 1991 && y <= 2020) { bs += yMean[i]; bc++; } });
            const baseline = bc > 0 ? bs / bc : yMean.reduce((a, b) => a + b, 0) / yMean.length;
            const lastAnom = yMean[yMean.length - 1] - baseline;

            $('decadalTrendDisplay').innerText = `${formatTempDiff(olsMean.slope * 10, 2)} / decade`;
            $('totalWarmingDisplay').innerText = formatTempDiff(olsMean.slope * (years[years.length - 1] - years[0]), 2);
            $('totalWarmingSub').innerText = `${years[0]}–${years[years.length - 1]} (fitted)`;
            $('nighttimeTrendDisplay').innerText = `${formatTempDiff(olsMin.slope * 10, 2)} / decade`;
            $('normalTempDisplay').innerText = formatTemp(baseline, 1);
            $('normalTempSub').innerText = `1991–2020 · ${years[years.length - 1]}: ${formatTempDiff(lastAnom, 1)}`;
            $('rSquaredValue').innerText = olsMean.rSquared.toFixed(3);
            $('stdErrValue').innerText = formatTempDiff(olsMean.stdErr, 2).replace('+', '');

            renderTrendChart(years, yMean, olsMean);
            renderDailyRecordsTable();
        }

        ''')

# ---------- Chart tweaks ----------
between('const smoothedValues = displayValues.map(', 'chartInstances.trend = new Chart',
        "const smoothedValues = displayValues.map((v, i, arr) => i < 9 ? null : arr.slice(i - 9, i + 1).reduce((a, b) => a + b, 0) / 10); // trailing 10-yr mean\n\n            ")
rep("const labels = h.time.slice(0, 24).map(t => new Date(t).toLocaleTimeString([], { hour: 'numeric', hour12: true }));",
    "const hs = hourlyStart();\n            const labels = h.time.slice(hs, hs + 24).map(t => new Date(t).toLocaleTimeString([], { hour: 'numeric', hour12: true }));")
rep("h.temperature_2m.slice(0, 24).map(", "h.temperature_2m.slice(hs, hs + 24).map(")
rep("h.precipitation_probability.slice(0, 24)", "h.precipitation_probability.slice(hs, hs + 24)")

# ---------- Weather code mapper ----------
between('// Weather Code Icon Mapper', '// Application Onload Initialization', r'''// Weather Code Icon Mapper (full WMO code set used by Open-Meteo)
        function getWeatherCondition(code, isDay) {
            const day = isDay === 1 || isDay === true;
            if (code === 0) return { text: "Clear Sky", icon: day ? "fa-sun" : "fa-moon", color: day ? "text-amber-400" : "text-indigo-300" };
            if (code === 1) return { text: "Mostly Clear", icon: day ? "fa-sun" : "fa-moon", color: day ? "text-amber-300" : "text-indigo-300" };
            if (code === 2) return { text: "Partly Cloudy", icon: day ? "fa-cloud-sun" : "fa-cloud-moon", color: "text-blue-300" };
            if (code === 3) return { text: "Overcast", icon: "fa-cloud", color: "text-slate-400" };
            if (code === 45 || code === 48) return { text: "Foggy", icon: "fa-smog", color: "text-slate-400" };
            if (code >= 51 && code <= 55) return { text: "Drizzle", icon: "fa-cloud-rain", color: "text-blue-400" };
            if (code === 56 || code === 57) return { text: "Freezing Drizzle", icon: "fa-cloud-rain", color: "text-cyan-300" };
            if (code >= 61 && code <= 65) return { text: "Rain", icon: "fa-cloud-showers-heavy", color: "text-blue-500" };
            if (code === 66 || code === 67) return { text: "Freezing Rain", icon: "fa-cloud-showers-heavy", color: "text-cyan-300" };
            if (code >= 71 && code <= 77) return { text: "Snow", icon: "fa-snowflake", color: "text-teal-200" };
            if (code >= 80 && code <= 82) return { text: "Rain Showers", icon: "fa-cloud-sun-rain", color: "text-blue-400" };
            if (code === 85 || code === 86) return { text: "Snow Showers", icon: "fa-snowflake", color: "text-teal-200" };
            if (code === 95) return { text: "Thunderstorm", icon: "fa-bolt", color: "text-amber-400" };
            if (code === 96 || code === 99) return { text: "Thunderstorm w/ Hail", icon: "fa-cloud-bolt", color: "text-amber-400" };
            return { text: "Variable", icon: "fa-cloud-sun", color: "text-slate-300" };
        }

        ''')

open('/mnt/user-data/outputs/the_weather.html', 'w', encoding='utf-8').write(src)
print("ok", len(src))
