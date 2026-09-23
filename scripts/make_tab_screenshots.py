"""Captures docs/screenshots/07..12 — the comparison, Results and vs-Perplexity tabs.

Same Playwright approach as scripts/make_screenshots.py (1440x900 viewport), but these
tabs are tall, so the shots are full-page.

Usage
  streamlit run app.py --server.headless true --server.port 8501 &
  python scripts/make_tab_screenshots.py            # all
  python scripts/make_tab_screenshots.py 09 10      # only these
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8501"
W, H = 1440, 900

SPINNER = '[data-testid="stSpinner"]'
PANEL = '[data-testid="stTabPanel"]:visible'


def panel(page):
    return page.locator(PANEL).first


def open_tab(page, name: str):
    page.get_by_role("tab", name=name, exact=True).click()
    page.wait_for_timeout(1800)
    print(f"   tab -> {name}")


def select_option(page, label: str, value: str):
    """Pick a value in a Streamlit selectbox (a react-aria ComboBox)."""
    box = panel(page).locator('[data-testid="stSelectbox"]').filter(has_text=label).first
    box.click()
    page.wait_for_timeout(700)
    page.get_by_role("option", name=value, exact=True).click()
    page.wait_for_timeout(1500)
    print(f"   {label} = {value}")


def click_button(page, name: str):
    panel(page).get_by_role("button", name=name, exact=True).click()
    page.wait_for_timeout(1200)
    print(f"   clicked {name!r}")


def wait_no_spinner(page, timeout: int = 900_000, settle: int = 2500):
    """Block until every st.spinner in the page is gone, then let the DOM settle."""
    page.wait_for_function(
        f"document.querySelectorAll('{SPINNER}').length === 0", timeout=timeout
    )
    page.wait_for_timeout(settle)


# ":visible" is a Playwright pseudo-class and is NOT valid inside document.querySelector,
# so JS-side code finds the shown panel via offsetParent instead.
JS_PANEL = """
  const panels = [...document.querySelectorAll('[data-testid="stTabPanel"]')];
  const p = panels.find(e => e.offsetParent !== null);
"""


def wait_count(page, needle: str, n: int, timeout: int = 900_000):
    """Block until `needle` appears at least n times in the visible tab panel."""
    page.wait_for_function(
        "([needle, n]) => {" + JS_PANEL + """
             if (!p) return false;
             return (p.innerText.split(needle).length - 1) >= n;
           }""",
        arg=[needle, n],
        timeout=timeout,
    )


def shot(page, name: str, full: bool = True, max_h: int = 7000):
    """Save the shot, growing the viewport when the tab is taller than 900 px.

    Streamlit scrolls inside its own container rather than the document, so Playwright's
    full_page=True yields just the viewport. Temporarily resizing the viewport to the
    content height is what actually produces a full-tab image. Width stays at 1440.
    """
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)
    h = H
    if full:
        measured = page.evaluate(
            """() => {
                 const c = document.querySelector('[data-testid="stMain"]');
                 const inner = c ? c.scrollHeight : 0;
                 return Math.max(inner, document.body.scrollHeight, 0);
               }"""
        )
        h = max(H, min(int(measured) + 80, max_h))
    if h != H:
        page.set_viewport_size({"width": W, "height": h})
        page.wait_for_timeout(1800)
    path = OUT / name
    page.screenshot(path=str(path))
    if h != H:
        page.set_viewport_size({"width": W, "height": H})
        page.wait_for_timeout(600)
    print(f"   saved {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB) at {W}x{h}")


def run_compare_models(page, example: str, out: str):
    open_tab(page, "Compare models")
    select_option(page, "Example prompt", example)
    click_button(page, "Run on all models")
    # four model columns, each ending in a "<n>s" caption; the score table renders last
    wait_no_spinner(page)
    page.wait_for_function(
        "() => {" + JS_PANEL + """
              return p && p.querySelectorAll('[data-testid="stDataFrame"]').length >= 1;
            }""",
        timeout=900_000,
    )
    page.wait_for_timeout(1500)
    txt = panel(page).inner_text()
    print("   router picked:",
          next((l for l in txt.splitlines() if "router picks" in l), "?").strip()[:90])
    shot(page, out)


def run_compare_variants(page, question: str, out: str):
    open_tab(page, "Compare A/B/C/D")
    select_option(page, "Question", question)
    click_button(page, "Run through baseline, A, B, C, D")
    wait_no_spinner(page)
    wait_count(page, "memory hits", 5)   # one caption per build
    page.wait_for_timeout(1500)
    shot(page, out)


def main():
    want = sys.argv[1:] or ["07", "08", "09", "10", "11", "12"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(URL, wait_until="networkidle", timeout=120_000)
        page.wait_for_selector('[role="tab"]', timeout=120_000)
        page.wait_for_timeout(2500)

        if "07" in want:
            print("07_compare_models_coding")
            run_compare_models(page, "Coding", "07_compare_models_coding.png")

        if "08" in want:
            print("08_compare_models_search")
            run_compare_models(page, "Search", "08_compare_models_search.png")

        if "09" in want:
            print("09_compare_variants_memory")
            run_compare_variants(page, "Where do I work?", "09_compare_variants_memory.png")

        if "10" in want:
            print("10_compare_variants_rag")
            run_compare_variants(page, "Who chairs the Helix board?", "10_compare_variants_rag.png")

        if "11" in want:
            print("11_results_tab")
            open_tab(page, "Results")
            wait_no_spinner(page)
            page.wait_for_timeout(2500)
            shot(page, "11_results_tab.png")

        if "12" in want:
            print("12_vs_perplexity")
            open_tab(page, "vs Perplexity")
            page.wait_for_timeout(1500)
            shot(page, "12_vs_perplexity.png")

        browser.close()
    print("done")


if __name__ == "__main__":
    main()
