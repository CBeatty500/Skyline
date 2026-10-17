        // ---------- Radar map: NOAA base reflectivity mosaic, redrawn on a clean scale over county and state lines ----------
        // Each pixel of NOAA's image is converted to dBZ with the calibrated colour path (rgbToDbz), light echoes and isolated
        // specks are removed, and the rest is recoloured. Counties / states: US Census boundaries (us-atlas). Warnings: NWS.
        const RM = { map: null, overlay: null, frames: [], loopTimer: null, looping: false, delay: 550, warnLayer: null, counties: null, token: 0, me: null };
        const RM_MIN_DBZ = 15;
        const RM_STOPS = [[15, [52, 96, 120]], [20, [6, 170, 70]], [25, [2, 200, 30]], [30, [0, 140, 0]], [35, [235, 225, 0]], [40, [250, 175, 0]],
            [45, [250, 110, 0]], [50, [225, 0, 0]], [55, [165, 0, 0]], [60, [240, 0, 240]], [65, [150, 60, 220]], [70, [255, 255, 255]]];
        function rmColor(z) {
            if (z >= 70) return RM_STOPS[RM_STOPS.length - 1][1];
            for (let i = 0; i < RM_STOPS.length - 1; i++) {
                const [z0, c0] = RM_STOPS[i], [z1, c1] = RM_STOPS[i + 1];
                if (z < z1) { const f = Math.max(0, (z - z0) / (z1 - z0)); return [0, 1, 2].map(k => Math.round(c0[k] + (c1[k] - c0[k]) * f)); }
            }
            return RM_STOPS[0][1];
        }
        const RM_WARN_COLORS = { 'Tornado Warning': '#ff0000', 'Severe Thunderstorm Warning': '#ffa500', 'Flash Flood Warning': '#8b0000', 'Flood Warning': '#00ff00',
            'Flood Advisory': '#00ff7f', 'Special Marine Warning': '#ffa500', 'Tornado Watch': '#ffff00', 'Severe Thunderstorm Watch': '#db7093', 'Flash Flood Watch': '#2e8b57',
            'Flood Watch': '#2e8b57', 'Winter Storm Warning': '#ff69b4', 'Winter Storm Watch': '#4682b4', 'Winter Weather Advisory': '#7b68ee', 'Blizzard Warning': '#ff4500',
            'Ice Storm Warning': '#8b008b', 'Wind Advisory': '#d2b48c', 'High Wind Warning': '#daa520', 'High Wind Watch': '#b8860b', 'Heat Advisory': '#ff7f50',
            'Excessive Heat Warning': '#c71585', 'Extreme Heat Warning': '#c71585', 'Dense Fog Advisory': '#708090', 'Frost Advisory': '#6495ed', 'Freeze Warning': '#483d8b',
            'Freeze Watch': '#00ffff', 'Red Flag Warning': '#ff1493', 'Fire Weather Watch': '#ffdead', 'Special Weather Statement': '#ffe4b5', 'Gale Warning': '#dda0dd',
            'Small Craft Advisory': '#d8bfd8', 'Lake Effect Snow Warning': '#008b8b', 'Coastal Flood Warning': '#228b22', 'Coastal Flood Advisory': '#7cfc00',
            'Hurricane Warning': '#dc143c', 'Tropical Storm Warning': '#b22222', 'Storm Surge Warning': '#b524f7' };
        function rmLoad(src, css) {
            return new Promise((res, rej) => {
                if (css) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = src; l.onload = res; l.onerror = rej; document.head.appendChild(l); return; }
                const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej; document.head.appendChild(s);
            });
        }
        async function openRadarMap() {
            try { await openRadarMapInner(); } catch (e) { console.warn('Radar map failed', e); }
        }
        async function openRadarMapInner() {
            const el = document.getElementById('radarMap'); if (!el || !currentLoc) return;
            if (!window.L) await Promise.all([rmLoad('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css', true), rmLoad('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js')]);
            if (!RM.map) {
                RM.map = L.map(el, { zoomControl: true, attributionControl: true, preferCanvas: true, minZoom: 4, maxZoom: 11 }).setView([+currentLoc.lat, +currentLoc.lon], rmZoom());
                RM.center = [+currentLoc.lat, +currentLoc.lon];
                ['rmBase', 'rmRadar', 'rmLines', 'rmWarn', 'rmLabels'].forEach((p, i) => { RM.map.createPane(p).style.zIndex = 200 + i * 50; });
                RM.map.getPane('rmLabels').style.pointerEvents = 'none'; RM.map.getPane('rmLines').style.pointerEvents = 'none';
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', { pane: 'rmBase', maxZoom: 16, attribution: 'Esri, NOAA/NWS, US Census' }).addTo(RM.map);
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', { pane: 'rmLabels', maxZoom: 16 }).addTo(RM.map);
                RM.map.getPane('rmBase').style.filter = 'brightness(0.42) contrast(1.15)';   // near-black background
                RM.overlay = L.imageOverlay('data:image/gif;base64,R0lGODlhAQABAAAAACw=', RM.map.getBounds(), { pane: 'rmRadar', opacity: 0.88, interactive: false }).addTo(RM.map);
                RM.map.on('moveend', () => { const was = RM.looping; radarMapStop(); RM.frames = []; radarMapDraw().then(() => { if (was) radarMapLoop(); }); });
                RM.map.on('resize', () => {});
                rmCounties();
            }
            radarMapCenter(false);
            setTimeout(() => { RM.map.invalidateSize(); radarMapDraw(); }, 60);
        }
        function rmZoom() { return window.innerWidth < 640 ? 7 : 8; }
        function radarMapCenter(force) {
            if (!RM.map || !currentLoc) return;
            const ll = [+currentLoc.lat, +currentLoc.lon];
            if (force || !RM.center || RM.center[0] !== ll[0] || RM.center[1] !== ll[1]) { RM.center = ll; RM.map.setView(ll, rmZoom()); }

        }
        async function rmCounties() {
            try {
                if (!window.topojson) await rmLoad('https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js');
                const us = await (await fetch('https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/counties-10m.json')).json();
                RM.us = us;
                L.geoJSON(topojson.mesh(us, us.objects.counties, (a, b) => a !== b && Math.floor(a.id / 1000) === Math.floor(b.id / 1000)), { pane: 'rmLines', style: { color: '#64748b', weight: 0.6, opacity: 0.85 }, interactive: false }).addTo(RM.map);
                L.geoJSON(topojson.mesh(us, us.objects.states, (a, b) => a !== b), { pane: 'rmLines', style: { color: '#e2e8f0', weight: 1.4, opacity: 0.9 }, interactive: false }).addTo(RM.map);
                L.geoJSON(topojson.mesh(us, us.objects.nation), { pane: 'rmLines', style: { color: '#e2e8f0', weight: 1.4, opacity: 0.9 }, interactive: false }).addTo(RM.map);
            } catch (e) { console.warn('County lines unavailable', e); }
        }
        // one radar frame for the current view, recoloured; returns a data URL
        async function rmFrame(t, b, sz, retry) {
            const sw = L.CRS.EPSG3857.project(b.getSouthWest()), ne = L.CRS.EPSG3857.project(b.getNorthEast());
            const w = Math.min(1400, sz.x), h = Math.round(sz.y * w / sz.x);
            const q = new URLSearchParams({ bbox: [sw.x, sw.y, ne.x, ne.y].join(','), bboxSR: '3857', imageSR: '3857', size: `${w},${h}`, format: 'png32', transparent: 'true',
                interpolation: 'RSP_NearestNeighbor', f: 'image' });
            if (t) q.set('time', String(t));
            // the server keeps pixels square: it widens the shorter side of the requested area around its centre
            const res = Math.max((ne.x - sw.x) / w, (ne.y - sw.y) / h), cxm = (sw.x + ne.x) / 2, cym = (sw.y + ne.y) / 2;
            const unproj = (x, y) => L.CRS.EPSG3857.unproject(L.point(x, y));
            const realB = L.latLngBounds(unproj(cxm - res * w / 2, cym - res * h / 2), unproj(cxm + res * w / 2, cym + res * h / 2));
            const r = await fetch(`${RADAR_IS}/exportImage?${q}`); if (!r.ok) throw new Error('radar ' + r.status);
            const bmp = await createImageBitmap(await r.blob());
            const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
            const cx = cv.getContext('2d'); cx.drawImage(bmp, 0, 0, w, h);
            const img = cx.getImageData(0, 0, w, h), d = img.data, Z = new Float32Array(w * h), cache = new Map();
            for (let i = 0, p = 0; i < d.length; i += 4, p++) {
                if (d[i + 3] < 100) { Z[p] = 0; continue; }
                const key = (d[i] << 16) | (d[i + 1] << 8) | d[i + 2];
                let z = cache.get(key); if (z === undefined) { z = rgbToDbz(`${d[i]} ${d[i + 1]} ${d[i + 2]} 255`); cache.set(key, z); }
                Z[p] = z;
            }
            for (let y = 0, p = 0; y < h; y++) for (let x = 0; x < w; x++, p++) {
                const z = Z[p], i = p * 4;
                let keep = z >= RM_MIN_DBZ;
                if (keep && z < 35) {   // isolated specks of light echo are clutter
                    let n = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { if (!dx && !dy) continue; const yy = y + dy, xx = x + dx; if (yy >= 0 && yy < h && xx >= 0 && xx < w && Z[yy * w + xx] >= RM_MIN_DBZ) n++; }
                    keep = n >= 3;
                }
                if (!keep) { d[i + 3] = 0; continue; }
                const c = rmColor(z); d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = z < 20 ? 150 + Math.round((z - 15) * 21) : 255;   // light echoes recede
            }
            cx.putImageData(img, 0, 0);
            let any = false; for (let i = 3; i < d.length; i += 4) if (d[i]) { any = true; break; }
            if (!any && !retry && Z.some(z => z > 0) === false && t) return rmFrame(null, b, sz, true);   // empty image for that time: ask for the latest
            return { url: cv.toDataURL('image/png'), bounds: realB };
        }
        function rmStamp(t) { return t ? new Date(t).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZoneName: 'short', timeZone: (ensembleData && ensembleData.timezone) || undefined }) : ''; }
        async function radarMapDraw() {
            if (!RM.map) return;
            const tok = ++RM.token, b = RM.map.getBounds(), sz = RM.map.getSize();
            try {
                const tEnd = await radarLatestTime();
                const stale = !tEnd || Date.now() - tEnd > 45 * 60e3;
                const fr = await rmFrame(tEnd, b, sz);
                if (tok !== RM.token) return;
                RM.overlay.setUrl(fr.url); RM.overlay.setBounds(fr.bounds);
                RM.tEnd = tEnd; RM.frames = [];
                document.getElementById('rmTime').innerText = rmStamp(tEnd) + (stale ? ' (radar delayed)' : '');
            } catch (e) { document.getElementById('rmTime').innerText = 'Radar unavailable'; }
        }
        function radarMapStop() {
            if (RM.loopTimer) { clearTimeout(RM.loopTimer); RM.loopTimer = null; }
            RM.looping = false;
            const b = document.getElementById('rmLoop'); if (b) b.innerHTML = '<i class="fa-solid fa-play"></i>';
        }
        function radarMapSpeed(v) { RM.delay = +v || 550; }
        async function radarMapLoop() {
            if (!RM.map) return;
            if (RM.looping) { radarMapStop(); radarMapDraw(); return; }   // the button stops a running loop
            RM.looping = true;
            const btn = document.getElementById('rmLoop'); btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            const tok = RM.token, b = RM.map.getBounds(), sz = RM.map.getSize();
            if (!RM.frames.length && RM.tEnd) {
                const times = [60, 50, 40, 30, 20, 10, 0].map(m => RM.tEnd - m * 60e3);
                const frs = await Promise.all(times.map(t => rmFrame(t, b, sz).catch(() => null)));
                if (tok !== RM.token || !RM.looping) return;
                RM.frames = times.map((t, i) => frs[i] ? { t, ...frs[i] } : null).filter(Boolean);
            }
            if (!RM.frames.length) { radarMapStop(); return; }
            btn.innerHTML = '<i class="fa-solid fa-pause"></i>';
            let i = 0;
            const step = () => {
                if (!RM.looping) return;
                const f = RM.frames[i]; RM.overlay.setUrl(f.url); RM.overlay.setBounds(f.bounds);
                document.getElementById('rmTime').innerText = rmStamp(f.t);
                const last = i === RM.frames.length - 1; i = last ? 0 : i + 1;
                RM.loopTimer = setTimeout(step, last ? Math.max(1200, RM.delay * 2.5) : RM.delay);
            };
            step();
        }
        // the device's own location, only when asked
        function radarMapMe(on) {
            if (RM.me) { RM.me.remove(); RM.me = null; }
            if (!on || !RM.map) return;
            const no = msg => { document.getElementById('rmMe').checked = false; showToast(msg); };
            if (!navigator.geolocation || !window.isSecureContext) { no('This browser cannot share your location with this page.'); return; }
            navigator.geolocation.getCurrentPosition(p => {
                if (!document.getElementById('rmMe').checked) return;
                const ll = [p.coords.latitude, p.coords.longitude];
                RM.me = L.layerGroup([L.circle(ll, { radius: Math.min(p.coords.accuracy || 0, 3000), color: '#38bdf8', weight: 1, fillOpacity: 0.12, pane: 'rmLabels' }),
                    L.circleMarker(ll, { radius: 5, color: '#e0f2fe', weight: 2, fillColor: '#38bdf8', fillOpacity: 1, pane: 'rmLabels' })]).addTo(RM.map);
            }, err => {
                no(err && err.code === 1 ? 'Location is turned off for this site. Allow location access in your browser or phone settings to show where you are.'
                   : err && err.code === 3 ? 'Your location took too long to arrive. Try again.'
                   : 'Your location is not available right now (location services may be off on this device).');
            }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 120000 });
        }
        async function radarMapWarnings(on) {
            if (!RM.map) return;
            if (RM.warnLayer) { RM.warnLayer.remove(); RM.warnLayer = null; }
            if (!on) return;
            try {
                const j = await (await fetch('https://api.weather.gov/alerts/active?status=actual', { headers: { Accept: 'application/geo+json' } })).json();
                const feats = (j.features || []).filter(f => f.properties && f.properties.event);
                const layer = L.layerGroup();
                const pop = p => `<b>${esc(p.event)}</b><br><span style="font-size:11px">${esc(p.headline || '')}</span>`;
                const col = ev => RM_WARN_COLORS[ev] || '#cbd5e1';
                // storm-based warnings with their own polygon
                feats.filter(f => f.geometry).forEach(f => L.geoJSON(f.geometry, { pane: 'rmWarn', style: { color: col(f.properties.event), weight: 2.5, fill: true, fillOpacity: 0.08 } }).bindPopup(pop(f.properties)).addTo(layer));
                // county / zone-based alerts: shade their counties (FIPS from the SAME codes)
                if (RM.us && window.topojson) {
                    if (!RM.counties) { RM.counties = new Map(); topojson.feature(RM.us, RM.us.objects.counties).features.forEach(c => RM.counties.set(String(c.id).padStart(5, '0'), c)); }
                    const order = ev => /Warning/.test(ev) ? 3 : /Watch/.test(ev) ? 2 : 1;
                    feats.filter(f => !f.geometry && f.properties.geocode && f.properties.geocode.SAME).sort((a, b) => order(a.properties.event) - order(b.properties.event)).forEach(f => {
                        const shapes = f.properties.geocode.SAME.map(s => RM.counties.get(String(s).slice(-5))).filter(Boolean);
                        if (shapes.length) L.geoJSON({ type: 'FeatureCollection', features: shapes }, { pane: 'rmWarn', style: { color: col(f.properties.event), weight: 1.2, fillColor: col(f.properties.event), fillOpacity: 0.12 } }).bindPopup(pop(f.properties)).addTo(layer);
                    });
                }
                if (!document.getElementById('rmWarn').checked) return;
                RM.warnLayer = layer.addTo(RM.map);
            } catch (e) { console.warn('Warnings unavailable', e); }
        }
        // at start-up: open the radar when precipitation is falling or expected later today, otherwise keep it closed
        let rmAutoDone = false, rmAutoAt = 0, rmUserSet = false;
        // the visitor opening or closing the radar themselves ends the automatic opening for this visit
        document.addEventListener('click', e => { if (e.target.closest && e.target.closest('#sec-radar .sec-head')) rmUserSet = true; }, true);
        function rainNowOrToday() {
            try {
                const nc = obsNowcast(); if (nc && nc.wet) return true;
                if (radarNow && Date.now() - radarNow.t < 50 * 60e3 && ((radarNow.z || 0) >= 20 || radarNow.drizzle || (radarNow.near50 || 0) >= 3 || (radarNow.any || 0) >= 5)) return true;   // overhead, drizzle, or precipitation within 50 miles
                const h = ensembleData.hourly, cur = hourlyStart(), day = h.time[cur].slice(0, 10);
                for (let j = cur; j < h.time.length && h.time[j].startsWith(day); j++) if (hourWetCode(j) > 0) return true;
            } catch (e) {}
            return false;
        }
        function radarAutoOpen(final) {
            const cfg = SECTIONS.find(s => s.key === 'radar'); if (!cfg || !cfg._panel) return;
            if (!rmAutoDone) {   // first view of this visit: the forecast decides (not saved, so it is decided fresh each visit)
                rmAutoDone = true; rmAutoAt = Date.now();
                setSecOpen(cfg, rainNowOrToday(), false);
            } else if (final && !rmUserSet && cfg._panel.classList.contains('collapsed') && rainNowOrToday()) {   // any later radar update (also on an open page brought back to the screen), unless the visitor chose
                // radar arriving moments later found precipitation: open without moving what the visitor is looking at
                const above = cfg._panel.getBoundingClientRect().bottom < 0, h0 = document.documentElement.scrollHeight;
                setSecOpen(cfg, true, false);
                if (above) window.scrollBy(0, document.documentElement.scrollHeight - h0);
            }
        }
