import re
s = open('/mnt/user-data/outputs/the_weather.html', encoding='utf-8').read()
bi = s.index('<body'); be = s.index('<script>', bi)
head, bodyhtml, rest = s[:bi], s[bi:be], s[be:]
lines = bodyhtml.split('\n')
def L(sub):
    return next(i for i, l in enumerate(lines) if sub in l)
m = dict(loc=L('<!-- Location Meta Header -->'), hero=L('<!-- Current Weather Hero Observation Card -->'),
         det=L('Detailed Current Observations') - 2, tsf=L('Today So Far</h3>') - 2,
         prec=L('<!-- Precipitation Totals -->'), alert=L('<!-- Active Weather Watches'),
         grid=L('<!-- 5-Day Best Bet'), hour=L('<!-- Hourly Forecast Slider'), disc=L('<!-- AI Synoptic'),
         afd=L('<!-- NWS Area Forecast'), chart=L('<!-- Main Charts'), clim=L('<!-- Historical ERA5 Climate'),
         foot=L('<!-- Footer -->'))
order = ['loc','hero','det','tsf','prec','alert','grid','hour','disc','afd','chart','clim','foot']
for a, b in zip(order, order[1:]): assert m[a] < m[b], (a, b)
end = L('</footer>') + 1
idx = [m[k] for k in order] + [end]
B = {k: '\n'.join(lines[idx[i]:idx[i+1]]) for i, k in enumerate(order)}
for k, v in B.items():
    if k != 'hero': assert v.count('<div') == v.count('</div>') or k == 'foot', (k, v.count('<div'), v.count('</div>'))

presets = [('Ashburn, VA', 'Ashburn', 39.0437, -77.4875), ('Washington DC', 'DC', 38.8951, -77.0364), ('New York', 'New York', 40.7143, -74.006),
           ('Denver', 'Denver', 39.7392, -104.9903), ('Chicago', 'Chicago', 41.85, -87.65), ('Seattle', 'Seattle', 47.6062, -122.3321),
           ('Anchorage, AK', 'Anchorage', 61.2181, -149.9003), ('Miami, FL', 'Miami', 25.7617, -80.1918)]
chips = ''.join(f'<button onclick="quickSelect(\'{n}\', {la}, {lo})" class="chip">{lab}</button>' for n, lab, la, lo in presets)

header = '''<div id="skyBg"></div>
    <header class="topbar">
        <div class="wrap flex items-center gap-3 py-3">
            <a href="#" class="brand shrink-0" aria-label="Skyline"><span class="brand-mark"><i class="fa-solid fa-cloud-sun"></i></span><span class="brand-name hidden sm:inline">Skyline</span></a>
            <div class="relative flex-1 min-w-0">
                <i class="fa-solid fa-magnifying-glass absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
                <input type="text" id="cityInput" class="search-input" placeholder="Search any city in the world" autocomplete="off">
                <button type="button" onclick="useMyLocation()" id="myLocBtn" class="loc-in" title="Use my location" aria-label="Use my location"><i class="fa-solid fa-location-crosshairs"></i></button>
                <div id="autocompleteResults" class="absolute w-full mt-2 bg-slate-800/95 border border-slate-700 rounded-2xl shadow-2xl max-h-60 overflow-y-auto hidden z-50 divide-y divide-slate-700/60"></div>
            </div>
            <button onclick="searchAndFetch()" class="go-btn shrink-0" aria-label="Get the forecast"><i class="fa-solid fa-arrow-right go-ic"></i><span id="generateBtnText">Fetch</span><div id="generateLoader" class="loader hidden"></div></button>
            <button onclick="refreshData()" id="refreshTop" class="unit-btn shrink-0" title="Refresh data" aria-label="Refresh data"><i class="fa-solid fa-rotate-right"></i><span>Refresh</span></button>
            <button onclick="toggleUnits()" id="unitToggleBtn" class="unit-btn shrink-0" title="Switch units"><i class="fa-solid fa-temperature-half"></i><span id="unitToggleLabel">°F · in · mph</span></button>
        </div>
        <div class="wrap pb-2.5 rail" id="navRail">
            <span id="sectionNav" class="flex items-center gap-1">
                <a href="#sec-now" class="navpill">Now</a><a href="#sec-details" class="navpill">Details</a><a href="#sec-radar" class="navpill">Radar</a><a href="#sec-hourly" class="navpill">Hourly</a><a href="#sec-forecast" class="navpill">Forecast</a><a href="#sec-climate" class="navpill">Climate</a>
            </span>
            <span class="rail-sep" aria-hidden="true"></span>
            <button type="button" id="placesToggle" class="chip" onclick="togglePlaces()" aria-expanded="false" aria-controls="placeChips"><i class="fa-solid fa-city mr-1.5 text-slate-400"></i>Places<i class="fa-solid fa-chevron-right ml-1.5 text-[9px] text-slate-400 pl-chev"></i></button>
            <span id="placeChips" class="place-chips">''' + chips + '''</span>
        </div>
    </header>'''

hero = '''<section id="sec-now" class="hero flex-1">
                    <div>
                        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
                            <span class="chip chip-static"><i class="fa-solid fa-satellite mr-1.5"></i><span id="currentObsSource">Current Conditions</span></span>
                            <span id="currentObsTime" class="text-xs text-slate-300/80"></span>
                            <span id="alertPill" class="alert-pill hidden"><i class="fa-solid fa-circle-check"></i>No active alerts</span><button onclick="refreshData()" class="refresh-btn" title="Refresh data" aria-label="Refresh data"><i class="fa-solid fa-rotate-right"></i><span>Refresh</span></button>
                        </div>
                        <div id="currentStationLine" class="text-[11px] text-slate-300/70 font-mono mt-1"></div>
                    </div>
                    <div class="hero-grid">
                    <div class="hero-main flex flex-wrap items-center gap-x-10 gap-y-2">
                        <div class="flex items-center gap-4 md:gap-7">
                            <i id="currentWeatherIcon" class="fa-solid fa-sun"></i>
                            <div class="flex flex-col"><span id="currentTempDisplay" class="hero-temp">--</span><div id="feelsLine" class="feels-line"><span id="feelsLbl">Feels like</span> <span id="currentApparentTemp" class="font-semibold text-white">--</span></div></div>
                        </div>
                        <div class="flex-1 min-w-[230px]">
                            <div class="flex items-center gap-2.5"><i id="currentWeatherIcon2" class="hero-ic2"></i><div id="currentWeatherConditionText" class="font-display text-3xl md:text-4xl leading-tight">--</div></div>
                            <div class="flex flex-wrap items-center gap-x-6 gap-y-1 mt-3">
                                <span id="heroHiWrap" class="hl hl-hi"><i class="fa-solid fa-arrow-up"></i><b id="heroHi">--</b><small id="heroHiLbl">High</small></span>
                                <span class="hl hl-lo"><i class="fa-solid fa-arrow-down"></i><b id="heroLo">--</b><small id="heroLoLbl">Overnight low</small></span>
                            </div>
                        </div>
                    </div>
                    <div id="heroAlertSlot" class="hero-alerts"></div>
                    <div class="hero-cc">
                        <div class="hg-head"><span class="ho-name"><i class="fa-solid fa-gauge mr-1.5"></i>Current conditions</span><span id="ccStamp" class="hg-meta"></span></div>
                        <div class="metric-strip">
                            <div><div class="mlabel"><i class="fa-solid fa-droplet text-teal-300"></i> Dew point</div><div class="mval"><span id="currentDewPoint">--</span> <span id="currentDewPointCategory" class="text-[10px] font-medium text-teal-300/90"></span></div><div class="msub">Humidity <span id="currentHumidity" class="font-semibold">--</span></div></div>
                            <div><div class="mlabel"><i class="fa-solid fa-wind text-teal-300"></i> Wind</div><div id="currentWind" class="mval">--</div></div>
                            <div><div class="mlabel"><i class="fa-solid fa-gauge-high text-indigo-300"></i> Pressure</div><div id="currentPressure" class="mval">--</div></div>
                            <div><div class="mlabel"><i class="fa-solid fa-lungs text-slate-300"></i> Air quality</div><div id="currentAQI" class="mval">--</div></div>
                        </div>
                    </div>
                    <div class="hero-tsf">
                        <div class="hg-head"><span class="ho-name"><i class="fa-solid fa-calendar-day mr-1.5"></i>Today so far</span><span id="todaySoFarSource" class="hg-meta"></span></div>
                        <div id="todaySoFarGrid" class="metric-strip"></div>
                    </div>
                    </div>
                    <div id="heroSun" class="flex flex-wrap items-center justify-center gap-x-5 gap-y-1 -mt-1 text-xs text-slate-200/90"></div>
                    <div class="hero-text">
                        <div class="hg-head"><span class="ho-name"><i class="fa-solid fa-calendar-week mr-1.5"></i>Forecast</span></div>
                        <div id="heroNarrLbl" class="ho-per">Today</div>
                        <p id="heroNarrative" class="text-sm text-slate-200/90 leading-relaxed"></p>
                        <div id="heroOutlook" class="hero-outlook"></div>
                    </div>
                </section>'''

