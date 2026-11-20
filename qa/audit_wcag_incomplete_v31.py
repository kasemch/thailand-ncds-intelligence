"""v3.1 non-native evidence clarification; does not certify real iPad Safari."""
import json
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

OUT=Path("qa-v31-evidence")
OUT.mkdir(exist_ok=True)
AXE="node_modules/axe-core/axe.min.js"
RESULT={"version":"3.1","generated_utc":datetime.now(timezone.utc).isoformat(),
"native_ipad_safari":"NOT CERTIFIED","voiceover":"NOT CERTIFIED",
"zoom":"PROXY ONLY: half CSS viewport, NOT device Safari zoom",
"production":"HOLD","checks":[]}
for engine in ("chromium","webkit"):
  with sync_playwright() as p:
    browser=getattr(p,engine).launch()
    for w,h in ((390,844),(844,390)):
      context=browser.new_context(viewport={"width":w,"height":h},
        has_touch=True,is_mobile=True)
      page=context.new_page()
      record={"engine":engine,"viewport":[w,h],"panels":[]}
      RESULT["checks"].append(record)
      try:
        page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded",timeout=50000)
        page.wait_for_timeout(1200)
        page.add_script_tag(path=AXE)
        for name in ("overview","explorer","quality"):
          page.locator("#tab-"+name).click()
          page.wait_for_timeout(400)
          incomplete=page.evaluate("""async () => {
            const r=await axe.run(document,{runOnly:{type:'tag',values:
            ['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}});
            return r.incomplete.map(x=>({id:x.id,impact:x.impact,
            help:x.help,helpUrl:x.helpUrl,
            nodes:x.nodes.map(n=>({target:n.target,html:n.html,
            failureSummary:n.failureSummary,
            any:n.any.map(y=>({id:y.id,message:y.message,data:y.data})),
            all:n.all.map(y=>({id:y.id,message:y.message,data:y.data}))})).slice(0,30)}));
          }""")
          # For keyboard analysis, collect the accessible controls and the first 30 tabbable elements.
          tabseq=page.evaluate("""() => {
            const isVisible = e => !!(e.getClientRects().length);
            return [...document.querySelectorAll('button,a[href],input,select,[tabindex]')]
              .filter(e=>isVisible(e)&&e.tabIndex>=0).slice(0,45)
              .map(e=>({tag:e.tagName,id:e.id,tabIndex:e.tabIndex,
              text:(e.getAttribute('aria-label')||e.textContent||'').trim().slice(0,90)}));
          }""")
          record["panels"].append({"name":name,"incomplete":incomplete,"tab_order_candidates":tabseq})
        # CSS half-viewport is a reflow STRESS TEST only; it is not 200% Safari zoom.
        # Captures computed scroll overflow and screenshots, preserves current working source.
        context.set_viewport_size({"width":max(180,w//2),"height":max(190,h//2)})
        page.wait_for_timeout(500)
        for name in ("overview","explorer","quality"):
          page.locator("#tab-"+name).click()
          page.wait_for_timeout(500)
          measure=page.evaluate("""id=>{
            let p=document.getElementById(id),d=document.documentElement;
            return {width:innerWidth,documentOverflowPx:Math.max(0,d.scrollWidth-d.clientWidth),
              panelOverflowPx:Math.max(0,p.scrollWidth-p.clientWidth),
              chartOverflows:[...p.querySelectorAll('.js-plotly-plot')].map(e=>
                ({id:e.id,overflowPx:Math.max(0,e.scrollWidth-e.clientWidth)}))};
          }""",name)
          record.setdefault("reflow_proxy",[]).append({"name":name,**measure})
          page.screenshot(path=str(OUT/f"{engine}-{w}x{h}-proxy-{name}.png"),
            full_page=True,scale="css")
        record["status"]="RECORDED"
      except Exception as exc:
        record["status"]="INCOMPLETE"
        record["error"]=str(exc)
      finally:
        context.close()
    browser.close()
(OUT/"v31-evidence.json").write_text(json.dumps(RESULT,indent=2,ensure_ascii=False))
print(json.dumps({"native_ipad_safari":RESULT["native_ipad_safari"],
"cases":[{"engine":x["engine"],"viewport":x["viewport"],"status":x.get("status"),
"reflow":[{"name":r["name"],"document_overflow_px":r["documentOverflowPx"]}
 for r in x.get("reflow_proxy",[])],
"incomplete_rules":{p["name"]:[x["id"] for x in p["incomplete"]]
 for p in x.get("panels",[])}} for x in RESULT["checks"]]},indent=2))
raise SystemExit(0 if all(x.get("status")=="RECORDED" for x in RESULT["checks"]) else 1)
