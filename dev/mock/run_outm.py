import asyncio, json, re, datetime as dt
exec(open('run.py').read().split('async def main')[0])
now=dt.datetime.utcnow()
def ddhhmm(t): return t.strftime('%d%H%M')
st=now-dt.timedelta(minutes=30); en=now+dt.timedelta(hours=2)
MD=f"""
000
ACUS11 KWNS {ddhhmm(st)}
SWOMCD
SPC MCD {ddhhmm(st)}
VAZ000-MDZ000-

Mesoscale Discussion 2105
NWS Storm Prediction Center Norman OK
0230 PM CDT Fri Oct 16 2026

Areas affected...Northern Virginia and central Maryland

Concerning...Severe potential...Watch likely

Valid {ddhhmm(st)}Z - {ddhhmm(en)}Z

Probability of Watch Issuance...80 percent

SUMMARY...Organized storms will move east across the area with
damaging wind the main threat.

DISCUSSION...A line of storms is moving through the Shenandoah
Valley with strong deep-layer shear in place. MLCAPE near 1500 J/kg.

..Smith.. 10/16/2026

ATTN...WFO...LWX...

LAT...LON   38407800 39507800 39507700 38407700 38407800
"""
MD2=MD.replace('2105','2104').replace('38407800 39507800 39507700 38407700 38407800','40008500 41008500 41008400 40008400')
DY1=f"""
000
ACUS01 KWNS {ddhhmm(now-dt.timedelta(hours=2))}
SWODY1
SPC AC 161630

Day 1 Convective Outlook
NWS Storm Prediction Center Norman OK

Valid 161630Z - 171200Z

...THERE IS A SLIGHT RISK OF SEVERE THUNDERSTORMS FOR THE MID-ATLANTIC...

...SUMMARY...
Scattered damaging wind gusts are possible this afternoon.

...Mid-Atlantic...
A cold front will move east with a line of storms ahead of it.

..Jones.. 10/16/2026
"""
def esri(feats): return json.dumps({'features':[{'attributes':a} for a in feats]})
LAY={1:[{'LABEL':'TSTM','DN':2},{'LABEL':'MRGL','DN':3},{'LABEL':'SLGT','DN':4,'VALID':now.strftime('%Y%m%d')+'1630'}],
     3:[{'label':'0.02'}],5:[{'label':'0.05'}],7:[{'label':'0.15'},{'label':'SIGN'}],
     9:[{'label':'MRGL','valid':(now+dt.timedelta(days=1)).strftime('%Y%m%d')+'1200'}],11:[],13:[{'label':'0.05'}],15:[{'label':'0.05'}],17:[]}
_old=handle_ref=None
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':900})
        logs=[]; pg.on('pageerror', lambda e: logs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: logs.append(m.type+': '+m.text) if m.type in ('error',) else None)
        H={'access-control-allow-origin':'*'}
        async def handle(route):
            u=route.request.url
            m=re.search(r'SPC_wx_outlks/MapServer/(\d+)/query',u)
            if m: await route.fulfill(status=200, content_type='application/json', body=esri(LAY.get(int(m.group(1)),[])), headers=H); return
            if 'afos/retrieve.py' in u:
                body = (MD+'\x03'+MD2) if 'SWOMCD' in u else DY1 if 'SWODY1' in u else DY1.replace('Day 1','Day 2').replace('ACUS01','ACUS02') if 'SWODY2' in u else ''
                await route.fulfill(status=200, content_type='text/plain', body=body, headers=H); return
            if 'api.open-meteo.com/v1/forecast' in u and 'models=' in u: await route.fulfill(status=200, content_type='application/json', body=MODELS, headers=H)
            elif 'api.open-meteo.com/v1/forecast' in u: await route.fulfill(status=200, content_type='application/json', body=BASE, headers=H)
            elif 'api.weather.gov' in u and '/products/' not in u:
                f = 'points.json' if '/points/' in u else 'fc.json' if u.endswith('/forecast') else 'alerts.json' if '/alerts' in u else 'stations.json' if u.endswith('/stations') else 'latest.json' if u.endswith('/latest') else 'obs.json'
                await route.fulfill(status=200, content_type='application/geo+json', body=open(f).read(), headers=H)
            elif 'chart' in u and u.endswith('.js'): await route.fulfill(status=200, content_type='application/javascript', body=STUB)
            else: await route.fulfill(status=404, body='', headers=H)
        await pg.route('**/*', lambda r: asyncio.ensure_future(handle(r)) if not r.request.url.startswith('file:') else asyncio.ensure_future(r.continue_()))
        await pg.goto('file:///mnt/user-data/outputs/skyline.html?city=Ashburn%2C%20VA&lat=39.0437&lon=-77.4875'); await pg.wait_for_timeout(5000)
        print(await pg.evaluate("[currentLoc.lat,currentLoc.lon,nwsOffice, JSON.stringify(spcData && {days:spcData.days, mds:spcData.mds.map(m=>[m.num,m.concerning,m.watchProb,String(m.end)]), texts:spcData.texts.length, winter:spcData.winter})]"))
        print(await pg.evaluate("document.getElementById('heroOutlook').innerText"))
        await pg.evaluate("toggleAFD()"); await pg.wait_for_timeout(800)
        await pg.evaluate("document.querySelectorAll('.spc-det').forEach((d,i)=>{if(i<1)d.open=true}); document.getElementById('afdPanel').scrollIntoView()")
        print(await pg.evaluate("document.getElementById('afdToggle').innerText+'\\n----\\n'+document.getElementById('spcSection').innerText.slice(0,1500)"))
        await pg.evaluate('window.scrollTo(0,0)'); await pg.wait_for_timeout(300); await pg.locator('#sec-now').screenshot(path='hero_m.png')
        for l in logs[:15]: print(l[:400])
        await b.close()
asyncio.run(main())