_ch = B['chart']
def _cut(a, b):
    i = _ch.index(a); j = _ch.index(b, i)
    seg = _ch[i:j].rstrip()
    return seg
CH = dict(temp=_cut('<!-- Hourly Temp Multi-Model Chart -->', '<!-- Raw Model Comparison Table -->'),
          table=_cut('<!-- Raw Model Comparison Table -->', '\n                </div>\n\n                <!-- Right Col'),
          precip=_cut('<!-- Precip Probabilities Chart -->', '<!-- Domain & Elevation Bias Panel -->'),
          weights=_ch[_ch.index('<!-- Domain & Elevation Bias Panel -->'):_ch.rindex('</div>\n                </div>\n            </div>')].rstrip() + '\n                    </div>')
for _k, _v in CH.items(): assert _v.count('<div') == _v.count('</div>'), (_k, _v.count('<div'), _v.count('</div>'))
QUICK = open('/home/claude/quick_view.html').read()
MODEL_HTML = open('/home/claude/model_analysis.html').read()
main = f'''<main class="wrap pb-16 pt-3 sm:pt-4 space-y-5">
{B['hero'].split(chr(10))[0] and ''}
        <div id="toastContainer" role="status" aria-live="polite" class="toast-float hidden glass-panel border-l-4 border-amber-500 p-4 rounded-xl flex justify-between items-center text-sm shadow-xl">
            <div class="flex items-center gap-3"><i class="fa-solid fa-circle-exclamation text-amber-400 text-lg"></i><span id="toastMessage" class="text-slate-200">System Notification</span></div>
            <button onclick="closeToast()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
        </div>

        <div id="statusMessage" class="bb-hero">
            <div class="bb-sky" aria-hidden="true"><span class="bb-glow"></span><span class="bb-cloud bb-c1"></span><span class="bb-cloud bb-c2"></span><span class="bb-cloud bb-c3"></span></div>
            <div class="bb-inner">
                <div class="bb-chip"><i class="fa-solid fa-cloud-sun text-6xl mb-5 text-amber-300"></i></div>
                <h1 class="bb-word"><span class="bb-best">Best Bet</span><span class="bb-wx">Weather</span></h1>
                <p class="bb-hook">Know the odds<br>before you go.</p>
                <div class="bb-cta">
                    <button type="button" class="bb-btn" onclick="useMyLocation()"><i class="fa-solid fa-location-crosshairs"></i>Get my forecast</button>
                    <button type="button" class="bb-btn2" onclick="var i=document.getElementById('cityInput');i.scrollIntoView({{block:'center'}});i.focus()"><i class="fa-solid fa-magnifying-glass"></i>Search a city</button>
                </div>
                <ul class="bb-tags"><li><i class="fa-solid fa-percent"></i>Hourly odds</li><li><i class="fa-solid fa-satellite-dish"></i>Live radar</li><li><i class="fa-solid fa-check-double"></i>Graded daily</li></ul>
            </div>
        </div>

        <div id="dashboardContent" class="hidden space-y-5">
            {B['loc']}
            <div id="topAlertSlot">{B['alert']}</div>
            <div class="flex">{hero}</div>
            <div id="sec-details" class="space-y-5">
                {B['det']}
            </div>
            <div id="sec-hourly">{B['hour']}</div>
            <div id="sec-graphs" class="glass-panel rounded-2xl p-5">
                <div class="graphs-head"><h3 class="flex items-center gap-2"><i class="fa-solid fa-chart-area"></i> Hourly Graphs</h3></div>
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-5 items-stretch">
                    <div class="lg:col-span-2 flex flex-col min-w-0 temp-col">{CH['temp']}</div>
                    <div class="flex flex-col gap-5 chart-precip min-w-0">{CH['precip']}</div>
                </div>
            </div>
            <div id="sec-forecast">{B['grid']}</div>
            {B['afd']}
            {QUICK}
            <div id="sec-climate">{B['clim']}</div>
            {MODEL_HTML}
            <footer class="text-center text-xs text-slate-400 py-8 border-t border-white/10">Skyline &bull; NOAA NWS, Open-Meteo multi-model ensemble, NASA POWER, NOAA GHCN normals, Iowa Environmental Mesonet climate reports.</footer>
        </div>
    </main>
'''
main = main.replace(B['hero'].split('\n')[0] and '', '')
_a = main.index('<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">\n                    <!-- Daily Historical Records Table -->')
_e = '</div>\n                    </div>\n                </div>\n'
_b = main.index(_e, main.index('Residual Std Dev')) + len(_e)
main = main[:_a] + main[_b:]
_c = main.index('<div id="sec-climate">') + len('<div id="sec-climate">')
main = main[:_c] + open('/home/claude/daily_climate.html').read() + '\n            <div class="h-5"></div>\n' + main[_c:]
assert main.count('<div id="forecastGrid"') == 1
main = main.replace('<div id="forecastGrid"', '<div class="fc-wrap"><div id="forecastGrid"', 1)
assert main.count('<!-- Forecast cards injected dynamically -->\n                </div>') == 1
main = main.replace('<!-- Forecast cards injected dynamically -->\n                </div>', '<!-- Forecast cards injected dynamically -->\n                </div><div id="fcSlider" class="fc-slider" role="slider" tabindex="0" aria-label="Scroll forecast days"><div class="fc-track"><div id="fcThumb" class="fc-thumb"></div></div></div></div>', 1)

