# post-processing: compiled Tailwind (no runtime CDN), page metadata, icons
import subprocess, os, re as _re2
_tw = '/home/claude/twbuild'
open(f'{_tw}/page.html', 'w').write(out)
open(f'{_tw}/tailwind.config.js', 'w').write("""module.exports = {
  content: ['./page.html'],
  darkMode: 'class',
  theme: { extend: { colors: { slate: { 850: '#111827', 950: '#030712' } } } },
  safelist: [
    { pattern: /^(text|bg|border)-(rose|sky|indigo|emerald|amber|slate|teal|cyan|blue)-(200|300|400|500|950)(\\/(20|30|40|60|90))?$/ },
    'hidden', 'ring-1'
  ]
};
""")
open(f'{_tw}/in.css', 'w').write('@tailwind base;\n@tailwind components;\n@tailwind utilities;\n')
subprocess.run(['./tailwindcss', '-c', 'tailwind.config.js', '-i', 'in.css', '-o', 'out.css', '--minify'], cwd=_tw, check=True, capture_output=True)
_css = open(f'{_tw}/out.css').read()
_a = out.index('<script src="https://cdn.tailwindcss.com"></script>')
_b = out.index('</script>', out.index('tailwind.config = {')) + len('</script>')
out = out[:_a] + '<style id="tw">' + _css + '</style>' + out[_b:]
assert 'cdn.tailwindcss.com' not in out and 'tailwind.config' not in out
print('tailwind css bytes', len(_css))

SITE = 'https://cbeatty500.github.io/Skyline/'
_icon = ("data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%23ffb84d'/%3E%3Cstop offset='1' stop-color='%23ff7a59'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='15' fill='url(%23g)'/%3E%3Ccircle cx='26' cy='26' r='10' fill='%231a1205'/%3E%3Cpath d='M22 48h22a9 9 0 0 0 0-18 12 12 0 0 0-22 4 7 7 0 0 0 0 14z' fill='%23fff7ec'/%3E%3C/svg%3E")
_meta = f'''
    <meta name="description" content="Skyline: a meteorologist's weather dashboard with live station observations, an observation-corrected multi-model forecast, and official climate records.">
    <meta name="theme-color" content="#0b2f63">
    <link rel="icon" href="{_icon}">
    <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png?v=2">
    <link rel="manifest" href="manifest.webmanifest">
    <meta name="apple-mobile-web-app-title" content="Best Bet Weather">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Skyline Weather">
    <meta property="og:title" content="Skyline Weather">
    <meta property="og:description" content="Live station observations, an observation-corrected multi-model forecast, and official climate records.">
    <meta property="og:url" content="{SITE}">
    <meta property="og:image" content="{SITE}og-image.png">
    <meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Skyline Weather">
    <meta name="twitter:description" content="Live station observations, an observation-corrected multi-model forecast, and official climate records.">
    <meta name="twitter:image" content="{SITE}og-image.png">'''
out = out.replace('<title>Skyline · Weather</title>', '<title>Skyline · Weather</title>' + _meta, 1)

# ---- no middle dots anywhere in the interface ----
for _a, _b in [
    ('<title>Skyline · Weather</title>', '<title>Skyline Weather</title>'),
    ('`Observed · ${o.stationId}`', '`Observed at ${o.stationId}`'),
    ('`${L.name} · Skyline Weather`', '`${L.name} – Skyline Weather`'),
    ('mb-2">Today · each', 'mb-2">Today: each'),
    ('Next 12 days · model', 'Next 12 days: model'),
    ("`· NWS ${", "`NWS ${"),
    ('<span class="inline-block mx-2.5 opacity-50">·</span>', '<span>, </span>'),
    ('<span class="text-slate-500">·</span> ', '<span class="text-slate-500">,</span> '),
    ('<span class="text-slate-400">· ${formatSnow(dp.v * 2.54)} on ground</span>', '<span class="text-slate-400">(${formatSnow(dp.v * 2.54)} on ground)</span>'),
    ('<span class="text-slate-400">· ${formatSnow(sn.v * 2.54)} on ground</span>', '<span class="text-slate-400">(${formatSnow(sn.v * 2.54)} on ground)</span>'),
    ('Skyline &bull; ', 'Skyline: '),
]:
    out = out.replace(_a, _b)
out = out.replace(' · ', ', ').replace('&middot;', ',')
_left = [m.start() for m in _re2.finditer('·', out)]
print('middle dots left:', len(_left), [out[max(0, i - 40):i + 10] for i in _left[:6]])
# ---- brand: Best Bet Weather (file and repository names stay "skyline" until the site goes public) ----
for _a, _b in [
    ('<title>Skyline Weather</title>', '<title>Best Bet Weather</title>'),
    ('content="Skyline: a meteorologist\'s weather dashboard with live station observations, an observation-corrected multi-model forecast, and official climate records."',
     'content="Best Bet Weather. A forecast you can bet on."'),
    ('content="Skyline Weather"', 'content="Best Bet Weather"'),
    ('aria-label="Skyline"', 'aria-label="Best Bet Weather"'),
    ('<span class="brand-name hidden sm:inline">Skyline</span>', '<span class="brand-name hidden sm:inline">Best Bet Weather</span>'),
    ('>Skyline: NOAA', '>Best Bet Weather: NOAA'),
    ('– Skyline Weather`', '– Best Bet Weather`'),
    ('Let Skyline pick the station again', 'Let the app pick the station again'),
]:
    assert _a in out, _a[:60]
    out = out.replace(_a, _b)
_i = out.index('</style>')
out = out[:_i] + '\n@media (max-width: 1023px) { .brand-name { display: none !important; } }\n' + out[_i:]

