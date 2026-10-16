import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file:///mnt/user-data/outputs/skyline.html'); await pg.wait_for_timeout(800)
        r=await pg.evaluate("""()=>{
          const time=[]; for(let i=0;i<48;i++) time.push(new Date(Date.UTC(2026,9,16,i)).toISOString().slice(0,13)+':00');
          const pp=time.map((t,i)=> i>=19&&i<=22?45:10), pr=time.map((t,i)=> i>=17&&i<=23?1.5:0);
          ensembleData={hourly:{time,precipitation_probability:pp,precipitation:pr,snowfall:time.map(()=>0),weather_code:time.map((t,i)=>i>=17&&i<=23?63:3),cloud_cover:time.map((t,i)=> i>=12&&i<18?30:75),is_day:time.map((t,i)=>i%24>=7&&i%24<18?1:0)},daily:{time:['2026-10-16','2026-10-17']}};
          const out=[]; for (const h of [5,10,14,19]) { hourlyStart=()=>h; out.push(h+': '+restOfDayPhrase()); }
          ensembleData.hourly.precipitation_probability=time.map(()=>80); ensembleData.hourly.precipitation=time.map(()=>1);
          hourlyStart=()=>5; out.push('allwet: '+restOfDayPhrase());
          return out.join('\\n');}""")
        print(r, errs); await b.close()
asyncio.run(main())
