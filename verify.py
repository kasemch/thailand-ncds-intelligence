import json
import os
from pathlib import Path
from tempfile import mkdtemp
from playwright.sync_api import sync_playwright

URL = "https://kasemch.github.io/thailand-ncds-intelligence/"
OUTPUT = Path(mkdtemp(prefix="ncd-mobile-", dir="."))
RECEIPT = {"url": URL, "production": "HOLD", "native_ipad_safari": "NOT CERTIFIED", "runs": []}

def overview(page, country, year, kpi):
    page.locator("#overview").get_by_text(kpi, exact=True).wait_for()
    page.locator("#trend").get_by_text(country, exact=True).wait_for()
    page.locator("#ranking").get_by_text(f"Country comparison · {year}", exact=True).wait_for()
    assert page.locator("#year option:checked").inner_text() == year
    assert page.locator("#country option:checked").inner_text() == country
    return {"country": country, "year": year, "kpi": kpi,
            "trend_ticks": page.locator("#trend .xtick text").all_text_contents(),
            "ranking": f"Country comparison · {year}"}

def run(browser, width, height, receipt):
    context = browser.new_context(viewport={"width": width, "height": height},
                                  is_mobile=True, has_touch=True, device_scale_factor=1)
    try:
        page = context.new_page()
        page.set_default_timeout(12000)
        response = page.goto(URL, wait_until="domcontentloaded")
        assert response and response.ok, "Live navigation did not return a successful response"
        receipt["actual"] = page.evaluate("() => [innerWidth, innerHeight]")
        assert receipt["actual"] == [width, height], "Unexpected layout viewport"
        receipt["baseline"] = overview(page, "Thailand", "2021", "14.50%")
        page.locator("#year").select_option(label="2000")
        page.locator("#country").select_option(label="Viet Nam")
        receipt["filtered"] = overview(page, "Viet Nam", "2000", "20.10%")
        receipt["panels"] = []
        for name in ("overview", "explorer", "quality"):
            page.locator("#tab-" + name).click()
            panel = page.locator("#" + name)
            panel.locator("h2").first.wait_for()
            if name == "explorer":
                page.locator("#heatmap .xtick text").first.wait_for()
                page.locator("#change").get_by_text("Change from 2000 → 2000", exact=True).wait_for()
            assert page.locator("#year option:checked").inner_text() == "2000"
            assert page.locator("#country option:checked").inner_text() == "Viet Nam"
            metrics = panel.evaluate("""panel => {
              const dimensions = e => ({scrollWidth:e.scrollWidth, clientWidth:e.clientWidth,
                 overflow:Math.max(0,e.scrollWidth-e.clientWidth)});
              return {viewport:[innerWidth,innerHeight], document:dimensions(document.documentElement),
                 panel:dimensions(panel), charts:[...panel.querySelectorAll('.js-plotly-plot')].map(e => ({
                   id:e.id, ...dimensions(e), xLabels:[...e.querySelectorAll('.xtick text')].map(t=>t.textContent),
                   yLabels:[...e.querySelectorAll('.ytick text')].map(t=>t.textContent)
                 }))};
            }""")
            assert metrics["viewport"] == [width, height], "Viewport changed during the run"
            path = OUTPUT / f"{width}x{height}-{name}.png"
            page.screenshot(path=path, scale="css")
            receipt["panels"].append({"name": name, "image": path.name, **metrics})
        page.locator("#tab-overview").click()
        receipt["return"] = overview(page, "Viet Nam", "2000", "20.10%")
        page.reload(wait_until="domcontentloaded")
        receipt["reload"] = overview(page, "Thailand", "2021", "14.50%")
        receipt["status"] = "FAIL_OVERFLOW" if any(
            metric["overflow"] for p in receipt["panels"]
            for metric in [p["document"], p["panel"], *p["charts"]]
        ) else "PASS_AUTOMATED_CHECKS"
    finally:
        context.close()

try:
    with sync_playwright() as playwright:
        executable = os.getenv("NCD_CHROMIUM_EXECUTABLE")
        options = {"executable_path": executable} if executable else {}
        browser = playwright.chromium.launch(**options)
        RECEIPT["chromium_version"] = browser.version
        try:
            for width, height in ((390, 844), (844, 390)):
                result = {"requested": [width, height], "status": "NOT CERTIFIED"}
                RECEIPT["runs"].append(result)
                try:
                    run(browser, width, height, result)
                except Exception as error:
                    result["error"] = str(error)
        finally:
            browser.close()
except Exception as error:
    RECEIPT["launch_error"] = str(error)
finally:
    (OUTPUT / "evidence.json").write_text(json.dumps(RECEIPT, indent=2, ensure_ascii=False))
    print(OUTPUT / "evidence.json")
raise SystemExit(0 if len(RECEIPT["runs"]) == 2 and all(
    run["status"] == "PASS_AUTOMATED_CHECKS" for run in RECEIPT["runs"]
) else 1)
