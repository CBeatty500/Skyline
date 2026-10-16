exec(open('run_layout.py').read().split("        await pg.evaluate('window.scrollTo(0,0)')")[0].replace("import sys\nW=int(sys.argv[1]);OUT=sys.argv[2]\n","W=1440;OUT='d'\n") + """        print(await pg.evaluate('''(()=>{const b=bestBetResults[0]; const before=b.bestMax; const end=new Date(Date.now()+5*3600e3).toISOString();
          nwsForecastData={properties:{periods:[{isDaytime:true,startTime:b.date+'T06:00:00-04:00',endTime:end,temperature:90,temperatureUnit:'F'}]}};
          raiseTodayHigh(); const a=obsAdjustedHourly(),h=ensembleData.hourly; let M=-99; for(let j=a.cur;j<a.T.length;j++){const t=h.time[j]; if(t.startsWith(b.date)&&+t.slice(11,13)>=6&&+t.slice(11,13)<=21&&a.T[j]!=null) M=Math.max(M,a.T[j]);}
          return [before.toFixed(2), b.bestMax.toFixed(2), M.toFixed(2), todayCurveTarget]})()'''))
        await b.close()
asyncio.run(main())
""")
