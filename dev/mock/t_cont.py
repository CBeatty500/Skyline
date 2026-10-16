import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file:///mnt/user-data/outputs/skyline.html'); await pg.wait_for_timeout(800)
        r=await pg.evaluate("""()=>{
          localStorage.clear(); currentLoc={lat:39.04,lon:-77.49,name:'A'};
          const mk=(p,mx)=>[{date:'2026-10-16',remaining:true,bestMax:mx,bestMin:10,bestPrecip:p,bestRain:p,bestSnow:0,precipProb:51,bestWind:12,bestGust:25},{date:'2026-10-17',bestMax:15,bestMin:5,bestPrecip:0,bestRain:0,bestSnow:0,precipProb:10,bestWind:10,bestGust:20}];
          const out=[];
          bestBetResults=mk(10.9,27.2); applyContinuity(); out.push(['run1',bestBetResults[0].bestPrecip.toFixed(2),bestBetResults[0].bestMax]);
          bestBetResults=mk(10.4,27.4); applyContinuity(); out.push(['run2 small',bestBetResults[0].bestPrecip.toFixed(2),bestBetResults[0].bestMax, JSON.stringify(continuityInfo)]);
          bestBetResults=mk(8.0,28.5); applyContinuity(); out.push(['run3 moderate',bestBetResults[0].bestPrecip.toFixed(2),bestBetResults[0].bestMax.toFixed(2)]);
          bestBetResults=mk(25,28.5); applyContinuity(); out.push(['run4 big',bestBetResults[0].bestPrecip.toFixed(2)]);
          return JSON.stringify(out);}""")
        print(r, errs); await b.close()
asyncio.run(main())
