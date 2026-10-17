// Screenshot of a section of the live app (for checking layout and live layers)
import { chromium } from 'playwright';
import path from 'node:path';
const parts = (process.env.PLACE || '39.0437,-77.4875,Ashburn, VA').split(',');
const lat = parts[0].trim(), lon = parts[1].trim(), name = parts.slice(2).join(',').trim();
import fs from 'node:fs';
const log = [];
const browser = await chromium.launch();
for (const [w, h, tag] of [[1280, 1000, 'desk'], [390, 844, 'phone']]) { try {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: tag === 'phone' ? 2 : 1 });
  page.on('console', m => { if (['warning', 'error'].includes(m.type())) log.push(tag + ' ' + m.type() + ': ' + m.text().slice(0, 200)); });
  await page.goto(`file://${path.join(process.cwd(), 'index.html')}?city=${encodeURIComponent(name.trim())}&lat=${lat}&lon=${lon}`);
  await page.waitForFunction(() => typeof bestBetResults !== 'undefined' && bestBetResults.length > 0, null, { timeout: 90000 });
  await page.evaluate(() => { const p = document.querySelector('#sec-radar > .glass-panel'); if (p && p.classList.contains('collapsed')) p.querySelector('.sec-head').click(); });
  await page.waitForTimeout(9000);
  if (process.env.WARN) { await page.evaluate(() => { const c = document.getElementById('rmWarn'); c.checked = true; c.dispatchEvent(new Event('change')); }); await page.waitForTimeout(6000); }
  await page.locator('#sec-radar').scrollIntoViewIfNeeded();
  await page.locator('#sec-radar').screenshot({ path: `data/shot_${tag}.png` });
  await page.close();
} catch (e) { log.push(tag + ': ' + String(e).slice(0, 400)); } }
fs.writeFileSync('data/shot_log.txt', log.join('\n') || 'ok');
await browser.close();
