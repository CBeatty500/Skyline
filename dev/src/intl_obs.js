        // ---------- International observations: nearest airport METAR station via the Iowa Environmental Mesonet ----------
        // Converted to the same shape as NWS observations so every observation-driven feature (current conditions,
        // today so far, observation-corrected forecast, model skill weighting, nowcast) works outside the US too.
        const CA_PROV = { 'Alberta': 'AB', 'British Columbia': 'BC', 'Manitoba': 'MB', 'New Brunswick': 'NB', 'Newfoundland and Labrador': 'NF', 'Nova Scotia': 'NS', 'Northwest Territories': 'NT', 'Nunavut': 'NU', 'Ontario': 'ON', 'Prince Edward Island': 'PE', 'Quebec': 'QC', 'Saskatchewan': 'SK', 'Yukon': 'YT' };
        async function intlNetworkFor(lat, lon) {
            const key = `intlnet1:${(+lat).toFixed(2)}:${(+lon).toFixed(2)}`;
            const c = await idb.get(key);
            if (c && c.v) return c.v;
            const q = String(currentLoc.name || '').split(',')[0].trim();
            if (!q) return null;
            const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=10&language=en&format=json`);
            if (!r.ok) return null;
            const j = await r.json();
            let best = null;
            (j.results || []).forEach(g => { const km = distKm(+lat, +lon, g.latitude, g.longitude); if (km < 150 && (!best || km < best.km)) best = { ...g, km }; });
            if (!best || !best.country_code) return null;
            const cc = best.country_code.toUpperCase();
            const net = cc === 'CA' ? (CA_PROV[best.admin1] ? `CA_${CA_PROV[best.admin1]}_ASOS` : null) : `${cc}__ASOS`;
            if (net) await idb.set(key, { v: net });
            return net;
        }
        function iemToObs(d) {
            const f2c = f => (f === null || f === undefined || f === '' || isNaN(f)) ? null : (f - 32) / 1.8;
            const v = x => ({ value: x === null || x === undefined || x === '' || (typeof x === 'number' && isNaN(x)) ? null : x });
            let ts = d.utc_valid || d.valid || null;
            if (ts && !/Z|[+-]\d\d:?\d\d$/.test(ts)) ts += 'Z';
            const wx = Array.isArray(d.wxcodes) ? d.wxcodes : String(d.wxcodes || d.presentwx || '').split(/\s+/).filter(Boolean);
            const layers = [1, 2, 3, 4].map(k => d['skyc' + k] ? { amount: d['skyc' + k], base: { value: d['skyl' + k] != null ? d['skyl' + k] * 0.3048 : null } } : null).filter(Boolean);
            const cover = layers.reduce((m, l) => Math.max(m, { CLR: 0, SKC: 0, NSC: 0, CAVOK: 0, FEW: 1, SCT: 2, BKN: 3, OVC: 4, VV: 4 }[l.amount] ?? 0), 0);
            const intens = c => c.startsWith('-') ? 'Light ' : c.startsWith('+') ? 'Heavy ' : '';
            const wxText = (() => {
                const c = wx.find(w => !/^VC/.test(w) && /(DZ|RA|SN|SG|PL|GR|GS|TS|FG|BR|HZ|FU)/.test(w));
                if (!c) return null;
                if (/TS/.test(c)) return 'Thunderstorm' + (/RA/.test(c) ? ' and Rain' : '');
                if (/FZ(RA|DZ)/.test(c)) return intens(c) + 'Freezing Rain';
                if (/SN/.test(c) && /RA/.test(c)) return intens(c) + 'Rain and Snow';
                if (/SN|SG/.test(c)) return intens(c) + 'Snow';
                if (/PL|GS|GR/.test(c)) return 'Ice Pellets';
                if (/SH/.test(c)) return intens(c) + 'Rain Showers';
                if (/RA/.test(c)) return intens(c) + 'Rain';
                if (/DZ/.test(c)) return intens(c) + 'Drizzle';
                if (/FG/.test(c)) return 'Fog';
                if (/BR/.test(c)) return 'Mist';
                if (/HZ|FU/.test(c)) return 'Haze';
                return null;
            })();
            const skyText = layers.length ? ['Clear', 'Mostly Clear', 'Partly Cloudy', 'Mostly Cloudy', 'Cloudy'][cover] : (/CAVOK/.test(d.raw || d.metar || '') ? 'Clear' : null);
            const kt = x => (x === null || x === undefined || x === '' || isNaN(x)) ? null : x * 1.852;
            return {
                timestamp: ts,
                temperature: v(f2c(d.tmpf)), dewpoint: v(f2c(d.dwpf)), relativeHumidity: v(d.relh),
                windSpeed: { value: kt(d.sknt), unitCode: 'wmoUnit:km_h-1' }, windDirection: v(d.drct), windGust: { value: kt(d.gust), unitCode: 'wmoUnit:km_h-1' },
                visibility: v(d.vsby != null && d.vsby !== '' ? d.vsby * 1609.34 : null),
                barometricPressure: v(d.alti != null && d.alti !== '' ? d.alti * 3386.39 : null),
                seaLevelPressure: v(d.mslp != null && d.mslp !== '' ? d.mslp * 100 : null),
                textDescription: wxText || skyText,
                presentWeather: wx.map(w => ({ rawString: w })),
                cloudLayers: layers,
                rawMessage: d.raw || d.metar || null,
                precipitationLastHour: v(d.p01i != null && d.p01i !== '' && d.p01i >= 0 ? d.p01i * 25.4 : null),
                heatIndex: v(null), windChill: v(null), intl: true
            };
        }
        async function fetchIntlObs(lat, lon, base) {
            const out = { obs: null, obsToday: [] };
            try {
                const net = await intlNetworkFor(lat, lon);
                if (!net) return out;
                const ck = `intlstn1:${net}`;
                let stns = (await idb.get(ck)) || null;
                if (!stns || Date.now() - stns.t > 30 * 864e5) {
                    const r = await fetch(`https://mesonet.agron.iastate.edu/geojson/network/${net}.geojson`);
                    if (!r.ok) return out;
                    const j = await r.json();
                    stns = { t: Date.now(), v: (j.features || []).filter(f => f.geometry && f.geometry.coordinates).map(f => ({
                        id: f.id || (f.properties && f.properties.sid), name: f.properties && f.properties.sname,
                        lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1], elev: f.properties && f.properties.elevation,
                        end: f.properties && f.properties.archive_end })) };
                    await idb.set(ck, stns);
                }
                const near = stns.v.filter(s => !s.end).map(s => ({ ...s, km: distKm(+lat, +lon, s.lat, s.lon) })).filter(s => s.km <= 60).sort((a, b) => a.km - b.km).slice(0, 3);
                const today = base.daily.time[0];
                const yd = (() => { const t = new Date(today + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() - 1); return t.toISOString().slice(0, 10); })();
                for (const s of near) {
                    const get = async date => {
                        const r = await fetch(`https://mesonet.agron.iastate.edu/api/1/obhistory.json?station=${encodeURIComponent(s.id)}&network=${net}&date=${date}&full=1`);
                        if (!r.ok) return [];
                        const j = await r.json();
                        return Array.isArray(j.data) ? j.data : [];
                    };
                    const rows = [...await get(yd).catch(() => []), ...await get(today).catch(() => [])];
                    const obs = rows.map(iemToObs).filter(o => o.timestamp && o.temperature.value !== null)
                        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                    if (!obs.length || Date.now() - new Date(obs[0].timestamp) > 3 * 3600e3) continue;
                    out.obs = { ...obs[0], stationId: s.id, stationName: s.name, stationLat: s.lat, stationLon: s.lon, stationElevM: (s.elev !== null && s.elev !== undefined) ? +s.elev : null };
                    out.obsToday = obs;
                    break;
                }
            } catch (e) { console.warn('International observations unavailable:', e); }
            return out;
        }

