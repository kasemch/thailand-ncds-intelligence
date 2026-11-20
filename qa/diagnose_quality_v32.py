import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from subprocess import run
p=Path("qa-v32-diagnostic");p.mkdir(exist_ok=True)
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch()
 for width in (195,320):
  ctx=browser.new_context(viewport={"width":width,"height":844},is_mobile=True,has_touch=True)
  pg=ctx.new_page()
  pg.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
  pg.locator("#tab-quality").click()
  pg.wait_for_timeout(900)
  data=pg.evaluate("""() => {
    const panel=document.getElementById('quality'), r=panel.getBoundingClientRect();
    const nodes=[...panel.querySelectorAll('*')];
    return {width:innerWidth,panel:{client:panel.clientWidth,scroll:panel.scrollWidth,
        x:r.x,right:r.right},candidates:nodes.map(e=>{
        const b=e.getBoundingClientRect(),s=getComputedStyle(e);
        return {tag:e.tagName,id:e.id,cls:String(e.className).slice(0,120),
          text:(e.textContent||'').trim().slice(0,65),
          left:b.left,right:b.right,width:b.width,
          scroll:e.scrollWidth,client:e.clientWidth,
          overflowX:s.overflowX,minWidth:s.minWidth,widthCSS:s.width,
          position:s.position,display:s.display,whiteSpace:s.whiteSpace}
       }).filter(o=>o.right>r.right+2 ||o.scroll>o.client+4 ||o.width>r.width+2)
         .sort((a,b)=>b.right-a.right).slice(0,80)};
  }""")
  results.append(data)
  ctx.close()
 browser.close()
(p/"quality-dom.json").write_text(json.dumps(results,indent=2))
for x in results:
 print("WIDTH",x["width"],"PANEL",x["panel"])
 for n in x["candidates"][:25]:
  print(n["tag"],n["id"],n["cls"],"left",round(n["left"]),"right",round(n["right"]),"client",n["client"],"scroll",n["scroll"],"CSS",n["widthCSS"],n["minWidth"],n["overflowX"],n["text"][:35])
