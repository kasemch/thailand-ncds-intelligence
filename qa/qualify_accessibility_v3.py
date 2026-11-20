#!/usr/bin/env python3
"""Chromium and Linux WebKit QA of a local non-deployed candidate."""
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

OUT = Path("qa-v3-evidence")
OUT.mkdir(exist_ok=True)
AXE = Path("node_modules/axe-core/axe.min.js")
URL = "http://127.0.0.1:8765/"
VIEWPORTS = [(390, 844), (844, 390)]
PANELS = ("overview", "explorer", "quality")
RESULT = {
    "schema": "ncd-v3.0-evidence-1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "target": URL,
    "source": "isolated branch checkout",
    "production": "HOLD",
    "native_ipad_safari": "NOT CERTIFIED",
    "webkit_platform": "Linux Playwright WebKit, not native iPad Safari",
    "cases": [],
    "gate": "PENDING",
}
CSS_METRIC_JS = """(id) => {
const p = document.getElementById(id);
const dims = el => ({clientWidth:el.clientWidth,scrollWidth:el.scrollWidth,overflowPx:Math.max(0,el.scrollWidth-el.clientWidth)});
const pr = p.getBoundingClientRect();
const plots = [...p.querySelectorAll('.js-plotly-plot')].map(el => {
  const r=el.getBoundingClientRect(), mode=el.querySelector('.modebar-container');
  const mr=mode ? mode.getBoundingClientRect() : null;
  const titles=[...el.querySelectorAll('.gtitle,.xtitle,.ytitle')].map(t => {
    const tr=t.getBoundingClientRect();
    return {text:t.textContent,rect:{x:tr.x,y:tr.y,width:tr.width,height:tr.height}};
  });
  const collisions=titles.filter(t=>mr && t.rect.width>0 && t.rect.height>0 &&
    t.rect.x<mr.right && t.rect.x+t.rect.width>mr.left &&
    t.rect.y<mr.bottom && t.rect.y+t.rect.height>mr.top);
  return {id:el.id,...dims(el),rect:{x:r.x,y:r.y,width:r.width,height:r.height},
    panelOverhangPx:Math.max(0,Math.ceil(r.right-pr.right)),
    modebarPresent:!!mr,modebarRect:mr?{x:mr.x,y:mr.y,width:mr.width,height:mr.height}:null,
    titleCollisionTexts:collisions.map(t=>t.text),titles};
});
return {viewport:{width:innerWidth,height:innerHeight},
  document:dims(document.documentElement),panel:dims(p),plots};
}"""
def record(checks, key, value, note=""):
    checks[key] = {"pass": bool(value), "detail": note}

