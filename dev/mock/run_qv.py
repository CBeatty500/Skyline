import asyncio, json
from playwright.async_api import async_playwright
STUB=open('chartstub.js').read(); BASE=open('base.json').read(); MODELS=open('models.json').read()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1440,'height':1000})
        logs=[]; pg.on('pageerror', lambda e: logs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: logs.append(m.type+': '+m.text) if m.type in ('error','warning') else None)
        async def handle(route):
            u=route.request.url
            if 'api.open-meteo.com/v1/forecast' in u and 'models=' in u: await route.fulfill(status=200, content_type='application/json', body=MODELS, headers={'access-control-allow-origin':'*'})
            elif 'api.open-meteo.com/v1/forecast' in u: await route.fulfill(status=200, content_type='application/json', body=BASE, headers={'access-control-allow-origin':'*'})
            elif 'api.weather.gov' in u:
                f = 'points.json' if '/points/' in u else 'fc.json' if u.endswith('/forecast') else 'alerts.json' if '/alerts' in u else 'stations.json' if u.endswith('/stations') else 'latest.json' if u.endswith('/latest') else 'obs.json'
                await route.fulfill(status=200, content_type='application/geo+json', body=open(f).read(), headers={'access-control-allow-origin':'*'})
            elif 'NWSCLI.geojson' in u:
                await route.fulfill(status=200, content_type='application/json', body=open('clinet.json').read(), headers={'access-control-allow-origin':'*'})
            elif 'json/cli.py' in u:
                f = 'cli2026.json' if 'year=2026' in u else 'cli2025.json' if 'year=2025' in u else None
                await route.fulfill(status=200 if f else 404, content_type='application/json', body=open(f).read() if f else '', headers={'access-control-allow-origin':'*'})
            elif 'rcc-acis.org/StnMeta' in u:
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({'meta':[{'name':'WASHINGTON DULLES INTL AP','sids':['93738 1','IAD 3','KIAD 5','IADthr 9'],'state':'VA','ll':[-77.45,38.93]}]}), headers={'access-control-allow-origin':'*'})
            elif 'rcc-acis.org/StnData' in u:
                import urllib.parse as up, datetime as dt, random
                q = dict(up.parse_qsl(up.urlparse(u).query))
                ne = len(q.get('elems','').split(','))
                sd = dt.date(1991,1,1) if q.get('sdate')=='por' else dt.date.fromisoformat(q['sdate']); ed = dt.date.fromisoformat(q['edate'])
                rows=[]; d=sd
                while d<=ed:
                    v=[str(65+(d.day%9)), str(45+(d.day%7)), '0.05' if d.day%4==0 else '0.00', '0.0', '0'][:ne]
                    rows.append([d.isoformat()]+v); d+=dt.timedelta(days=1)
                await route.fulfill(status=200, content_type='application/json', body=json.dumps({'meta':{'name':'DULLES'},'data':rows}), headers={'access-control-allow-origin':'*'})
            elif 'chart' in u and u.endswith('.js'): await route.fulfill(status=200, content_type='application/javascript', body=STUB)
            else: await route.fulfill(status=404, body='', headers={'access-control-allow-origin':'*'})
        await pg.route('**/*', lambda r: asyncio.ensure_future(handle(r)) if not r.request.url.startswith('file:') else asyncio.ensure_future(r.continue_()))
        await pg.goto('file:///mnt/user-data/outputs/skyline.html'); await pg.wait_for_timeout(4000)
        print(await pg.evaluate("[document.getElementById('dashboardContent').className, document.getElementById('toastMessage') && document.getElementById('toastMessage').innerText]"))
        await pg.wait_for_timeout(2000)
        await pg.locator('#sec-quick').screenshot(path='qv0.png'); await pg.evaluate('toggleQuickView()'); await pg.wait_for_timeout(300); await pg.locator('#sec-quick').screenshot(path='qv1.png')
        await pg.locator('.temp-col').screenshot(path='tempcol.png')
        print(await pg.evaluate("[document.querySelector('.temp-col').offsetHeight, document.getElementById('precipTotalsGrid').children.length]"))
        for l in logs[:15]: print(l[:400])
        await b.close()
asyncio.run(main())
