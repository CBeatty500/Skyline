import sys
W=int(sys.argv[1])
exec(open('run_layout.py').read().split("        await pg.evaluate('window.scrollTo(0,0)')")[0].replace("import sys\nW=int(sys.argv[1]);OUT=sys.argv[2]\n","OUT='d'\n") + """        await pg.add_style_tag(content='.topbar{position:static!important}')
        await pg.evaluate("document.getElementById('feelsLine').style.display='';document.getElementById('feelsLbl').innerText='Wind chill';document.getElementById('currentApparentTemp').innerText='38°F'")
        await pg.locator('.hero-main').screenshot(path=f'feels{W}.png')
        await b.close()
asyncio.run(main())
""")
