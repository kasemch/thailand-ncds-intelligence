import json, os, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT=Path("mobile-evidence")
OUTPUT.mkdir(exist_ok=True)
URL=os.environ.get("NCD_TEST_URL","http://127.0.0.1:8765/")
RECEIPT={"url":URL,"production":"HOLD","native_ipad_safari":"NOT CERTIFIED","runs":[]}
error_count=0

with sync_playwright() as p:
    browser=p.chromium.launch()
    RECEIPT["chromium_version"]=browser.version
    for w,h in [(390,844),(844,390)]:
        ctx=browser.new_context(viewport={"width":w,"height":h},is_mobile=True,has_touch=True,device_scale_factor=1)
        page=ctx.new_page()
        entry={"viewport":[w,h],"panels":[]}
        RECEIPT["runs"].append(entry)
        try:
            response=page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            if not response or not response.ok: raise RuntimeError("HTTP navigation failed")
            page.wait_for_timeout(2800)
            for panel_name in ["overview","explorer","quality"]:
                page.locator("#tab-"+panel_name).click(timeout=12000)
                page.wait_for_timeout(1200)
                panel=page.locator("#"+panel_name)
                panel.locator("h2").first.wait_for(timeout=12000)
                measured=page.evaluate("""id => {
                  const panel=document.getElementById(id);
                  const dims=e=>({client:e.clientWidth,scroll:e.scrollWidth,overflow:Math.max(0,e.scrollWidth-e.clientWidth)});
                  const charts=[...panel.querySelectorAll('.js-plotly-plot')].map(e=>{
                    const r=e.getBoundingClientRect(), pr=panel.getBoundingClientRect();
                    const mode=e.querySelector('.modebar-container');
                    const mr=mode&&mode.getBoundingClientRect();
                    return {id:e.id,...dims(e),left:r.left,right:r.right,
                      beyondPanel:Math.max(0,Math.ceil(r.right-pr.right)),
                      modebarTop:mr?mr.top:null,plotTop:r.top,
                      plotWidth:e._fullLayout?.width||null};
                  });
                  return {viewport:[innerWidth,innerHeight],document:dims(document.documentElement),
                    panel:dims(panel),charts};
                }""",panel_name)
                image=f"{w}x{h}-{panel_name}.png"
                page.screenshot(path=str(OUTPUT/image),full_page=True,scale="css")
                measured["image"]=image
                entry["panels"].append({"name":panel_name,**measured})
                bad=measured["document"]["overflow"] or measured["panel"]["overflow"] or any(c["overflow"] or c["beyondPanel"] for c in measured["charts"])
                if bad: error_count+=1
            entry["status"]="PASS" if all(x["document"]["overflow"]==0 and x["panel"]["overflow"]==0 and not any(c["overflow"] or c["beyondPanel"] for c in x["charts"]) for x in entry["panels"]) else "FAIL"
        except Exception as exc:
            error_count+=1
            entry["status"]="ERROR"
            entry["error"]=str(exc)
        finally:
            ctx.close()
    browser.close()
RECEIPT["status"]="PASS" if error_count==0 else "FAIL"
(OUTPUT/"evidence.json").write_text(json.dumps(RECEIPT,ensure_ascii=False,indent=2))
print(json.dumps(RECEIPT,ensure_ascii=False,indent=2))
sys.exit(0 if error_count==0 else 1)
