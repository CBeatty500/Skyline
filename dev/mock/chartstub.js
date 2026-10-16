window.Chart = class {
  constructor(ctx, cfg) {
    this.ctx = ctx; this.config = cfg; const cv = ctx.canvas, par = cv.parentElement;
    cv.width = par.clientWidth; cv.height = par.clientHeight; cv.style.width = cv.width+'px'; cv.style.height = cv.height+'px';
    const n = cfg.data.labels.length, left = 10, right = cv.width - 10, top = 24, bottom = cv.height - 30;
    this.chartArea = { left, right, top, bottom };
    const colW = (right - left) / n;
    const all = cfg.data.datasets.flatMap(d => d.data.filter(v => v !== null && v !== undefined && typeof v === 'number'));
    const mn = Math.min(...all) - 5, mx = Math.max(...all) + 5;
    this.scales = { x: { getPixelForValue: i => left + colW * (i + 0.5) }, y: { getPixelForValue: v => bottom - (v - mn) / (mx - mn) * (bottom - top), ticks: [] } };
    if (cfg.type === 'bar' || (cfg.data.datasets[0] && cfg.data.datasets[0].type === 'bar')) { const y = v => bottom - v / 100 * (bottom - top); this.scales.y.getPixelForValue = y; const d = cfg.data.datasets[0]; ctx.fillStyle = 'rgba(129,140,248,.55)'; this._bars = d.data.map((v, i) => { const x = this.scales.x.getPixelForValue(i); if (v > 0) ctx.fillRect(x - colW * 0.35, y(v), colW * 0.7, y(0) - y(v)); return { x, width: colW * 0.7 }; }); }
    this.getDatasetMeta = () => ({ data: this._bars || [] });
    const pl = (cfg.plugins || []);
    pl.forEach(p => p.afterLayout && p.afterLayout(this));
    pl.forEach(p => p.beforeDatasetsDraw && p.beforeDatasetsDraw(this));
    if (cfg.type === 'line') cfg.data.datasets.forEach(d => { ctx.strokeStyle = d.borderColor; ctx.lineWidth = 2; ctx.beginPath(); let s = false; d.data.forEach((v, i) => { if (typeof v !== 'number') { s = false; return; } const x = this.scales.x.getPixelForValue(i), y = this.scales.y.getPixelForValue(v); s ? ctx.lineTo(x, y) : ctx.moveTo(x, y); s = true; }); ctx.stroke(); });
    pl.forEach(p => p.afterDatasetsDraw && p.afterDatasetsDraw(this));
    ctx.fillStyle = '#cbd5e1'; ctx.font = '10px sans-serif'; cfg.data.labels.forEach((l, i) => { if (i % 3 === 0) ctx.fillText(Array.isArray(l) ? l[0] : l, this.scales.x.getPixelForValue(i) - 8, bottom + 14); });
  }
  destroy() {} update() {}
};
Chart.register = () => {};
