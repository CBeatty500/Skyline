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

SITE = 'https://weatherisawesome.netlify.app/'
_icon = ("data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%23ffb84d'/%3E%3Cstop offset='1' stop-color='%23ff7a59'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='15' fill='url(%23g)'/%3E%3Ccircle cx='26' cy='26' r='10' fill='%231a1205'/%3E%3Cpath d='M22 48h22a9 9 0 0 0 0-18 12 12 0 0 0-22 4 7 7 0 0 0 0 14z' fill='%23fff7ec'/%3E%3C/svg%3E")
_meta = f'''
    <meta name="description" content="Skyline: a meteorologist's weather dashboard with live station observations, an observation-corrected multi-model forecast, and official climate records.">
    <meta name="theme-color" content="#0b2f63">
    <link rel="icon" href="{_icon}">
    <link rel="apple-touch-icon" href="apple-touch-icon.png">
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