css = r'''
/* ===== Skyline theme ===== */
:root { --card: rgba(10,20,42,.56); --line: rgba(255,255,255,.12); --ink: #eef3fb; --mute: #b9c6dd; --accent: #7cc8ff; }
html { scroll-behavior: smooth; }
body { font-family: 'Outfit', system-ui, sans-serif !important; color: var(--ink) !important; background: #07101f !important; padding: 0 !important; }
.font-display, .hero-temp, h2 { font-family: 'Fraunces', Georgia, serif; }
/* notices float over whatever the visitor is looking at, not at the top of the page */
.toast-float{position:fixed;left:50%;bottom:calc(18px + env(safe-area-inset-bottom));transform:translateX(-50%);width:min(calc(100vw - 24px),520px);z-index:3000;background:rgba(10,20,42,.96)!important;backdrop-filter:blur(10px);box-shadow:0 18px 40px -12px rgba(0,0,0,.7)!important;animation:toastIn .25s ease-out}
@keyframes toastIn{from{opacity:0;transform:translate(-50%,12px)}to{opacity:1;transform:translate(-50%,0)}}

/* welcome hero */
.bb-hero{position:relative;overflow:hidden;border-radius:1.75rem;padding:3.25rem 1.25rem 2.25rem;text-align:center;
  background:radial-gradient(120% 80% at 50% 0%,#24508f 0%,#173566 45%,#0d1f42 100%);border:1px solid rgba(255,255,255,.09);
  box-shadow:0 30px 60px -25px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.08)}
.bb-sky{position:absolute;inset:0;pointer-events:none}
.bb-glow{position:absolute;left:50%;top:-6%;width:340px;height:340px;transform:translateX(-50%);border-radius:50%;
  background:radial-gradient(circle,rgba(255,176,90,.38) 0%,rgba(255,140,90,.12) 40%,transparent 70%);animation:bbGlow 6s ease-in-out infinite}
.bb-cloud{position:absolute;border-radius:999px;background:rgba(255,255,255,.07);filter:blur(1px)}
.bb-cloud::before,.bb-cloud::after{content:"";position:absolute;border-radius:50%;background:inherit}
.bb-c1{width:150px;height:38px;top:16%;left:-170px;animation:bbDrift 46s linear infinite}
.bb-c1::before{width:62px;height:62px;left:24px;top:-30px}.bb-c1::after{width:46px;height:46px;left:74px;top:-20px}
.bb-c2{width:110px;height:28px;top:58%;left:-130px;animation:bbDrift 62s linear -24s infinite;opacity:.8}
.bb-c2::before{width:46px;height:46px;left:18px;top:-22px}.bb-c2::after{width:34px;height:34px;left:56px;top:-14px}
.bb-c3{width:190px;height:44px;top:80%;left:-210px;animation:bbDrift 80s linear -50s infinite;opacity:.6}
.bb-c3::before{width:74px;height:74px;left:30px;top:-36px}.bb-c3::after{width:56px;height:56px;left:92px;top:-26px}
.bb-inner{position:relative;max-width:30rem;margin:0 auto}
.bb-chip{display:flex;justify-content:center;margin-bottom:1.1rem;filter:drop-shadow(0 12px 18px rgba(0,0,0,.45))}
.bb-chip svg{width:104px;height:104px;animation:bbToss 1.1s cubic-bezier(.2,.9,.25,1.15) both}
.bb-word{margin:0;line-height:1;font-family:'Outfit',system-ui,sans-serif}
.bb-best{display:block;font-weight:800;font-size:clamp(2.6rem,13vw,4.25rem);letter-spacing:-.02em;text-transform:uppercase;
  background:linear-gradient(180deg,#ffe3a8 0%,#ffb84d 45%,#ff7a59 100%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 4px 14px rgba(255,140,80,.28));animation:bbRise .7s .25s ease-out both}
.bb-wx{display:flex;align-items:center;justify-content:center;gap:.75rem;margin-top:.45rem;font-weight:500;font-size:clamp(.9rem,4vw,1.1rem);
  letter-spacing:.55em;text-indent:.55em;text-transform:uppercase;color:#dbe7f7;animation:bbRise .7s .4s ease-out both}
.bb-wx::before,.bb-wx::after{content:"";height:1px;width:2.2rem;background:linear-gradient(90deg,transparent,rgba(255,200,130,.7))}
.bb-wx::after{transform:scaleX(-1)}
.bb-hook{margin:1.6rem 0 0;font-family:'Fraunces',Georgia,serif;font-size:clamp(1.55rem,7vw,2.1rem);line-height:1.15;color:#fff;animation:bbRise .7s .55s ease-out both}
.bb-cta{display:flex;flex-wrap:wrap;justify-content:center;gap:.7rem;margin-top:1.75rem;animation:bbRise .7s .7s ease-out both}
.bb-btn,.bb-btn2{display:inline-flex;align-items:center;justify-content:center;min-width:13.5rem;gap:.55rem;border-radius:999px;padding:.85rem 1.4rem;font-family:'Outfit',sans-serif;font-weight:600;font-size:1rem;transition:transform .15s,box-shadow .15s,background .15s}
.bb-btn{color:#2a1504;background:linear-gradient(135deg,#ffc062,#ff7a59);box-shadow:0 10px 24px -8px rgba(255,122,89,.7)}
.bb-btn:hover{transform:translateY(-1px);box-shadow:0 14px 28px -8px rgba(255,122,89,.85)}
.bb-btn2{color:#e6eefa;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18)}
.bb-btn2:hover{background:rgba(255,255,255,.14)}
.bb-btn:active,.bb-btn2:active{transform:scale(.97)}
.bb-tags{display:flex;flex-wrap:wrap;justify-content:center;gap:.5rem 1.1rem;margin:1.9rem 0 0;padding:0;list-style:none;font-size:.85rem;color:#a9bddb;animation:bbRise .7s .85s ease-out both}
.bb-tags i{color:#ffb84d;margin-right:.4rem;font-size:.8em}
@keyframes bbToss{0%{transform:translateY(-70px) rotate(-200deg) scale(.6);opacity:0}70%{transform:translateY(4px) rotate(8deg) scale(1.03);opacity:1}100%{transform:none}}
@keyframes bbRise{from{transform:translateY(12px);opacity:0}to{transform:none;opacity:1}}
@keyframes bbDrift{from{transform:translateX(0)}to{transform:translateX(calc(100vw + 420px))}}
@keyframes bbGlow{0%,100%{opacity:.85}50%{opacity:1}}
@media (prefers-reduced-motion:reduce){.bb-hero *{animation:none!important}}

.wrap { max-width: 1400px; margin: 0 auto; padding-left: 14px; padding-right: 14px; }
@media (min-width: 768px) { .wrap { padding-left: 28px; padding-right: 28px; } }
[id^="sec-"] { scroll-margin-top: 8.5rem; }

/* sky: changes with the current conditions and time of day */
#skyBg { position: fixed; inset: 0; z-index: -1; background: linear-gradient(180deg, #0b2f63 0%, #17508f 50%, #2c6aa8 100%); transition: background 1s; }
#skyBg::before { content: ""; position: absolute; inset: 0; background: radial-gradient(900px 420px at 85% -5%, rgba(255,214,140,.30), transparent 60%); }
#skyBg::after { content: ""; position: absolute; inset: 0; background: transparent; transition: background 1s; }
body[data-sky^="cloud"] #skyBg { background: linear-gradient(180deg, #263444 0%, #46586b 50%, #6c7f92 100%); }
body[data-sky^="fog"] #skyBg { background: linear-gradient(180deg, #2c3743 0%, #4a5866 50%, #7b8896 100%); }
body[data-sky^="rain"] #skyBg { background: linear-gradient(180deg, #152433 0%, #27415a 50%, #3d5d78 100%); }
body[data-sky^="snow"] #skyBg { background: linear-gradient(180deg, #2a3a52 0%, #51698a 50%, #8fa6c3 100%); }
body[data-sky^="storm"] #skyBg { background: linear-gradient(180deg, #17122a 0%, #2b1f4a 50%, #4a3472 100%); }
body[data-sky^="cloud"] #skyBg::before, body[data-sky^="rain"] #skyBg::before, body[data-sky^="fog"] #skyBg::before, body[data-sky^="storm"] #skyBg::before, body[data-sky^="snow"] #skyBg::before { background: radial-gradient(900px 420px at 85% -5%, rgba(180,200,230,.14), transparent 60%); }
body[data-sky$="night"] #skyBg::after { background: rgba(2,6,22,.62); }
body[data-sky="clear-night"] #skyBg::before { background: radial-gradient(1px 1px at 20% 30%, #fff, transparent), radial-gradient(1px 1px at 70% 18%, #fff, transparent), radial-gradient(1.5px 1.5px at 45% 60%, #fff, transparent), radial-gradient(1px 1px at 88% 52%, #fff, transparent), radial-gradient(1px 1px at 12% 74%, #fff, transparent), radial-gradient(800px 380px at 80% 0%, rgba(120,150,255,.18), transparent 60%); }

/* top bar */
.topbar { position: sticky; top: 0; z-index: 40; background: rgba(6,12,26,.62); backdrop-filter: blur(18px) saturate(1.3); -webkit-backdrop-filter: blur(18px) saturate(1.3); border-bottom: 1px solid var(--line); }
.brand { display: flex; align-items: center; gap: .6rem; color: #fff; text-decoration: none; }
.brand-mark { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; background: linear-gradient(135deg, #ffb84d, #ff7a59); color: #1a1205; font-size: 18px; }
.brand-name { font-family: 'Fraunces', serif; font-size: 1.5rem; letter-spacing: -.02em; }
.search-input { width: 100%; height: 44px; border-radius: 999px; background: rgba(255,255,255,.09); border: 1px solid var(--line); color: #fff; padding: 0 44px 0 42px; font-size: 14px; outline: none; }
.loc-in { position: absolute; right: 5px; top: 50%; transform: translateY(-50%); width: 34px; height: 34px; border-radius: 999px; display: grid; place-items: center; color: #7dd3fc; background: rgba(125,211,252,.10); border: 1px solid rgba(125,211,252,.30); }
.loc-in:hover { background: rgba(125,211,252,.20); color: #fff; }
.search-input::placeholder { color: var(--mute); }
.search-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(124,200,255,.2); }
.go-ic { display: none; }
@media (max-width: 639px) { .go-btn { width: 44px; padding: 0; justify-content: center; } .go-btn #generateBtnText { display: none; } .go-btn .go-ic { display: inline; } .go-btn:has(.loader:not(.hidden)) .go-ic { display: none; } }
.go-btn { height: 44px; padding: 0 20px; border-radius: 999px; background: linear-gradient(135deg, #ffb84d, #ff8a4c); color: #1a1205; font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 8px; }
.unit-btn { height: 44px; padding: 0 14px; border-radius: 999px; background: rgba(255,255,255,.09); border: 1px solid var(--line); color: var(--ink); font-size: 12px; display: flex; align-items: center; gap: 8px; white-space: nowrap; }
#myLocBtn.busy i { animation: spin 1s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } }
#refreshTop { display: none !important; } @media (min-width: 768px) { #refreshTop { display: flex !important; } }
.refresh-btn { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 11px; border-radius: 999px; font-size: 12px; color: #dbeafe; background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.18); }
.refresh-btn:hover { background: rgba(255,255,255,.18); }
.refresh-btn { margin-left: auto; }
@media (max-width: 767px) { .refresh-btn span { display: none; } .refresh-btn { width: 30px; height: 30px; padding: 0; justify-content: center; } }
.refreshing .fa-rotate-right { animation: spin .9s linear infinite; }
.unit-btn span { display: none; } @media (min-width: 900px) { .unit-btn span { display: inline; } }
.rail { display: flex; align-items: center; gap: 6px; overflow-x: auto; scrollbar-width: none; }
.rail::-webkit-scrollbar { display: none; }
.rail-sep { flex: 0 0 1px; align-self: stretch; margin: 3px 4px; background: rgba(255,255,255,.15); }
body.no-data .rail-sep { display: none; }
.place-chips { display: none; align-items: center; gap: 6px; }
.place-chips.open { display: flex; }
#placesToggle[aria-expanded="true"] .pl-chev { transform: rotate(180deg); }
@media (min-width: 1024px) { .place-chips { display: flex; } #placesToggle { display: none; } }
@media (max-width: 639px) { .navpill { padding: 4px 8px; } #sectionNav { gap: 0; } }
/* top of the forecast: no inherited gap above it, a short gap before the alerts */
#dashboardContent { margin-top: 0 !important; }
#dashboardContent > #topAlertSlot { margin-top: .75rem; }
#dashboardContent > #topAlertSlot:empty { margin-top: 0; }
.rail-label { font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: var(--mute); margin-right: 4px; }
.chip { padding: 4px 12px; border-radius: 999px; background: rgba(255,255,255,.08); border: 1px solid var(--line); font-size: 12px; color: var(--ink); white-space: nowrap; }
.chip:hover { background: rgba(255,255,255,.16); }
.chip-static { display: inline-flex; align-items: center; background: rgba(124,200,255,.15); border-color: rgba(124,200,255,.35); color: #cfeaff; font-weight: 600; }
.navpill { padding: 4px 11px; border-radius: 999px; font-size: 12px; color: var(--mute); white-space: nowrap; text-decoration: none; }
.navpill:hover { color: #fff; } .navpill.active { background: rgba(255,255,255,.16); color: #fff; }
body.no-data #sectionNav { display: none; }

/* hero */
.hero { position: relative; border-radius: 28px; padding: 24px; background: linear-gradient(140deg, rgba(255,255,255,.17), rgba(255,255,255,.05)), rgba(10,20,42,.10); border: 1px solid rgba(255,255,255,.2); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); box-shadow: 0 30px 60px -30px rgba(0,0,0,.6); }
@media (min-width: 768px) { .hero { padding: 36px; } }
.hero-outlook { display: none; }
@media (min-width: 1280px) { .hero-outlook:not(:empty) { display: flex; flex-direction: column; gap: 12px; padding: 12px 0 0; } }
.hero-outlook .ho-name { font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #fde68a; margin-bottom: 3px; }
.hero-outlook p { font-size: 14px; line-height: 1.5; color: rgba(226,232,240,.92); }
#heroSun b { margin-left: 5px; }
.feels-line { font-size: 15px; color: #cbd5e1; margin-top: 10px; margin-bottom: 14px; text-align: center; }
@media (max-width: 767px) { .feels-line { font-size: 13px; margin-top: 6px; } }
.hero-temp { font-weight: 300; font-size: clamp(5.5rem, 14vw, 9.5rem); line-height: .85; letter-spacing: -.05em; color: #fff; text-shadow: 0 6px 40px rgba(0,0,0,.25); }
#currentWeatherIcon { font-size: clamp(3.6rem, 8vw, 5.6rem) !important; filter: drop-shadow(0 0 22px currentColor); }
.hl { display: inline-flex; align-items: baseline; gap: 6px; font-size: 15px; } .hl b { font-size: 26px; font-weight: 600; } .hl small { color: var(--mute); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
.hl-hi i { color: #ff9f6b; } .hl-lo i { color: #7cc8ff; }
.metric-strip { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.metric-strip > div { background: rgba(8,16,34,.34); border: 1px solid rgba(255,255,255,.1); border-radius: 14px; padding: 12px 16px; min-height: 88px; }
.mlabel { font-size: 11px; color: var(--mute); letter-spacing: .04em; } .mlabel i { margin-right: 4px; }
.mval { font-size: 18px; font-weight: 600; margin-top: 2px; }

/* cards: recolor the existing panels */
.col-fill { display: flex; flex-direction: column; gap: 20px; }
.glass-panel, .glass-panel-accent { background: linear-gradient(140deg, rgba(255,255,255,.07), rgba(255,255,255,.015)), var(--card) !important; border: 1px solid var(--line) !important; border-radius: 22px !important; backdrop-filter: blur(10px) saturate(1.2); -webkit-backdrop-filter: blur(10px) saturate(1.2); box-shadow: 0 18px 40px -24px rgba(0,0,0,.7) !important; }
[class*="bg-slate-900"] { background-color: rgba(255,255,255,.045) !important; }
[class*="bg-slate-950"] { background-color: rgba(0,0,0,.32) !important; }
[class*="bg-slate-800"] { background-color: rgba(255,255,255,.08) !important; }
[class*="border-slate-"], [class*="border-purple-"] { border-color: var(--line) !important; }
.text-slate-400, .text-slate-500 { color: var(--mute) !important; }
.plabel { color: #d3dcea !important; font-weight: 600; }
.pcell { background: rgba(255,255,255,.06) !important; border-color: rgba(255,255,255,.12) !important; }
.pcell.past { opacity: .6 !important; }
.pop { background: #0f3a68 !important; color: #fff !important; }
.glass-panel .bg-gradient-to-r { background-image: linear-gradient(90deg, rgba(255,255,255,.08), rgba(255,255,255,.02)) !important; }
#displayLocationName { font-family: 'Fraunces', serif; font-weight: 400; letter-spacing: -.02em; }
#forecastGrid { display: flex !important; overflow-x: auto; gap: 12px; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
                padding-bottom: 10px; scrollbar-width: none; scroll-behavior: smooth; }
#forecastGrid::-webkit-scrollbar { display: none; }
#forecastGrid > div { flex: 0 0 calc((100% - 36px) / 4); min-width: 0; scroll-snap-align: start; }
@media (max-width: 1023px) { #forecastGrid > div { flex-basis: calc((100% - 24px) / 3); } }
@media (max-width: 767px) {
  #forecastGrid { margin: 0 -14px; padding: 0 14px 10px; scroll-padding-left: 14px; }
  #forecastGrid > div { flex: 0 0 84%; max-width: 360px; }
}
.fc-wrap { position: relative; }
.fc-slider { position: relative; padding: 10px 0; margin-top: 4px; cursor: pointer; touch-action: none; outline: none; user-select: none; -webkit-user-select: none; }
.fc-slider.hidden { display: none; }
.fc-track { position: relative; height: 6px; border-radius: 999px; background: rgba(255,255,255,.14); }
.fc-thumb { position: absolute; top: 50%; left: 0; height: 10px; transform: translateY(-50%); border-radius: 999px; min-width: 36px;
            background: linear-gradient(90deg, #7cc8ff, #a9dcff); box-shadow: 0 2px 8px rgba(0,0,0,.35); transition: height .15s; }
.fc-slider:hover .fc-thumb, .fc-slider.dragging .fc-thumb, .fc-slider:focus-visible .fc-thumb { height: 14px; }
.fc-slider:focus-visible .fc-track { box-shadow: 0 0 0 2px rgba(124,200,255,.4); }
#forecastGrid > div { border-radius: 20px !important; background: linear-gradient(140deg, rgba(255,255,255,.07), rgba(255,255,255,.015)), var(--card) !important; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
#hourlyContainer { scrollbar-width: thin; }

/* observations grid: equal-size boxes; a partly filled last row is centered */
#obsDetailGrid { display: flex !important; flex-wrap: wrap; justify-content: center; align-content: flex-start; gap: 12px; }
#obsDetailGrid > div { flex: 0 0 calc((100% - 12px) / 2); min-width: 0; box-sizing: border-box; }
@media (min-width: 768px) { #obsDetailGrid > div { flex-basis: calc((100% - 36px) / 4); } }
@media (min-width: 1280px) { #obsDetailGrid { gap: 10px; } #obsDetailGrid > div { flex-basis: calc((100% - 40px) / 5); padding: 10px 12px !important; } }
.chart-precip > .glass-panel:first-child, .model-col > .glass-panel { flex: 1; display: flex; flex-direction: column; }
.chart-precip .relative.h-56 { flex: 1; min-height: 14rem; height: auto !important; }
.chart-precip .relative.h-56 > canvas { position: absolute; inset: 0; }
/* the temperature graph grows to match the column beside it */
@media (min-width: 1024px) {
  .temp-col > .glass-panel { display: flex; flex-direction: column; }
  .temp-col .flex:has(> #tempYAxis) { flex: 1; min-height: 15rem; }
  .temp-col #tempYAxis { height: auto !important; align-self: stretch; }
  .temp-col #tempChartScroll { display: flex; }
  .temp-col #tempChartInner { height: auto !important; min-height: 15rem; align-self: stretch; flex: 0 0 auto; }
  .temp-col #tempChartInner > canvas { position: absolute; inset: 0; }
}
.min-w-0 { min-width: 0; }
#sec-details > .grid > div, #dashboardContent > .grid > div { min-width: 0; }
:where(#dashboardContent .grid) { grid-template-columns: minmax(0, 1fr); }
.lg\:col-span-2.flex > .glass-panel { flex: 1; }
.model-col > .glass-panel > table { flex: 1; }
@media (min-width: 640px) { .model-col #weightsContainer { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; } .model-col #weightsContainer > * { margin: 0 !important; } }
@media (min-width: 1280px) { .model-col > .glass-panel { margin: 0; } }
/* no "NWS Guidance" badge */
#nwsStatusBadge, #climateAnomalyBadge { display: none !important; }
#bestBetConfidenceBadge { display: none !important; }
#displayLocationName { display: inline; margin-right: 14px; }
#displayLocationMeta { display: inline-block; margin-top: 0 !important; white-space: nowrap; }
@media (max-width: 767px) { #displayLocationName { display: block; margin-right: 0; } #displayLocationMeta { display: block; margin-top: 4px !important; white-space: normal; } }
@media (min-width: 768px) { #climateYesterday > :last-child:nth-child(odd) { grid-column: 1 / -1; justify-self: center; width: calc(50% - 4px); } }
/* yesterday's records (climate section) */
.yrec { display: flex; align-items: flex-start; gap: 12px; padding: 10px 14px; border-radius: 14px; border: 1px solid rgba(251,191,36,.35); background: rgba(251,191,36,.08); }
.dclim td { padding: 8px 10px; white-space: nowrap; border-top: 1px solid rgba(255,255,255,.06); }
.dclim tr.grp td { padding: 14px 10px 4px; border-top: 0; font-family: 'Outfit', system-ui, sans-serif; font-size: 10px; letter-spacing: .08em; text-transform: uppercase; color: #8fa3c0; }
.dclim tr.today td { background: rgba(124,200,255,.10); border-top-color: rgba(124,200,255,.35); }
.dclim tr.today td:first-child { border-radius: 10px 0 0 10px; } .dclim tr.today td:last-child { border-radius: 0 10px 10px 0; }
.dclim tr.fc td.ob { font-style: italic; color: #b9c6dd; }
.dclim .dep { font-size: 10px; margin-left: 5px; }
.dclim .rec { color: #fcd34d; margin-left: 5px; }
.dc-pick { height: 34px; border-radius: 10px; background: rgba(255,255,255,.08); border: 1px solid var(--line); color: var(--ink); font-size: 13px; padding: 0 28px 0 10px; appearance: none; -webkit-appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, #b9c6dd 50%), linear-gradient(135deg, #b9c6dd 50%, transparent 50%); background-position: calc(100% - 15px) 14px, calc(100% - 10px) 14px; background-size: 5px 5px; background-repeat: no-repeat; }
.dc-pick option { background: #0e1a2e; color: #eef3fb; }
.dcs-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
@media (min-width: 768px) { .dcs-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); } }
.dcs { padding: 10px 12px; border-radius: 12px; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.09); }
.dclim td.qv-ic { padding-left: 2px; padding-right: 2px; text-align: center; font-size: 15px; width: 28px; }
.dclim tr.fc td.ob, .dclim td.ob { font-style: normal; }
@media (max-width: 767px) { .dclim td:first-child, .dclim th:first-child { position: sticky; left: 0; z-index: 1; background: #13233d; } .dclim tr.grp td:first-child { background: transparent; } .dclim tr.today td:first-child { background: #1b3352; } }
.yrec i { color: #fcd34d; margin-top: 3px; }
/* narrow columns */
#precipTotalsGrid { grid-template-columns: 1fr !important; }
@media (min-width: 640px) { #precipTotalsGrid { grid-template-columns: repeat(2, 1fr) !important; } }
@media (min-width: 1024px) { #precipTotalsGrid { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)) !important; } #precipTotalsGrid > :last-child:nth-child(odd) { grid-column: auto !important; width: auto !important; justify-self: stretch !important; } }
.hero-tsf .ho-name, .hero-cc .ho-name { font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #fde68a; }
#heroAlertSlot:empty, #topAlertSlot:empty { display: none; }
.hero-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 18px; }
@media (min-width: 1024px) { .hero-grid { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); column-gap: 28px; row-gap: 22px; } .hero-main { flex-wrap: nowrap !important; align-self: center; } .hero-main > .flex-1 { flex: 0 1 auto !important; } .hero-alerts { min-width: 0; align-self: stretch; } .hero-alerts #alertsContainer { height: 100%; } }
.hg-head .ho-name { white-space: nowrap; }
.hero-cc, .hero-tsf { display: flex; flex-direction: column; min-width: 0; }
.hero-cc > .metric-strip, .hero-tsf > .metric-strip { flex: 1; grid-auto-rows: 1fr; }
.alert-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 600; color: #a7f3d0; background: rgba(16,185,129,.12); border: 1px solid rgba(52,211,153,.35); border-radius: 999px; padding: 3px 10px; }
.alert-pill.hidden { display: none; }
.hero-main { grid-area: main; } #heroAlertSlot { grid-area: alerts; } .hero-cc { grid-area: cc; } .hero-tsf { grid-area: tsf; }
.hero-grid { grid-template-areas: "main" "alerts" "cc" "tsf"; }
.hero-grid.al-none #heroAlertSlot { display: none; }
@media (min-width: 1024px) {
  .hero-grid.al-few { grid-template-areas: "main alerts" "cc tsf"; }
  .hero-grid.al-none { grid-template-areas: "main main" "cc tsf"; }
  .hero-grid.al-many { grid-template-areas: "alerts alerts" "main main" "cc tsf"; }
  .hero-grid.al-many #alertsList { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .hero-grid.al-many #alertsList > * { margin: 0 !important; }
}
@media (min-width: 1280px) {
  .hero-grid.al-none { grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr) minmax(0, 1fr); grid-template-areas: "main cc tsf"; }
  .hero-grid.al-many { grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr) minmax(0, 1fr); grid-template-areas: "alerts alerts alerts" "main cc tsf"; }
  .hero-grid.al-none .hero-main, .hero-grid.al-many .hero-main { flex-direction: column; align-items: flex-start !important; gap: 6px !important; }
}
.hg-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 8px; min-height: 18px; }
.hg-meta { font-size: 11px; color: rgba(203,213,225,.7); font-family: ui-monospace, Menlo, monospace; text-align: right; }
.msub { font-size: 10px; color: rgba(203,213,225,.72); margin-top: 2px; line-height: 1.35; }
.rec-btn { background: none; border: 0; padding: 0; cursor: pointer; }
.rec-pop { position: fixed; z-index: 80; max-width: 280px; padding: 8px 11px; border-radius: 10px; background: #1e293b; border: 1px solid rgba(251,191,36,.55); color: #fde68a; font: 500 12px/1.45 'Outfit', system-ui, sans-serif; box-shadow: 0 12px 30px -10px rgba(0,0,0,.7); }
#heroAlertSlot #alertsContainer { background: rgba(8,16,34,.3); border-color: rgba(255,255,255,.14); box-shadow: none; }

/* search suggestions: solid, readable panel */
#autocompleteResults { background: #0e1a2e !important; backdrop-filter: none !important; border: 1px solid rgba(124,200,255,.3) !important; box-shadow: 0 24px 48px -12px rgba(0,0,0,.85) !important; }
#autocompleteResults > * { background: transparent !important; color: #eaf1fb; }
#autocompleteResults > *:hover { background: rgba(124,200,255,.14) !important; }

/* hero fills its row; the metric strip sits on the bottom edge */
.hero { display: flex; flex-direction: column; gap: 16px; }
#currentWeatherIcon2 { display: none; }
@media (max-width: 767px) { .hero { padding: 18px 18px 16px !important; gap: 14px; } .hero-main { flex-wrap: nowrap !important; align-items: center !important; gap: 16px !important; }
  .hero-main > :first-child { flex: 0 0 auto; }
  .hero-main > :first-child #currentWeatherIcon { display: none !important; }
  #currentWeatherIcon2 { display: inline-block !important; font-size: 1.9rem !important; filter: drop-shadow(0 0 14px currentColor); }
  .hero-temp { font-size: 4.6rem !important; }
  .hero-main > .flex-1 { flex: 1 1 auto !important; min-width: 0 !important; }
  .hero-main #currentWeatherConditionText { font-size: 1.6rem; }
  .hero-main > .flex-1 > div.flex:has(#heroHiWrap) { flex-direction: column; align-items: flex-start; gap: 0 !important; margin-top: 6px !important; }
  .hero-main > .flex-1 > div.flex:has(#currentWeatherIcon2) { flex-wrap: nowrap; gap: 8px !important; }
  .hero-main > .flex-1 .text-sm.mt-1 { margin-top: 2px !important; }
  .hero-main .hl b { font-size: 21px; } .hero-main .hl small { font-size: 10px; letter-spacing: .06em; } .hero-main .hl { gap: 5px; } }
.hero .metric-strip { margin-top: 2px; }
.hero-text { border-top: 1px solid rgba(255,255,255,.14); padding-top: 14px; }
.hero-text .ho-per, .hero-outlook .ho-name { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #e2e8f0; margin-bottom: 3px; }
@media (min-width: 768px) {
  .hero-text { display: grid; grid-template-columns: 9.5rem minmax(0, 1fr); column-gap: 14px; row-gap: 10px; align-items: baseline; }
  .hero-text > .hg-head, .hero-text > .hero-outlook { grid-column: 1 / -1; }
  .hero-text > .hg-head { margin-bottom: 0; }
  .hero-text .ho-per, .hero-outlook .ho-name { margin-bottom: 0; }
}
@media (min-width: 1280px) {
  .hero-outlook:not(:empty) { display: grid !important; grid-template-columns: 9.5rem minmax(0, 1fr); column-gap: 14px; row-gap: 10px; padding-top: 0 !important; align-items: baseline; }
  .hero-outlook .ho-item { display: contents; }
}
.hero-text .hg-head .ho-name { font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #fde68a; margin-bottom: 3px; }

/* desktop alignment: columns in a row end on the same line */
@media (min-width: 1280px) {
  .col-stretch { display: flex; flex-direction: column; }
  .col-stretch > * { flex: 1; }
  .col-stretch > .glass-panel { display: flex; flex-direction: column; }
  #obsDetailGrid { flex: 1; align-content: stretch; }
  #obsDetailGrid > div { display: flex; flex-direction: column; justify-content: center; }
  #precipTotalsGrid > div { flex: 1; display: grid; grid-template-columns: auto minmax(0, 1fr); column-gap: 18px; align-content: center; align-items: center; padding: 12px 16px !important; }
  #precipTotalsGrid > div > * { margin-top: 0 !important; }
  #precipTotalsGrid > div > :first-child { grid-column: 1 / -1; margin-bottom: 2px; }
  #precipTotalsGrid > div > .text-2xl { grid-column: 1; }
  #precipTotalsGrid > div > .text-sky-200 { grid-column: 2; text-align: right; font-size: 11px; line-height: 1.45; }
  #precipTotalsGrid > div > :last-child { grid-column: 1 / -1; margin-top: 4px !important; }
  #precipTotalsGrid > :last-child:nth-child(odd) { grid-column: auto !important; justify-self: stretch !important; width: auto !important; }
  .col-fill { display: flex; flex-direction: column; gap: 20px; }
  .col-fill > :last-child { flex: 1; display: flex; flex-direction: column; }
  .col-fill #todaySoFarGrid { flex: 1; grid-auto-rows: 1fr; }
  .col-abs { position: relative; min-height: 420px; }
  .col-abs > #afdPanel { position: absolute; inset: 0; display: flex; flex-direction: column; }
  .col-abs > #afdPanel.hidden { display: none; }
}
'''

