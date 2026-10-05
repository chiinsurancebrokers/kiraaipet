import asyncio, re
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await (await b.new_context(viewport={"width":1100,"height":900})).new_page()
        async def txt(): return await pg.evaluate("document.body.innerText")
        async def click(name, nth=0):
            await pg.get_by_role("button", name=re.compile(name)).nth(nth).click(); await pg.wait_for_timeout(3500)
        await pg.goto("http://localhost:8504/?t=dashboard"); await pg.wait_for_timeout(7000)
        res=[]
        await click("Ξεκίνα με τη νοσηλεύτρια"); t=await txt(); res.append(("start nurse -> chat", "μία ερώτηση τη φορά" in t and "Δημιουργία Κτηνιατρικής" in t))
        await click("Ζωτικά"); t=await txt(); res.append(("evidence vitals", "Ζωτικά & αναπνοές" in t))
        await click("Πίσω στη νοσηλεύτρια"); t=await txt(); res.append(("back to chat", "Δημιουργία Κτηνιατρικής" in t))
        await click("Αρχική"); 
        for label,expect in [("Άνοιγμα →|Open","Ζωτικά & αναπνοές")]:
            pass
        tools=[("Ζωτικά & αναπνοές",0),("Έλεγχος με φωτογραφία",1),("Εργαστηριακές εξετάσεις",2),("Έλεγχος μακροζωίας",3),("Ημερολόγιο συμπτωμάτων",4),("Κτηνίατρος κοντά σου",5),("Ασφάλιση κατοικιδίου",6)]
        for title,i in tools:
            await pg.goto("http://localhost:8504/?t=dashboard"); await pg.wait_for_timeout(6500)
            btns=pg.get_by_role("button", name=re.compile(r"^Άνοιγμα →"))
            await btns.nth(i).click(); await pg.wait_for_timeout(3500)
            t=await txt(); res.append((f"tool {i} -> {title}", title in t))
        await pg.goto("http://localhost:8504/?t=dashboard"); await pg.wait_for_timeout(6500)
        await click("Επείγον"); t=await txt(); res.append(("emergency -> vets", "Κτηνίατρος κοντά σου" in t))
        for r in res: print(("PASS" if r[1] else "FAIL"), r[0])
        await b.close()
asyncio.run(main())