# ---- logo (betting chip with a sky inside) and tagline ----
import re as _re3
_LOGO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="38" height="38" aria-hidden="true"><defs><linearGradient id="bbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffc062"/><stop offset="1" stop-color="#ff7a59"/></linearGradient><linearGradient id="bbs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e3a6b"/><stop offset="1" stop-color="#0b1630"/></linearGradient></defs><circle cx="32" cy="32" r="30" fill="url(#bbg)"/><g fill="#fff4e0"><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(0 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(45 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(90 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(135 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(180 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(225 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(270 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(315 32 32)"/></g><circle cx="32" cy="32" r="19.5" fill="url(#bbs)"/><circle cx="32" cy="32" r="19.5" fill="none" stroke="#fff4e0" stroke-width="1.4" stroke-dasharray="2.6 2.6" opacity=".55"/><circle cx="27.5" cy="28.5" r="6.8" fill="#ffb84d"/><path d="M22.5 40.5h18a5.6 5.6 0 0 0 .2-11.2 7.6 7.6 0 0 0-14.6 2.3 4.5 4.5 0 0 0-3.6 8.9z" fill="#eef2f7"/></svg>'
_LOGO_BIG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="76" height="76" aria-hidden="true"><defs><linearGradient id="bwg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffc062"/><stop offset="1" stop-color="#ff7a59"/></linearGradient><linearGradient id="bws" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e3a6b"/><stop offset="1" stop-color="#0b1630"/></linearGradient></defs><circle cx="32" cy="32" r="30" fill="url(#bwg)"/><g fill="#fff4e0"><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(0 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(45 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(90 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(135 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(180 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(225 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(270 32 32)"/><rect x="28.5" y="2.5" width="7" height="9" rx="2" transform="rotate(315 32 32)"/></g><circle cx="32" cy="32" r="19.5" fill="url(#bws)"/><circle cx="32" cy="32" r="19.5" fill="none" stroke="#fff4e0" stroke-width="1.4" stroke-dasharray="2.6 2.6" opacity=".55"/><circle cx="27.5" cy="28.5" r="6.8" fill="#ffb84d"/><path d="M22.5 40.5h18a5.6 5.6 0 0 0 .2-11.2 7.6 7.6 0 0 0-14.6 2.3 4.5 4.5 0 0 0-3.6 8.9z" fill="#eef2f7"/></svg>'
_FAV = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22 width=%2264%22 height=%2264%22 aria-hidden=%22true%22%3E%3Cdefs%3E%3ClinearGradient id=%22fg%22 x1=%220%22 y1=%220%22 x2=%221%22 y2=%221%22%3E%3Cstop offset=%220%22 stop-color=%22%23ffc062%22/%3E%3Cstop offset=%221%22 stop-color=%22%23ff7a59%22/%3E%3C/linearGradient%3E%3ClinearGradient id=%22fs%22 x1=%220%22 y1=%220%22 x2=%220%22 y2=%221%22%3E%3Cstop offset=%220%22 stop-color=%22%231e3a6b%22/%3E%3Cstop offset=%221%22 stop-color=%22%230b1630%22/%3E%3C/linearGradient%3E%3C/defs%3E%3Ccircle cx=%2232%22 cy=%2232%22 r=%2230%22 fill=%22url%28%23fg%29%22/%3E%3Cg fill=%22%23fff4e0%22%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%280 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%2845 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%2890 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%28135 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%28180 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%28225 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%28270 32 32%29%22/%3E%3Crect x=%2228.5%22 y=%222.5%22 width=%227%22 height=%229%22 rx=%222%22 transform=%22rotate%28315 32 32%29%22/%3E%3C/g%3E%3Ccircle cx=%2232%22 cy=%2232%22 r=%2219.5%22 fill=%22url%28%23fs%29%22/%3E%3Ccircle cx=%2232%22 cy=%2232%22 r=%2219.5%22 fill=%22none%22 stroke=%22%23fff4e0%22 stroke-width=%221.4%22 stroke-dasharray=%222.6 2.6%22 opacity=%22.55%22/%3E%3Ccircle cx=%2227.5%22 cy=%2228.5%22 r=%226.8%22 fill=%22%23ffb84d%22/%3E%3Cpath d=%22M22.5 40.5h18a5.6 5.6 0 0 0 .2-11.2 7.6 7.6 0 0 0-14.6 2.3 4.5 4.5 0 0 0-3.6 8.9z%22 fill=%22%23eef2f7%22/%3E%3C/svg%3E'
out = out.replace('<span class="brand-mark"><i class="fa-solid fa-cloud-sun"></i></span>', '<span class="brand-mark">' + _LOGO + '</span>', 1)
out = _re3.sub(r'<link rel="icon" href="[^"]*">', '<link rel="icon" href="' + _FAV.replace('\\', '\\\\') + '">', out, count=1)
assert '<i class="fa-solid fa-cloud-sun text-6xl mb-5 text-amber-300"></i>' in out
out = out.replace('<i class="fa-solid fa-cloud-sun text-6xl mb-5 text-amber-300"></i>', '<div class="flex justify-center mb-5">' + _LOGO_BIG + '</div>', 1)
out = out.replace('>The Best Bet Forecast.</h2>', '>Best Bet Weather</h2>', 1)
_i = out.index('</style>')
out = out[:_i] + '\n.brand-mark { background: none !important; width: 38px; height: 38px; } .brand-mark svg { display: block; }\n' + out[_i:]

# the page must start with the doctype: nothing stray before it (a find-and-replace with an empty pattern would put text there)
assert out.lstrip().startswith('<!DOCTYPE html>'), 'stray text before <!DOCTYPE html>: ' + out[:120]
