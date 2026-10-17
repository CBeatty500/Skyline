// Screenshot of a section of the live app (for checking layout and live layers)
import { chromium } from 'playwright';
import path from 'node:path';
const [lat, lon, name] = (process.env.PLACE || '39.0437,-77.4875,Ashburn, VA').split(',').map((s, i) => i < 2 ? s.trim() : s).reduce((a, s, i) => (i < 2 ? a.push(s) : (a[2] = a[2] ? a[2] + ',' + s : s), a), []);
const browser = await chromium.launch();
for (const [w, h, tag] of [[1280, 1000, 'desk'], [390, 844, 'phone']]) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: tag === 'phone' ? 2 : 1 });
  await page.goto(`file://${path.join(process.cwd(), 'index.html')}?city=${encodeURIComponent(name.trim())}&lat=${lat}&lon=${lon}`);
  await page.waitForFunction(() => typeof bestBetResults !== 'undefined' && bestBetResults.length > 0, null, { timeout: 90000 });
  await page.evaluate(() => { const p = document.querySelector('#sec-radar > .glass-panel'); if (p && p.classList.contains('collapsed')) p.querySelector('.sec-head').click(); });
  await page.waitForTimeout(9000);
  if (process.env.WARN) { await page.click('#rmWarn'); await page.waitForTimeout(6000); }
  await page.locator('#sec-radar').scrollIntoViewIfNeeded();
  await page.locator('#sec-radar').screenshot({ path: `data/shot_${tag}.png` });
  await page.close();
}
await browser.close();
