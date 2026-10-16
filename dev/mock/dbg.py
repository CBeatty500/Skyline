import sys
exec(open('run_layout.py').read().split("        await pg.evaluate('window.scrollTo(0,0)')")[0].replace("import sys\nW=int(sys.argv[1]);OUT=sys.argv[2]\n","W=1440;OUT='d'\n") + """        print(await pg.evaluate("(()=>{const c=SECTIONS.find(s=>s.key==='details');c._head.click();const p=c._panel;return [p.className, [...p.children].map(ch=>ch.className+':'+getComputedStyle(ch).display)]})()"))
        await b.close()
asyncio.run(main())
""")
