        window.onload = function() {
            fetchForecastData();
        };

        // ---------- Auto refresh: re-check every source every 10 minutes while the page is open ----------
        let autoRefreshing = false, lastFetchAt = 0, keepScroll = null;
        const REFRESH_MS = 10 * 60 * 1000;
        function saveScroll() {
            const o = {};
            ['forecastGrid', 'hourlyContainer', 'tempChartScroll'].forEach(id => { const el = document.getElementById(id); if (el) o[id] = el.scrollLeft; });
            keepScroll = { o, until: Date.now() + 60000 };
        }
        function restoreScroll() {
            if (!keepScroll || Date.now() > keepScroll.until) { keepScroll = null; return; }
            const k = keepScroll;
            requestAnimationFrame(() => Object.entries(k.o).forEach(([id, x]) => {
                const el = document.getElementById(id); if (!el) return;
                const sb = el.style.scrollBehavior; el.style.scrollBehavior = 'auto'; el.scrollLeft = x; el.style.scrollBehavior = sb;
            }));
        }
        async function autoRefresh() {
            if (autoRefreshing || !currentLoc) return;
            if (document.hidden) return;                       // caught up as soon as the tab is visible again
            if (document.querySelector('.fc-slider.dragging')) return;
            autoRefreshing = true; saveScroll();
            try { await fetchForecastData(); } finally { autoRefreshing = false; }
        }
        setInterval(() => { if (lastFetchAt && Date.now() - lastFetchAt >= REFRESH_MS - 5000) autoRefresh(); }, 60000);
        document.addEventListener('visibilitychange', () => { if (!document.hidden && lastFetchAt && Date.now() - lastFetchAt >= REFRESH_MS) autoRefresh(); });