js = r'''
        // ---------- Skyline: sky theme, hero summary, section navigation ----------
        function applySky() {
            const cc = getCurrentConditions();
            if (!cc) return;
            const day = cc.isDay === 1 || cc.isDay === true, t = (cc.text || '').toLowerCase(), code = cc.code;
            let kind = 'clear';
            if (/thunder/.test(t) || code >= 95) kind = 'storm';
            else if (/snow|sleet|flurr/.test(t) || (code >= 71 && code <= 77) || code === 85 || code === 86) kind = 'snow';
            else if (/rain|shower|drizzle/.test(t) || (code >= 51 && code <= 67) || (code >= 80 && code <= 82)) kind = 'rain';
            else if (/fog|mist|haze|smoke/.test(t) || code === 45 || code === 48) kind = 'fog';
            else if (/overcast|mostly cloudy/.test(t) || code === 3 || (cc.cloud != null && cc.cloud >= 75)) kind = 'cloud';
            document.body.dataset.sky = `${kind}-${day ? 'day' : 'night'}`;
        }

        function renderHero() {
            document.body.classList.remove('no-data');
            { const i1 = document.getElementById('currentWeatherIcon'), i2 = document.getElementById('currentWeatherIcon2'); if (i1 && i2) i2.className = i1.className; }
            const bb = bestBetResults[0];
            if (!bb) return;
            try { renderHeroOutlook(); } catch (e) { console.warn(e); }
            const $h = id => document.getElementById(id);
            {
                const d = ensembleData.daily, ct = ensembleData.current && ensembleData.current.time;
                const afterSunset = ct && d.sunset && d.sunset[0] && ct.slice(0, 16) >= d.sunset[0].slice(0, 16) && d.sunrise[1];
                const j = afterSunset ? 1 : 0, sr = d.sunrise && d.sunrise[j], ss = d.sunset && d.sunset[j];
                const mins = (a, b) => (a && b) ? Math.round((new Date(b.slice(0, 16) + ':00Z') - new Date(a.slice(0, 16) + ':00Z')) / 60000) : null;
                const len = mins(sr, ss), nxt = mins(d.sunrise && d.sunrise[j + 1], d.sunset && d.sunset[j + 1]);
                const diff = (len !== null && nxt !== null) ? nxt - len : null;
                const el = $h('heroSun');
                if (el) el.innerHTML = sr && ss ? `<span><i class="fa-solid fa-sun text-amber-300 mr-1.5"></i>Sunrise <b class="text-white">${fmtClock(sr)}</b>${afterSunset ? ' <span class="text-slate-400">tomorrow</span>' : ''}</span>`
                    + `<span><i class="fa-solid fa-moon text-indigo-300 mr-1.5"></i>Sunset <b class="text-white">${fmtClock(ss)}</b></span>`
                    + `<span><i class="fa-solid fa-hourglass-half text-amber-200/80 mr-1.5"></i>Daylight <b class="text-white">${dayLength(sr, ss)}</b></span>` : '';
            }
            const ni = nightInfo();
            const rf = recordFlags(0);
            if (ni) {
                // tonight: the low leads; a high only appears if temperatures will climb overnight
                const lo = $h('heroLo').parentElement, hiW = $h('heroHiWrap');
                lo.parentElement.insertBefore(lo, hiW);
                $h('heroLo').innerText = formatTemp(ni.low); $h('heroLoLbl').innerText = 'Low tonight';
                hiW.style.display = ni.high !== null ? '' : 'none';
                if (ni.high !== null) { $h('heroHi').innerText = formatTemp(ni.high); $h('heroHiLbl').innerText = 'Rising to'; }
                const parts = [ni.nowcast && ni.nowcast.wet ? `${NOWCAST_WORD[ni.nowcast.kind]} falling now; low tonight near ${formatTemp(ni.low)}.` : `${(t => t[0] + t.slice(1).toLowerCase())(ni.cond.text.split(' · ')[0])} tonight with a low near ${formatTemp(ni.low)}.`];
                if (ni.high !== null) parts.push(`Temperatures rise to around ${formatTemp(ni.high)} before sunrise.`);
                if (precipExpected(ni.pp, ni.rain + ni.snow)) parts.push(`${ni.pp}% chance of precipitation${ni.rain >= 0.05 ? `, about ${formatPrecip(ni.rain)}` : ''}${ni.snow >= 0.05 ? ` (${formatSnow(ni.snow)} of snow)` : ''}.`);
                else if (ni.pp >= 20) parts.push(`A ${ni.pp}% chance of a passing shower.`);
                if (ni.gust >= 40) parts.push(`Gusts to ${formatSpeed(ni.gust)}.`);
                if (rf.high && rf.high.type === 'set') parts.push(rf.high.tie ? 'Today tied the daily record high.' : 'Today set a new daily record high.');
                if (radarInfo && radarInfo.msg) parts.splice(1, 0, radarInfo.msg);
                $h('heroNarrative').innerText = parts.join(' ');
                $h('heroNarrLbl').innerText = 'Tonight';
                return;
            }
            const hiW = $h('heroHiWrap'), lo = $h('heroLo').parentElement;
            hiW.style.display = ''; hiW.parentElement.insertBefore(hiW, lo);
            $h('heroHiLbl').innerText = 'High'; $h('heroLoLbl').innerText = 'Overnight low';
            $h('heroHi').innerText = formatTemp(bb.bestMax);
            $h('heroLo').innerText = formatTemp(bb.bestMin);
            const cond = dailyCondition(bb), parts = [], nc = bb.nowcast;
            if (nc && nc.wet) {
                parts.push(`${NOWCAST_WORD[nc.kind]} falling now, with a high near ${formatTemp(bb.bestMax)}.`);
                if (bb.bestPrecip >= 0.25) parts.push(`About ${formatPrecip(bb.bestPrecip)} more today.`);
                if (bb.laterProb != null) parts.push(`Once it ends, ${bb.laterProb}% chance of more later today.`);
            } else {
                const ph = restOfDayPhrase() || '';
                parts.push(withHigh(restOfDayPhrase() || cond.text.split(' · ')[0] + ' for the rest of today', `high near ${formatTemp(bb.bestMax)}`));
                if (/shower|rain|storm|snow|drizzle|sleet|mix/i.test(ph) && bb.bestPrecip >= 0.25) parts.push(`About ${formatPrecip(bb.bestPrecip)} possible.`);
            }
            if (bb.bestGust >= 40) parts.push(`Gusts to ${formatSpeed(bb.bestGust)}.`);
            parts.push(`Overnight low near ${formatTemp(bb.bestMin)}.`);
            if (rf.high && rf.high.type === 'set') parts.push(rf.high.tie ? 'The daily record high has been tied.' : 'A new daily record high has been set.');
            else if (rf.high && rf.high.type === 'record') parts.push('Record high territory.');
            if (radarInfo && radarInfo.msg) parts.splice(1, 0, radarInfo.msg);
            $h('heroNarrative').innerText = parts.join(' ');
            $h('heroNarrLbl').innerText = 'Today';
        }

        (function () {
            const pills = [...document.querySelectorAll('.navpill')];
            const io = new IntersectionObserver(es => es.forEach(e => {
                if (e.isIntersecting) pills.forEach(p => p.classList.toggle('active', p.getAttribute('href') === '#' + e.target.id));
            }), { rootMargin: '-25% 0px -65% 0px' });
            pills.forEach(p => { const el = document.querySelector(p.getAttribute('href')); if (el) io.observe(el); });
        })();

        function fcScroll(dir) { const g = document.getElementById('forecastGrid'); if (!g) return; g.scrollBy({ left: dir * g.clientWidth, behavior: 'smooth' }); }
        function fcNavState() {
            const g = document.getElementById('forecastGrid'), sl = document.getElementById('fcSlider'), th = document.getElementById('fcThumb');
            if (!g || !sl || !th) return;
            const max = g.scrollWidth - g.clientWidth;
            sl.classList.toggle('hidden', max < 4);
            if (max < 4) return;
            const tw = sl.querySelector('.fc-track').clientWidth;
            const w = Math.max(36, tw * g.clientWidth / g.scrollWidth);
            th.style.width = w + 'px';
            th.style.left = ((tw - w) * Math.min(1, Math.max(0, g.scrollLeft / max))) + 'px';
            sl.setAttribute('aria-valuenow', Math.round(100 * g.scrollLeft / max));
        }
        (function () {
            let drag = null;
            function geom() {
                const g = document.getElementById('forecastGrid'), sl = document.getElementById('fcSlider'), th = document.getElementById('fcThumb');
                const tr = sl.querySelector('.fc-track').getBoundingClientRect();
                return { g, sl, th, tr, w: th.offsetWidth, max: g.scrollWidth - g.clientWidth };
            }
            function moveTo(x, off) {
                const o = geom(); const span = o.tr.width - o.w; if (span <= 0) return;
                const f = Math.min(1, Math.max(0, (x - o.tr.left - off) / span));
                o.g.scrollLeft = f * o.max;
            }
            document.addEventListener('pointerdown', e => {
                const sl = e.target.closest && e.target.closest('#fcSlider'); if (!sl) return;
                const o = geom();
                o.g.style.scrollSnapType = 'none'; o.g.style.scrollBehavior = 'auto';
                const thr = o.th.getBoundingClientRect();
                const off = (e.clientX >= thr.left && e.clientX <= thr.right) ? e.clientX - thr.left : o.w / 2;
                drag = { off, id: e.pointerId };
                sl.classList.add('dragging');
                try { sl.setPointerCapture(e.pointerId); } catch (_) {}
                moveTo(e.clientX, off); e.preventDefault();
            });
            document.addEventListener('pointermove', e => { if (drag && e.pointerId === drag.id) moveTo(e.clientX, drag.off); });
            function end(e) {
                if (!drag || e.pointerId !== drag.id) return;
                drag = null;
                const o = geom(); o.sl.classList.remove('dragging');
                o.g.style.scrollBehavior = ''; o.g.style.scrollSnapType = '';
                const card = o.g.firstElementChild;
                if (card) { const step = card.getBoundingClientRect().width + 12; o.g.scrollTo({ left: Math.round(o.g.scrollLeft / step) * step, behavior: 'smooth' }); }
            }
            document.addEventListener('pointerup', end); document.addEventListener('pointercancel', end);
            document.addEventListener('keydown', e => {
                if (!e.target || e.target.id !== 'fcSlider') return;
                const g = document.getElementById('forecastGrid'); const card = g.firstElementChild; if (!card) return;
                const step = card.getBoundingClientRect().width + 12;
                if (e.key === 'ArrowRight') { g.scrollBy({ left: step, behavior: 'smooth' }); e.preventDefault(); }
                if (e.key === 'ArrowLeft') { g.scrollBy({ left: -step, behavior: 'smooth' }); e.preventDefault(); }
                if (e.key === 'Home') { g.scrollTo({ left: 0, behavior: 'smooth' }); e.preventDefault(); }
                if (e.key === 'End') { g.scrollTo({ left: g.scrollWidth, behavior: 'smooth' }); e.preventDefault(); }
            });
        })();
        document.addEventListener('scroll', e => { if (e.target && e.target.id === 'forecastGrid') fcNavState(); }, true);
        window.addEventListener('resize', fcNavState);

        // Application Onload Initialization'''

