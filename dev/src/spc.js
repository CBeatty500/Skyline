        // ---------- SPC severe outlooks (Days 1-3), SPC mesoscale discussions, WPC winter discussion ----------
        // Outlook polygons: NOAA/NWS map service (point query). Products: IEM AFOS archive, NWS API as backup.
        let spcData = null;
        const SPC_CAT = { TSTM: { n: 0, name: 'General Thunderstorms', c: '#c1e9c1' }, MRGL: { n: 1, name: 'Marginal Risk', c: '#66a366' }, SLGT: { n: 2, name: 'Slight Risk', c: '#ffe066' }, ENH: { n: 3, name: 'Enhanced Risk', c: '#ffa366' }, MDT: { n: 4, name: 'Moderate Risk', c: '#e06666' }, HIGH: { n: 5, name: 'High Risk', c: '#ee99ee' } };
        const SPC_DN = { 2: 'TSTM', 3: 'MRGL', 4: 'SLGT', 5: 'ENH', 6: 'MDT', 8: 'HIGH' };
        const SPC_LAYERS = { 1: { cat: 1, tornado: 3, hail: 5, wind: 7 }, 2: { cat: 9, tornado: 11, hail: 13, wind: 15 }, 3: { cat: 17, severe: 19 } };
        const SPC_MS = 'https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/MapServer/';
        const WINTER_RE = /snow|freezing|ice\b|icing|sleet|blizzard|winter/i;

        function spcFetch(u, ms = 12000) {
            const ac = typeof AbortController !== 'undefined' ? new AbortController() : null;
            const t = ac ? setTimeout(() => ac.abort(), ms) : null;
            return fetch(u, ac ? { signal: ac.signal } : {}).finally(() => { if (t) clearTimeout(t); });
        }
        function spcInConus(lat, lon) { return lat > 23 && lat < 51 && lon > -127 && lon < -65; }
        function spcTime(v) {
            if (v == null || v === '') return null;
            if (typeof v === 'number') return new Date(v);
            const s = String(v), m = s.match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})$/);
            const d = m ? new Date(Date.UTC(+m[1], m[2] - 1, +m[3], +m[4], +m[5])) : new Date(s);
            return isNaN(d) ? null : d;
        }
        // ddhhmm (UTC) -> Date nearest to now
        function spcDDHHMM(dd, hh, mm) {
            const n = new Date();
            let d = new Date(Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), +dd, +hh, +mm));
            if (d - n > 15 * 864e5) d = new Date(Date.UTC(n.getUTCFullYear(), n.getUTCMonth() - 1, +dd, +hh, +mm));
            else if (n - d > 15 * 864e5) d = new Date(Date.UTC(n.getUTCFullYear(), n.getUTCMonth() + 1, +dd, +hh, +mm));
            return d;
        }
        function spcPct(a) {
            const lab = String(a.label == null ? '' : a.label);
            if (!/\d/.test(lab)) return 0;
            let v = parseFloat(lab.replace(/[^\d.]/g, ''));
            if (!isFinite(v)) return 0;
            if (v < 1) v *= 100;
            return Math.round(v);
        }
        async function spcQuery(layer, lat, lon) {
            const u = `${SPC_MS}${layer}/query?geometry=${lon},${lat}&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&f=json`;
            const r = await spcFetch(u);
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const j = await r.json();
            if (j.error || !Array.isArray(j.features)) throw new Error('outlook service');
            return j.features.map(f => { const o = {}; Object.entries(f.attributes || {}).forEach(([k, v]) => { o[k.toLowerCase()] = v; }); return o; });
        }
        // newest-first list of product texts for an AWIPS id (e.g. SWOMCD, SWODY1, QPFHSD)
        async function spcProducts(pil, n, maxAgeH) {
            const fresh = t => { const d = spcIssued(t); return !maxAgeH || !d || Date.now() - d < maxAgeH * 36e5; };
            try {
                const r = await spcFetch(`https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?pil=${pil}&limit=${n}&fmt=text`);
                if (r.ok) {
                    const t = (await r.text()).replace(/\r/g, '');
                    const parts = t.split(/[\x01\x03]|(?=^[A-Z]{4}\d{2} [A-Z]{4} \d{6}[ A-Z]*$)/m).map(s => s.trim()).filter(s => s.length > 80 && !/^</.test(s));
                    if (parts.length) return parts.filter(fresh);
                }
            } catch (e) {}
            try {
                const j = await (await spcFetch(`https://api.weather.gov/products/types/${pil.slice(0, 3)}/locations/${pil.slice(3)}`)).json();
                const items = (j['@graph'] || []).filter(p => !maxAgeH || Date.now() - Date.parse(p.issuanceTime) < maxAgeH * 36e5).slice(0, n);
                const texts = await Promise.all(items.map(p => spcFetch(p['@id'] || `https://api.weather.gov/products/${p.id}`).then(r => r.json()).then(x => x.productText || '').catch(() => '')));
                return texts.filter(Boolean);
            } catch (e) { return []; }
        }
        function spcIssued(t) {
            const m = String(t).match(/^[A-Z]{4}\d{2} [A-Z]{4} (\d{2})(\d{2})(\d{2})/m);
            return m ? spcDDHHMM(m[1], m[2], m[3]) : null;
        }
        function spcInPoly(lat, lon, poly) {
            let inside = false;
            for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
                const [yi, xi] = poly[i], [yj, xj] = poly[j];
                if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) inside = !inside;
            }
            return inside;
        }
        function parseMD(t) {
            const num = (t.match(/Mesoscale Discussion\s+(\d+)/i) || [])[1];
            if (!num) return null;
            const grab = re => ((t.match(re) || [])[1] || '').replace(/\s+/g, ' ').trim();
            const v = t.match(/Valid\s+(\d{2})(\d{2})(\d{2})Z\s*-\s*(\d{2})(\d{2})(\d{2})Z/i);
            const ll = t.match(/LAT\.\.\.LON\s+([\d\s]+)/);
            const poly = ll ? (ll[1].match(/\d{8}/g) || []).map(p => {
                let lo = +p.slice(4) / 100; if (lo < 50) lo += 100;
                return [+p.slice(0, 4) / 100, -lo];
            }) : [];
            const wp = t.match(/Probability of Watch Issuance\.\.\.\s*(\d+)\s*percent/i);
            return {
                num: +num, text: t,
                concerning: grab(/Concerning\.\.\.([\s\S]*?)(?:\n\s*\n|$)/i),
                areas: grab(/Areas affected\.\.\.([\s\S]*?)(?:\n\s*\n|$)/i),
                summary: grab(/SUMMARY\.\.\.([\s\S]*?)(?:\n\s*\n|$)/),
                start: v ? spcDDHHMM(v[1], v[2], v[3]) : null,
                end: v ? spcDDHHMM(v[4], v[5], v[6]) : null,
                watchProb: wp ? +wp[1] : null, poly
            };
        }

        async function fetchSPC(lat, lon, onDays) {
            const res = { days: [], mds: [], texts: [], winter: null, catFailed: false, conus: spcInConus(lat, lon) };
            if (!res.conus) return res;
            const dayP = Promise.all([1, 2, 3].map(async d => {
                const L = SPC_LAYERS[d], out = { day: d, cat: null, valid: null, probs: {} };
                try {
                    (await spcQuery(L.cat, lat, lon)).forEach(a => {
                        let code = String(a.label || '').toUpperCase();
                        if (!SPC_CAT[code]) code = SPC_DN[a.dn] || '';
                        const c = SPC_CAT[code];
                        if (c && (!out.cat || c.n > out.cat.n)) { out.cat = { ...c, code }; out.valid = spcTime(a.valid); }
                    });
                } catch (e) {
                    out.failed = true; res.catFailed = true;
                }
                if (out.cat && out.cat.n >= 1) {
                    await Promise.all(Object.keys(L).filter(k => k !== 'cat').map(k => spcQuery(L[k], lat, lon)
                        .then(f => { const m = Math.max(0, ...f.map(spcPct)); if (m) out.probs[k] = m; }).catch(() => {})));
                }
                return out;
            }));
            const mdP = spcProducts('SWOMCD', 15, 8).then(list => {
                const now = Date.now(), seen = new Set();
                return list.map(parseMD).filter(m => {
                    if (!m || seen.has(m.num)) return false;
                    seen.add(m.num);
                    return m.end && m.end > now && m.poly.length >= 3 && spcInPoly(lat, lon, m.poly);
                });
            }).catch(() => []);
            res.days = await dayP;
            if (onDays) onDays(res);
            res.mds = await mdP;
            // outlook discussions for each day that has a severe risk here
            const want = res.days.filter(d => d.cat && d.cat.n >= 1).map(d => d.day);
            res.texts = (await Promise.all(want.map(d => spcProducts('SWODY' + d, 1, 30).then(l => l[0] ? { day: d, text: l[0], issued: spcIssued(l[0]) } : null).catch(() => null)))).filter(Boolean);
            // winter: WPC heavy snow and icing discussion when snow or ice is in play here
            const winterAlerts = (nwsAlerts || []).filter(a => WINTER_RE.test(a.event || ''));
            const snowSoon = (bestBetResults || []).slice(0, 3).some(b => b.bestSnow > 0.1);
            if (winterAlerts.length || snowSoon || res.mds.some(m => WINTER_RE.test(m.concerning))) {
                const t = (await spcProducts('QPFHSD', 1, 24).catch(() => []))[0];
                res.winter = { alerts: winterAlerts.map(a => a.event), text: t || null, issued: t ? spcIssued(t) : null };
            }
            return res;
        }

        async function loadSPC(token, lat, lon) {
            spcData = null;
            refreshSPC();
            let d;
            try { d = await fetchSPC(lat, lon, r => { if (token !== fetchToken) return; spcData = { ...r, mds: [], texts: [], winter: null }; renderActiveAlerts(); refreshSPC(); }); } catch (e) { d = { days: [], mds: [], texts: [], winter: null, catFailed: true, conus: true }; }
            if (token !== fetchToken) return;
            spcData = d;
            renderActiveAlerts();
            refreshSPC();
            try { renderHourlySlider(); renderHero(); } catch (e) {}
        }

        function spcDayLabel(d) {
            const dates = (ensembleData && ensembleData.daily && ensembleData.daily.time) || [];
            const today = dates[0];
            if (d.valid && today) {
                const vd = d.valid.toISOString().slice(0, 10);
                if (vd < today) return 'Tonight';
                if (vd === today) return 'Today';
                return new Date(vd + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long' });
            }
            if (d.day === 1) return 'Today';
            const ds = dates[d.day - 1];
            return ds ? new Date(ds + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long' }) : `Day ${d.day}`;
        }
        function spcHaz(d) {
            const p = d.probs || {}, k = Object.keys(p);
            if (!k.length) return '';
            return ' (' + k.map(x => `${x} ${p[x]}%`).join(', ') + ')';
        }
        function spcFmtTime(dt) {
            if (!dt) return '';
            const tz = ensembleData && ensembleData.timezone;
            return dt.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit', timeZoneName: 'short', ...(tz ? { timeZone: tz } : {}) });
        }
        function spcAlerts() {
            const a = [];
            if (!spcData) return a;
            const risk = spcData.days.filter(d => d.cat && d.cat.n >= 1);
            if (risk.length) {
                const top = risk.reduce((x, y) => y.cat.n > x.cat.n ? y : x);
                a.push({ type: top.cat.n >= 3 || (top.day === 1 && top.cat.n >= 2) ? 'danger' : 'warning', tag: 'SPC',
                    title: `${top.cat.name} of Severe Storms ${spcDayLabel(top)} (${top.cat.n} of 5)`,
                    text: risk.map(d => `${spcDayLabel(d)}: ${d.cat.name}${spcHaz(d)}`).join('. ') + '.',
                    links: [{ label: 'Severe weather discussion', fn: 'openSevere()' }, { label: 'SPC outlook', href: `https://www.spc.noaa.gov/products/outlook/day${top.day}otlk.html` }] });
            }
            spcData.mds.forEach(m => {
                const w = WINTER_RE.test(m.concerning);
                a.push({ type: w ? 'warning' : (m.watchProb >= 60 || /watch \d/i.test(m.concerning) ? 'danger' : 'warning'), tag: 'SPC',
                    title: `Mesoscale Discussion ${m.num}`,
                    text: `${m.concerning || 'Concerning this area'}${m.watchProb != null ? `. Watch probability ${m.watchProb}%` : ''}. Valid until ${spcFmtTime(m.end)}.`,
                    links: [{ label: 'Read the discussion', fn: `openSevere(${m.num})` }, { label: 'SPC page', href: `https://www.spc.noaa.gov/products/md/${(m.end || new Date()).getUTCFullYear()}/md${String(m.num).padStart(4, '0')}.html` }] });
            });
            return a;
        }

        function spcFormat(raw) {
            let t = String(raw || '').replace(/\r/g, '');
            t = t.split(/\n\s*ATTN\.\.\./)[0].split(/\n\s*LAT\.\.\.LON/)[0];
            const hdr = t.search(/\n[ \t]*\d{3,4} [AP]M [A-Z]{3,4} \w{3} \w{3} \d{1,2} \d{4}[ \t]*\n/);
            if (hdr >= 0) t = t.slice(hdr).replace(/^\s*\n[^\n]*\n/, '');
            t = t.replace(/^[ \t]*(?:\.\.\.)?(SUMMARY|DISCUSSION|SYNOPSIS)\.\.\./gm, '.$1...')
                 .replace(/^[ \t]*\.\.\.([^.\n]{2,60})\.\.\.[ \t]*$/gm, '.$1...');
            return formatAFD(t);
        }
        function spcBlock(title, meta, html, link) {
            return `<details class="spc-det"><summary><span>${esc(title)}</span>${meta ? `<span class="spc-meta">${esc(meta)}</span>` : ''}</summary><div class="spc-body">${html}${link ? `<a class="text-blue-400 underline text-xs" href="${link}" target="_blank" rel="noopener">Open at the source</a>` : ''}</div></details>`;
        }
        function spcSectionHTML() {
            if (!nwsOffice) return '';
            const head = (t, cls) => `<h4 class="afd-h ${cls}">${t}</h4>`;
            if (!spcData) return head('Severe Weather', 'spc-h') + '<p class="afd-p text-slate-400 italic">Checking the SPC outlook…</p>';
            if (!spcData.conus) return '';
            let h = head('Severe Weather', 'spc-h');
            const rows = spcData.days.filter(d => d.cat);
            if (rows.length) {
                h += '<div class="spc-days">' + rows.map(d => `<div class="spc-row"><span class="spc-chip" style="background:${d.cat.c}">${d.cat.code}</span><span><b>${spcDayLabel(d)}:</b> ${d.cat.name}${d.cat.n >= 1 ? ` (${d.cat.n} of 5)` : ''}${spcHaz(d).replace(/^ \((.*)\)$/, ', $1')}</span></div>`).join('') + '</div>';
            }
            if (!spcData.days.some(d => d.cat && d.cat.n >= 1)) h += `<p class="afd-p text-slate-300">${spcData.catFailed ? 'The SPC outlook is unavailable right now.' : 'No severe risk from SPC through Day 3.'}</p>`;
            const sev = spcData.mds.filter(m => !WINTER_RE.test(m.concerning)), win = spcData.mds.filter(m => WINTER_RE.test(m.concerning));
            const mdBlock = m => spcBlock(`Mesoscale Discussion ${m.num}${m.concerning ? ': ' + m.concerning : ''}`,
                `Valid until ${spcFmtTime(m.end)}${m.watchProb != null ? `, watch probability ${m.watchProb}%` : ''}`,
                spcFormat(m.text),
                `https://www.spc.noaa.gov/products/md/${(m.end || new Date()).getUTCFullYear()}/md${String(m.num).padStart(4, '0')}.html`);
            h += sev.map(mdBlock).join('');
            h += spcData.texts.map(x => spcBlock(`Day ${x.day} Convective Outlook discussion`, x.issued ? 'Issued ' + spcFmtTime(x.issued) : '', spcFormat(x.text), `https://www.spc.noaa.gov/products/outlook/day${x.day}otlk.html`)).join('');
            if (spcData.winter || win.length) {
                h += head('Winter Weather', 'spc-hw');
                const w = spcData.winter || {};
                if (w.alerts && w.alerts.length) h += `<p class="afd-p text-slate-200">In effect: ${esc([...new Set(w.alerts)].join(', '))}.</p>`;
                h += win.map(mdBlock).join('');
                if (w.text) h += spcBlock('WPC Heavy Snow and Icing Discussion', w.issued ? 'Issued ' + spcFmtTime(w.issued) : '', spcFormat(w.text), 'https://www.wpc.ncep.noaa.gov/discussions/hpcdiscussions.php?disc=qpfhsd');
                else if (!win.length && !(w.alerts && w.alerts.length)) h += '<p class="afd-p text-slate-400">No current WPC winter discussion.</p>';
            }
            return h + '<hr class="afd-rule">';
        }
        function refreshSPC() {
            const box = document.getElementById('spcSection'), badge = document.getElementById('afdSpcBadge');
            if (box) {
                const keep = new Set([...box.querySelectorAll('.spc-det[open] > summary')].map(x => x.textContent.slice(0, 40)));
                box.innerHTML = spcSectionHTML();
                box.querySelectorAll('.spc-det > summary').forEach(x => { if (keep.has(x.textContent.slice(0, 40))) x.parentElement.open = true; });
            }
            if (badge) {
                const r = spcData ? spcData.days.filter(d => d.cat && d.cat.n >= 1) : [];
                const top = r.length ? r.reduce((x, y) => y.cat.n > x.cat.n ? y : x) : null;
                const md = spcData && spcData.mds.length;
                badge.innerHTML = top ? `<span class="spc-chip" style="background:${top.cat.c}">${top.cat.code} ${esc(spcDayLabel(top))}</span>` : '';
                if (md) badge.innerHTML += `<span class="spc-chip" style="background:#93c5fd">MD</span>`;
            }
        }

        // jump from an alert to its discussion in the forecast discussion section
        function openSevere(mdNum) {
            const c = (typeof SECTIONS !== 'undefined') ? SECTIONS.find(x => x.key === 'afd') : null;
            if (c && c._panel && c._panel.classList.contains('collapsed')) setSecOpen(c, true, true);
            const go = () => {
                const dets = [...document.querySelectorAll('#spcSection .spc-det')];
                let target = null;
                if (mdNum != null) target = dets.find(d => (d.querySelector('summary') || {}).textContent && d.querySelector('summary').textContent.includes(`Mesoscale Discussion ${mdNum}`));
                else target = dets.find(d => /Convective Outlook discussion/.test((d.querySelector('summary') || {}).textContent || ''));
                if (target) target.open = true;
                (target || document.getElementById('spcSection') || document.getElementById('afdPanel')).scrollIntoView({ behavior: 'smooth', block: 'start' });
            };
            setTimeout(go, 350);
        }
        function openAFDPanel() {
            const c = (typeof SECTIONS !== 'undefined') ? SECTIONS.find(x => x.key === 'afd') : null;
            if (c && c._panel && c._panel.classList.contains('collapsed')) setSecOpen(c, true, true);
            requestAnimationFrame(() => { const t = document.getElementById('afdText') || document.getElementById('afdPanel'); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
        }

