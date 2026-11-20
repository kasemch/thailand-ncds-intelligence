"""Before/after Chromium + WebKit reflow regression with raw evidence."""
import argparse,json,hashlib,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser()
p.add_argument("--phase",choices=("before","after"),required=True)
a=p.parse_args()
phase=a.phase
OUT=Path("qa-v32-evidence");OUT.mkdir(exist_ok=True)
URL="http://127.0.0.1:8765/"
viewports=(195,320,390,844)
res={"phase":phase,"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
     "source_sha256":hashlib.sha256(Path("index.html").read_bytes()).hexdigest(),
     "native_safari":"NOT CERTIFIED","wcag_full":"NOT CERTIFIED",
     "browser_cases":[]}
with sync_playwright() as playwright:
  for engine in ("chromium","webkit"):
    browser=getattr(playwright,engine).launch()
    for width in viewports:
      height=844 if width<844 else 390
      ctx=browser.new_context(viewport={"width":width,"height":height},
                               is_mobile=True,has_touch=True,device_scale_factor=1)
      page=ctx.new_page()
      case={"engine":engine,"width":width,"height":height,"panels":[]}
      res["browser_cases"].append(case)
      errors=[]
      page.on("pageerror",lambda e:errors.append(str(e)))
      try:
        page.goto(URL,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(1600)
        if phase=="after":
          page.add_script_tag(path="node_modules/axe-core/axe.min.js")
        for name in ("overview","explorer","quality"):
          page.locator("#tab-"+name).click(timeout=15000)
          page.wait_for_timeout(900)
          metrics=page.evaluate("""id=>{
            const node=document.getElementById(id),d=document.documentElement;
            const dim=e=>({client:e.clientWidth,scroll:e.scrollWidth,
              overflow:Math.max(0,e.scrollWidth-e.clientWidth)});
            const pr=node.getBoundingClientRect();
            const plots=[...node.querySelectorAll('.js-plotly-plot')].map(e=>{
              const r=e.getBoundingClientRect(),region=e.closest('.ncd-accessible-scroll');
              const scroll=region?{...dim(region),scrollLeft:region.scrollLeft,
                keyboard:region.tabIndex>=0,ariaLabel:region.getAttribute('aria-label')}:null;
              const mode=e.querySelector('.modebar-container');
              const mr=mode&&mode.getBoundingClientRect();
              const collisions=[...e.querySelectorAll('.gtitle,.xtitle,.ytitle')].filter(t=>{
                if(!mr)return false;const x=t.getBoundingClientRect();
                return x.width>0&&x.height>0&&x.left<mr.right&&x.right>mr.left&&x.top<mr.bottom&&x.bottom>mr.top;
              }).map(t=>t.textContent);
              return {id:e.id,...dim(e),
                beyondPanel:Math.max(0,Math.ceil(r.right-pr.right)),
                region:scroll,modebarTitleCollisions:collisions};
            });
            const regions=[...node.querySelectorAll('.ncd-accessible-scroll')].map(e=>({
               label:e.getAttribute('aria-label'),...dim(e),tabIndex:e.tabIndex,
               children:e.children.length,scrollable:e.scrollWidth>e.clientWidth}));
            return {document:dim(d),panel:dim(node),plots,regions,viewportWidth:innerWidth};
          }""",name)
          metrics["name"]=name
          if phase=="after":
            metrics["axe"]=page.evaluate("""async()=> {
              const r=await axe.run(document,{runOnly:{type:'tag',
                values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
              return {violations:r.violations.map(x=>({id:x.id,
                 impact:x.impact,targets:x.nodes.map(n=>n.target).slice(0,10)})),
                 incomplete:r.incomplete.map(x=>x.id)};
            }""")
            # Verify keyboard-focused scroll region when it has a real overflow.
            if width==195 and name in ("explorer","quality"):
              region=page.locator("#"+name+" .ncd-accessible-scroll").first
              if region.count():
                region.focus()
                metrics["focusRegion"]=region.evaluate("e=>document.activeElement===e")
                metrics["scrollBefore"]=region.evaluate("e=>e.scrollLeft")
                region.press("End")
                page.wait_for_timeout(100)
                metrics["scrollAfter"]=region.evaluate("e=>e.scrollLeft")
            page.screenshot(path=str(OUT/(phase+"-"+engine+"-"+str(width)+"-"+name+".png")),
               scale="css",full_page=True)
          elif width==195:
            page.screenshot(path=str(OUT/(phase+"-"+engine+"-"+str(width)+"-"+name+".png")),
               scale="css",full_page=True)
          case["panels"].append(metrics)
        case["pageErrors"]=errors
        case["status"]="RECORDED"
      except Exception as e:
        case["status"]="ERROR"
        case["error"]=str(e)
      finally:ctx.close()
    browser.close()
(OUT/(phase+".json")).write_text(json.dumps(res,ensure_ascii=False,indent=2))
# Evidence generation is distinct from qualification.
print(json.dumps({"phase":phase,
   "cases":[{"engine":x["engine"],"width":x["width"],"status":x["status"],
     "overflow":[[k["name"],k["document"]["overflow"],k["panel"]["overflow"]] for k in x["panels"]]}
     for x in res["browser_cases"]]},indent=2))
raise SystemExit(0 if len(res["browser_cases"])==8 and all(c["status"]=="RECORDED" for c in res["browser_cases"]) else 1)