# assemble
new_body = bodyhtml[:bodyhtml.index('>') + 1].replace(re.search(r'class="[^"]*"', bodyhtml[:bodyhtml.index('>')]).group(0), 'class="no-data selection:bg-sky-400 selection:text-slate-900"') + '\n    ' + header + '\n    ' + main + '\n\n    '
out = head + new_body + rest
out = re.sub(r'<title>.*?</title>', '<title>Skyline · Weather</title>', out, count=1, flags=re.S)
out = out.replace('</head>', '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,600&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">\n</head>', 1)
cssend = out.index('</style>')
out = out[:cssend] + css + out[cssend:]
assert out.count('// Application Onload Initialization') == 1
out = out.replace('// Application Onload Initialization', js.strip().replace('// Application Onload Initialization', '') + '\n        // Application Onload Initialization', 1)
assert out.count('updateAFDPanel();\n') == 1
out = out.replace('updateAFDPanel();\n', 'updateAFDPanel();\n            renderHero();\n            applySky();\n            requestAnimationFrame(fcNavState);\n', 1)
DESK = "window.matchMedia('(min-width: 1024px)').matches"
YOLD = """                    alerts.push({ type: 'warning', tag: 'NWS climate report', title: `Record ${w} ${r.tie ? 'Tied' : 'Set'} Yesterday — ${stn}`,
                        text: `${w} of ${fv(r.valRaw)} ${r.tie ? 'tied' : 'set'} the daily record${r.prior ? ` (previous ${r.prior})` : ''}.` });
                });"""
