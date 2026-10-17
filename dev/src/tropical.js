        // ---------- Tropical cyclones: National Hurricane Center / Central Pacific Hurricane Center ----------
        // One identify request: forecast cones that include the location, the 5-day wind speed probabilities there
        // (34 / 50 / 64 kt), and any 7-day development area. Covers the Atlantic, East and Central Pacific basins.
        let tropicalInfo = null;
        const NHC_MS = 'https://mapservices.weather.noaa.gov/tropical/rest/services/tropical/NHC_tropical_weather/MapServer';
        const NHC_CONES = [8, 34, 60, 86, 112, 138, 164, 190, 216, 242, 268, 294, 320, 346, 372];
        function nhcPct(s) { const m = String(s || '').match(/(\d+)/); return m ? +m[1] + (/^\s*>/.test(s) ? 1 : 0) : 0; }
        async function loadTropical(token, lat, lon) {
            tropicalInfo = null;
            lat = +lat; lon = +lon;
            if (!(lat > 0 && lat < 55 && (lon < -40 || lon > 160))) return;   // outside NHC / CPHC waters and coasts
            const key = `skyline:trop:${lat.toFixed(2)},${lon.toFixed(2)}`;
            try { const c = JSON.parse(sessionStorage.getItem(key) || 'null'); if (c && Date.now() - c.at < 20 * 60e3) { tropicalInfo = c.v; if (token === fetchToken) renderActiveAlerts(); return; } } catch (e) {}
            try {
                const url = `${NHC_MS}/identify?geometry=${lon},${lat}&geometryType=esriGeometryPoint&sr=4326&layers=all:${NHC_CONES.join(',')},395,396,397,3`
                    + `&tolerance=1&mapExtent=${lon - 5},${lat - 5},${lon + 5},${lat + 5}&imageDisplay=400,400,96&returnGeometry=false&f=json`;
                const j = await (await fetch(url)).json();
                const R = (j && j.results) || [];
                const A = (r, ...k) => { for (const x of k) if (r.attributes && r.attributes[x] != null) return r.attributes[x]; return null; };
                const v = { cones: [], wsp: {}, area: null };
                const best = {};
                R.forEach(r => {
                    if (NHC_CONES.includes(r.layerId)) v.cones.push({ layer: r.layerId, name: A(r, 'Storm Name', 'stormname') || r.value, bin: A(r, 'Bin Number', 'binnumber') });
                    else if (r.layerId >= 395 && r.layerId <= 397) {
                        const lab = A(r, 'Percentage', 'percentage') || r.value, kt = { 395: 34, 396: 50, 397: 64 }[r.layerId];
                        if (!best[kt] || nhcPct(lab) > nhcPct(best[kt])) best[kt] = lab;
                    } else if (r.layerId === 3) {
                        const p7 = A(r, 'Seven-Day Probability Forecast', 'prob7day'), p2 = A(r, 'Two-Day Probability Forecast', 'prob2day');
                        if (!v.area || nhcPct(p7) > nhcPct(v.area.p7)) v.area = { p7, p2 };
                    }
                });
                v.wsp = best;
                // current position and strength of each storm whose cone covers the location
                await Promise.all(v.cones.map(async c => {
                    try {
                        const q = await (await fetch(`${NHC_MS}/${c.layer - 2}/query?where=tau%3D0&outFields=stormname,stormtype,maxwind,tcdir,tcspd,lat,lon&returnGeometry=false&f=json`)).json();
                        const a = q && q.features && q.features[0] && q.features[0].attributes;
                        if (a) Object.assign(c, { name: a.stormname || c.name, type: a.stormtype, kt: a.maxwind, dir: a.tcdir, spd: a.tcspd, slat: a.lat, slon: a.lon });
                    } catch (e) {}
                }));
                if (token !== fetchToken) return;
                tropicalInfo = v;
                try { sessionStorage.setItem(key, JSON.stringify({ at: Date.now(), v })); } catch (e) {}
                renderActiveAlerts();
            } catch (e) { /* the hurricane center service is unreachable: nothing to add */ }
        }
        function tropicalAlerts() {
            const v = tropicalInfo; if (!v) return [];
            const out = [], src = 'NHC';
            const ktKmh = kt => kt * 1.852, link = bin => bin ? [{ label: 'Hurricane center graphics', href: `https://www.nhc.noaa.gov/graphics_${String(bin).toLowerCase()}.shtml` }] : [{ label: 'National Hurricane Center', href: 'https://www.nhc.noaa.gov/' }];
            const w34 = v.wsp[34], w64 = v.wsp[64];
            v.cones.forEach(c => {
                const bits = [];
                if (c.kt != null && c.kt < 999) bits.push(`Maximum sustained winds ${formatSpeed(ktKmh(c.kt))}.`);
                if (c.slat != null && c.slon != null) {
                    const km = distKm(+currentLoc.lat, +currentLoc.lon, c.slat, c.slon);
                    const y = Math.sin((c.slon - currentLoc.lon) * Math.PI / 180) * Math.cos(c.slat * Math.PI / 180);
                    const x = Math.cos(currentLoc.lat * Math.PI / 180) * Math.sin(c.slat * Math.PI / 180) - Math.sin(currentLoc.lat * Math.PI / 180) * Math.cos(c.slat * Math.PI / 180) * Math.cos((c.slon - currentLoc.lon) * Math.PI / 180);
                    const brg = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
                    bits.push(`Centered ${isImperial ? Math.round(km * 0.621371 / 10) * 10 + ' miles' : Math.round(km / 10) * 10 + ' km'} ${compass(brg)} of here${c.dir != null && c.dir < 999 && c.spd != null && c.spd < 999 ? `, moving ${compass(c.dir)} at ${formatSpeed(ktKmh(c.spd))}` : ''}.`);
                }
                if (w34) bits.push(`Chance of tropical-storm-force winds here within 5 days: ${w34}${w64 ? `; hurricane-force: ${w64}` : ''}.`);
                out.push({ type: c.type === 'HU' || nhcPct(w34) >= 50 ? 'danger' : 'warning', tag: src, title: `${c.name || 'Tropical cyclone'}: this location is in the forecast cone`, text: bits.join(' '), links: link(c.bin) });
            });
            if (!v.cones.length && nhcPct(w34) >= 5)
                out.push({ type: nhcPct(w34) >= 50 ? 'danger' : 'warning', tag: src, title: 'Tropical-Storm-Force Wind Chance', text: `${w34} chance of tropical-storm-force winds (39+ mph) here within 5 days${w64 ? `; hurricane-force: ${w64}` : ''}.`, links: link(null) });
            if (v.area && nhcPct(v.area.p7) >= 10)
                out.push({ type: 'warning', tag: src, title: 'Tropical Development Area', text: `This location is inside an area the hurricane center is watching: ${v.area.p7} chance of a tropical cyclone forming within 7 days${nhcPct(v.area.p2) ? ` (${v.area.p2} within 2 days)` : ''}.`, links: [{ label: 'Tropical weather outlook', href: 'https://www.nhc.noaa.gov/gtwo.php' }] });
            return out;
        }