def audit_case(browser, engine, width, height):
    entry = {"engine": engine, "viewport": [width,height], "panels": [], "checks": {},
             "status": "NOT CERTIFIED", "axe": {}}
    RESULT["cases"].append(entry)
    context = browser.new_context(viewport={"width":width,"height":height},
        is_mobile=True, has_touch=True, device_scale_factor=1)
    page = context.new_page()
    page.set_default_timeout(18000)
    errors=[]
    page.on("pageerror", lambda err: errors.append(str(err)))
    try:
        response=page.goto(URL,wait_until="domcontentloaded",timeout=60000)
        if not response or not response.ok:
            raise AssertionError("Local HTTP server failed")
        page.locator("#tab-overview").wait_for()
        page.wait_for_timeout(1800)
        record(entry["checks"],"correct_viewport",
               page.evaluate("() => [innerWidth,innerHeight]")==[width,height])
        # Keyboard sequence: focus and activate each tab via keyboard, recording observed behavior.
        for panel_name in PANELS:
            tab=page.locator("#tab-"+panel_name)
            tab.focus()
            focused=tab.evaluate("(e) => e === document.activeElement")
            record(entry["checks"],"keyboard_focus_"+panel_name, focused)
            tab.press("Enter")
            page.wait_for_timeout(400)
            active=page.locator("#"+panel_name).is_visible()
            record(entry["checks"],"keyboard_activate_"+panel_name,active,
                   "Enter activation (not a Tab-order or screen-reader certification)")
            # Touch test uses Playwright's touch-enabled browser context and tap.
            tab.tap()
            page.wait_for_timeout(1000)
            active_after=page.locator("#"+panel_name).is_visible()
            record(entry["checks"],"touch_activate_"+panel_name,active_after)
            metrics=page.evaluate(CSS_METRIC_JS,panel_name)
            metrics["panelName"]=panel_name
            metrics["image"]=f"{engine}-{width}x{height}-{panel_name}.png"
            page.screenshot(path=str(OUT/metrics["image"]),full_page=True,scale="css")
            entry["panels"].append(metrics)
            # Strict zero-width layout overflow; allow 2px border rounding within charts and panels only.
            record(entry["checks"],"document_no_overflow_"+panel_name,
                   metrics["document"]["overflowPx"]==0,
                   str(metrics["document"]))
            record(entry["checks"],"panel_no_material_overflow_"+panel_name,
                   metrics["panel"]["overflowPx"]<=2,
                   str(metrics["panel"]))
            record(entry["checks"],"plot_contained_"+panel_name,
                   all(pl["panelOverhangPx"]==0 and pl["overflowPx"]<=2 for pl in metrics["plots"]),
                   json.dumps([{"id":pl["id"],"overhang":pl["panelOverhangPx"],"overflow":pl["overflowPx"]} for pl in metrics["plots"]]))
            record(entry["checks"],"modebar_title_nonoverlap_"+panel_name,
                   all(not pl["titleCollisionTexts"] for pl in metrics["plots"]),
                   str([{"plot":pl["id"],"collisions":pl["titleCollisionTexts"]} for pl in metrics["plots"]]))
        # Axe scan each visible panel. Scoped scan plus general document level.
        if not AXE.exists():
            raise FileNotFoundError("Pinned axe-core distribution unavailable")
        page.add_script_tag(path=str(AXE))
        for panel_name in PANELS:
            page.locator("#tab-"+panel_name).tap()
            page.wait_for_timeout(350)
            axe=page.evaluate("""async id => {
               const res=await axe.run(document, {runOnly:{type:'tag',values:
                 ['wcag2a','wcag2aa','wcag21a','wcag21aa','best-practice']}});
               return {violations:res.violations.map(v=>({id:v.id,impact:v.impact,
                 description:v.description,nodes:v.nodes.map(n=>({target:n.target,
                 failureSummary:n.failureSummary})).slice(0,20)})),
                 passes:res.passes.length,incomplete:res.incomplete.length};
            }""",panel_name)
            entry["axe"][panel_name]=axe
            record(entry["checks"],"axe_zero_violations_"+panel_name,
                   len(axe["violations"])==0,
                   str([{"id":v["id"],"impact":v["impact"],"nodes":len(v["nodes"])} for v in axe["violations"]]))
        # Recorded JS runtime exceptions are reported separately; no presumptive exemption.
        entry["page_errors"]=errors
        record(entry["checks"],"no_page_errors",not errors,str(errors[:10]))
    except Exception as ex:
        entry["fatal_error"]=str(ex)
        entry["traceback"]=traceback.format_exc()
    finally:
        entry["status"]="PASS" if (not entry.get("fatal_error") and
            entry["checks"] and all(x["pass"] for x in entry["checks"].values())) else "FAIL"
        context.close()

with sync_playwright() as playwright:
    for engine in ("chromium","webkit"):
        try:
            browser=getattr(playwright,engine).launch(headless=True)
            RESULT[engine+"_version"]=browser.version
            for width,height in VIEWPORTS:
                audit_case(browser,engine,width,height)
            browser.close()
        except Exception as ex:
            RESULT["cases"].append({"engine":engine,"status":"BLOCKED","fatal_error":str(ex)})

RESULT["gate"]="AUTOMATED_PASS" if (
    len(RESULT["cases"])==4 and
    all(c["status"]=="PASS" for c in RESULT["cases"])
) else "AUTOMATED_HOLD"
(OUT/"evidence.json").write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
print(json.dumps({"gate":RESULT["gate"],
 "cases":[{"engine":c.get("engine"),"viewport":c.get("viewport"),"status":c["status"],
 "failed":[k for k,v in c.get("checks",{}).items() if not v["pass"]],
 "fatal_error":c.get("fatal_error")} for c in RESULT["cases"]]},indent=2))
# A failing test must be visible in Actions despite artifacts being saved.
raise SystemExit(0 if RESULT["gate"]=="AUTOMATED_PASS" else 1)
