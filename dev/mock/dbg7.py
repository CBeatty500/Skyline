exec(open('run_layout.py').read().split("        await pg.evaluate('window.scrollTo(0,0)')")[0].replace("import sys\nW=int(sys.argv[1]);OUT=sys.argv[2]\n","W=1440;OUT='d'\n") + """        await pg.add_style_tag(content='.topbar{position:static!important}')
        print(await pg.evaluate('''(()=>{const h=ensembleData.hourly,c=hourlyStart();nwsThunder=new Map();for(let j=c;j<c+60;j++){const ms=Date.parse(h.time[j]+':00Z')-(ensembleData.utc_offset_seconds||0)*1000;nwsThunder.set(ms, j<c+3?10:j<c+8?55:j<c+30?25:0);}
          annotateThunder(); renderDashboard(); return [bestBetResults.slice(0,3).map(b=>b.thunder), typeof ensembleData.utc_offset_seconds]})()'''))
        await pg.wait_for_timeout(500)
        await pg.locator('#sec-hourly').screenshot(path='th_h.png')
        await pg.locator('#sec-forecast').screenshot(path='th_f.png')
        await b.close()
asyncio.run(main())
""")
