exec(open('run_layout.py').read().split("        await pg.evaluate('window.scrollTo(0,0)')")[0].replace("import sys\nW=int(sys.argv[1]);OUT=sys.argv[2]\n","W=1440;OUT='d'\n") + """        print(await pg.evaluate('''(()=>{const a=obsAdjustedHourly(); if(!a) return 'no adj'; const h=ensembleData.hourly; return bestBetResults.slice(0,3).map(b=>{let m=-99; h.time.forEach((t,j)=>{ if(t.startsWith(b.date)&&+t.slice(11,13)>=6&&+t.slice(11,13)<=21&&a.T[j]!=null) m=Math.max(m,a.T[j]);}); return [b.date, b.bestMax.toFixed(2), m.toFixed(2)];})})()'''))
        await b.close()
asyncio.run(main())
""")