YNEW_UNUSED = """                    yItems.push(`<div class="yrec"><i class="fa-solid fa-trophy"></i><div><div class="text-sm font-bold text-amber-100">Record ${w.toLowerCase()} ${r.tie ? 'tied' : 'set'} yesterday at ${esc(stn)}</div><div class="text-xs text-slate-300 mt-0.5">${w} of <b class="font-mono">${fv(r.valRaw)}</b> ${r.tie ? 'tied' : 'set'} the daily record${r.prior ? ` (previous ${r.prior})` : ''}. NWS climate report.</div></div></div>`);
                });
                const yEl = document.getElementById('climateYesterday');
                if (yEl) { yEl.innerHTML = yItems.join(''); yEl.classList.toggle('hidden', !yItems.length); }"""
YNEW = """                });"""
assert out.count(YOLD) == 1
out = out.replace(YOLD, YNEW)
assert out.count("const ry = recordsYesterday();") == 1
out = out.replace("const ry = recordsYesterday();", "const ry = recordsYesterday(), yItems = [];")
for a, b in [
    ("let snowTotals = null,", "let afdAuto = false, snowTotals = null,"),
]:
    assert out.count(a) == 1, (a[:60], out.count(a))
    out = out.replace(a, b)
# short unit labels
n1 = len(re.findall(r'°F / in / mph \(Imperial\)', out)); out = re.sub(r'°F / in / mph \(Imperial\)', '°F · in · mph', out)
n2 = len(re.findall(r'°C[^\'"`<]*\(Metric\)', out)); out = re.sub(r'°C[^\'"`<]*\(Metric\)', '°C · mm · km/h', out)
print('unit label replacements', n1, n2)
for a, b, n in [("forecast_days=9", "forecast_days=13", 2), ("const n = Math.min(8, d.time.length);", "const n = Math.min(12, d.time.length);", 1),
                ("8-Day Operational Forecast Grid", "12-Day Forecast", 1),
                ("(dt ? dt + ' · ' : '') + formatSpeed(cc.wind)", "(dt ? dt + ' ' : '') + formatSpeed(cc.wind)", 1)]:
    assert out.count(a) == n, (a, out.count(a))
    out = out.replace(a, b)
assert out.count("['Dew pt', ") == 2
out = out.replace("['Dew pt', ", "['Dewpoint', ")
exec(open('/home/claude/skyline_extra.py').read())
import re as _re
out = _re.sub(r'([Dd])ew[ -][Pp]oint', lambda m: m.group(1)+'ewpoint', out)
exec(open('/home/claude/skyline_post.py').read())
open('/mnt/user-data/outputs/skyline.html', 'w', encoding='utf-8').write(out)
js_ = re.findall(r'<script>(.*?)</script>', out, re.S)[-1]
open('/tmp/sky.js', 'w').write(js_)
print('bytes', len(out))
# every id the script writes to must still exist
ids = set(re.findall(r"getElementById\('([A-Za-z0-9_]+)'\)", js_)) | set(re.findall(r"\$\('([A-Za-z0-9_]+)'\)", js_)) | set(re.findall(r"\$r\('([A-Za-z0-9_]+)'\)", js_))
html_ids = set(re.findall(r'id="([A-Za-z0-9_]+)"', out))
missing = sorted(i for i in ids if i not in html_ids)
print('ids referenced but not in markup:', missing)
