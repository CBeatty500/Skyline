        // ---------- Collapsible sections: one look, one behavior; open/closed is remembered per section ----------
        const SECTIONS = [
            { key: 'details', panel: () => document.querySelector('#sec-details > .glass-panel'), title: p => p.querySelector('h3') },
            { key: 'radar', panel: () => document.querySelector('#sec-radar > .glass-panel'), title: p => p.querySelector('h3'), closed: true,
              onOpen: () => { try { openRadarMap(); } catch (e) {} }, onClose: () => { try { radarMapStop(); } catch (e) {} } },
            { key: 'hourly', panel: () => document.querySelector('#sec-hourly > .glass-panel'), title: p => p.querySelector('h3 > span') },
            { key: 'graphs', panel: () => document.getElementById('sec-graphs'), title: p => p.querySelector('.graphs-head h3'), onOpen: () => { try { renderCharts(); } catch (e) {} } },
            { key: 'forecast', panel: () => document.querySelector('#sec-forecast > div'), title: p => p.querySelector('h3 > span') },
            { key: 'afd', panel: () => document.getElementById('afdPanel'), head: () => document.getElementById('afdToggle'), title: h => h.querySelector('span'), closed: true,
              onOpen: () => { afdOpen = true; loadAFD(); }, onClose: () => { afdOpen = false; } },
            { key: 'quick2', panel: () => document.getElementById('sec-quick'), head: () => document.getElementById('quickToggle'), title: h => h.querySelector('h3') },
            { key: 'climate', panel: () => document.getElementById('dailyClimatePanel'), title: p => p.querySelector('h3') },
            { key: 'trend', panel: () => { const h = [...document.querySelectorAll('#sec-climate h3')].find(x => /Long-Term Climate Trend/.test(x.textContent)); return h && h.closest('.glass-panel'); },
              title: p => [...p.querySelectorAll('h3')].find(x => /Long-Term/.test(x.textContent)), closed: true },
            { key: 'models', panel: () => document.getElementById('sec-models'), head: () => document.getElementById('maToggle'), title: h => h.querySelector('span > span'), closed: true,
              onOpen: () => { maOpen = true; renderModelAnalysis(); }, onClose: () => { maOpen = false; } }
        ];
        function secState(key, def) { try { const v = localStorage.getItem('skyline:sec:' + key); return v === null ? def : v === '1'; } catch (e) { return def; } }
        function setSecOpen(cfg, open, save) {
            const p = cfg._panel; if (!p) return;
            p.classList.toggle('collapsed', !open);
            if (cfg._head) cfg._head.setAttribute('aria-expanded', String(open));
            if (save) { try { localStorage.setItem('skyline:sec:' + cfg.key, open ? '1' : '0'); } catch (e) {} }
            try { if (open && cfg.onOpen) cfg.onOpen(); if (!open && cfg.onClose) cfg.onClose(); } catch (e) {}
            if (open) setTimeout(() => window.dispatchEvent(new Event('resize')), 30);
        }
        function initSections() {
            SECTIONS.forEach(cfg => {
                const p = cfg.panel(); if (!p || p._sec) return;
                p._sec = true; cfg._panel = p;
                p.classList.add('sec-card', 'glass-panel');
                // the header row: the element holding the title that is a direct child of the panel
                let head = cfg.head ? cfg.head() : null;
                const t0 = cfg.title(head || p);
                if (!head && t0) { head = t0; while (head.parentElement && head.parentElement !== p) head = head.parentElement; }
                if (!head) return;
                cfg._head = head;
                head.classList.add('sec-head');
                head.removeAttribute('onclick'); head.onclick = null;
                const t = cfg.title(head) || t0;
                if (t) t.classList.add('sec-title');
                ['afdChevron', 'quickChevron', 'maChevron'].forEach(id => { const c = head.querySelector('#' + id); if (c) c.remove(); });
                // collapsed: only the title (and anything inside it) and the chevron stay visible
                if (t) {
                    const mark = el => [...el.children].forEach(ch => {
                        if (ch === t || ch.classList.contains('sec-chev')) return;
                        if (ch.contains(t)) { ch.classList.add('sec-tw'); mark(ch); } else ch.classList.add('sec-x');
                    });
                    mark(head);
                }
                const chev = document.createElement('i'); chev.className = 'fa-solid fa-chevron-down sec-chev'; head.appendChild(chev);
                // bodies that used their own hidden switch are now controlled here
                ['afdBody', 'quickBody', 'maBody'].forEach(id => { const b = p.querySelector('#' + id); if (b) b.classList.remove('hidden'); });
                head.setAttribute('role', 'button'); head.tabIndex = 0;
                const toggle = e => {
                    const hit = e.target.closest('button, select, input, a, .rec-btn');
                    if (hit && hit !== head) return;
                    setSecOpen(cfg, p.classList.contains('collapsed'), true);
                };
                head.addEventListener('click', toggle);
                head.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(e); } });
                setSecOpen(cfg, secState(cfg.key, !cfg.closed), false);
            });
        }
        function toggleAFD() { const c = SECTIONS.find(s => s.key === 'afd'); if (c && c._panel) setSecOpen(c, c._panel.classList.contains('collapsed'), true); }
        function toggleQuickView() { const c = SECTIONS.find(s => s.key === 'quick2'); if (c && c._panel) setSecOpen(c, c._panel.classList.contains('collapsed'), true); }
        function toggleModelAnalysis() { const c = SECTIONS.find(s => s.key === 'models'); if (c && c._panel) setSecOpen(c, c._panel.classList.contains('collapsed'), true); }
        initSections();

