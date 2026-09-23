"""Captures the demo screenshots in docs/screenshots/ by driving the Streamlit app with Playwright.

Usage
  streamlit run app.py --server.headless true --server.port 8501 &
  python scripts/make_screenshots.py            # all shots
  python scripts/make_screenshots.py 03 06      # only these
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://localhost:8501"
W, H = 1440, 900

FORM_INPUT = '[data-testid="stForm"] input[type="text"]'
SEND = '[data-testid="stFormSubmitButton"] button'
MSG = '[data-testid="stChatMessage"]'


def ask(page, text: str, timeout: int = 240_000):
    """Submit a query in the Chat tab and wait for the answer to render."""
    before = page.locator(MSG).count()
    box = page.locator(FORM_INPUT).first
    box.click()
    box.fill(text)
    page.locator(SEND).first.click()
    # user + assistant bubbles are appended together after st.rerun()
    page.wait_for_function(
        f"document.querySelectorAll('{MSG}').length >= {before + 2}", timeout=timeout
    )
    page.wait_for_selector('[data-testid="stSpinner"]', state="detached", timeout=timeout)
    page.wait_for_timeout(1500)


def wait_text(page, needle: str, timeout: int = 60_000):
    page.wait_for_function(f"document.body.innerText.includes({needle!r})", timeout=timeout)
    page.wait_for_timeout(500)


def frame_inspector(page, offset: int = 0):
    """Scroll so the Inspector column (intent chart + score table) sits in the viewport."""
    page.evaluate(
        """(off) => {
            const h = [...document.querySelectorAll('h3, [data-testid="stHeading"]')]
                        .find(e => e.innerText.trim().startsWith('Inspector'));
            if (h) h.scrollIntoView({block: 'start'});
            window.scrollBy(0, off);
        }""",
        offset,
    )
    page.wait_for_timeout(900)


def frame_label(page, label: str, offset: int = -90):
    """Scroll so a specific Inspector label (e.g. 'Retrieved passages:') is near the top."""
    page.evaluate(
        """([lbl, off]) => {
            const el = [...document.querySelectorAll('[data-testid="stMarkdownContainer"] p')]
                         .find(e => e.innerText.trim().startsWith(lbl));
            if (!el) return;
            el.scrollIntoView({block: 'start'});
            // Streamlit scrolls inside its own container, so window.scrollBy is a no-op:
            // walk up to the real scrolling ancestor and nudge that instead.
            let p = el.parentElement;
            while (p && p.scrollHeight <= p.clientHeight) p = p.parentElement;
            (p || document.scrollingElement).scrollTop += off;
        }""",
        [label, offset],
    )
    page.wait_for_timeout(900)


def shot(page, name: str):
    path = OUT / name
    page.screenshot(path=str(path))
    print(f"   saved {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")


def routed_model(page) -> str:
    m = re.search(r"Routed to:\s*(\w+)", page.inner_text("body"))
    return m.group(1) if m else "?"


def new_session(page):
    """Clears the chat history so each shot shows only its own exchange.

    Without this the chat column still renders the *previous* shot's answer while the
    Inspector shows the current one, which reads as a mismatch.
    """
    page.get_by_role("button", name="New session").click()
    page.wait_for_timeout(2500)


def set_slider(page, label: str, key: str, steps: int = 0) -> str:
    """Drive a Streamlit slider from the keyboard.

    The thumb is a react-aria <input type="range"> that is visually hidden (1x1 px), so it
    cannot be clicked; focus it directly instead. Home/End jump to min/max, arrows step.
    """
    sl = page.locator('[data-testid="stSlider"]').filter(has_text=label).first
    sl.locator('input[type="range"]').first.evaluate("el => el.focus()")
    page.keyboard.press(key)
    page.wait_for_timeout(400)
    for _ in range(steps):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(150)
    page.wait_for_timeout(1500)
    val = sl.locator('[data-testid="stSliderThumbValue"]').first.inner_text()
    print(f"   {label} -> {val}")
    return val


def open_passage_expanders(page, markers=("[3]",)):
    """Expand the '[n] doc sim=..' retrieved-passage expanders in the Inspector.

    Only the requested markers are opened. Passage [1] is the first chunk of
    01_company_overview.md, which begins with the corpus file's '# Helix Robotics'
    heading; st.write renders that as an H1 that fills the whole viewport and makes the
    screenshot unreadable. [3] is the chunk that actually contains the board-chair sentence.
    """
    n = 0
    heads = page.locator('[data-testid="stExpander"] summary')
    for i in range(heads.count()):
        h = heads.nth(i)
        try:
            # summary text is prefixed by the material-icon ligature ("keyboard_arrow_right")
            txt = h.inner_text()
            if re.search(r"\[\d+\]", txt) and any(mk in txt for mk in markers):
                h.click()
                page.wait_for_timeout(500)
                n += 1
        except Exception:
            continue
    print(f"   expanded {n} passage(s)")
    page.wait_for_timeout(700)


def main():
    want = [a for a in sys.argv[1:]] or ["01", "02", "03", "04", "05", "06"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(URL, wait_until="networkidle", timeout=120_000)
        page.wait_for_selector(FORM_INPUT, timeout=120_000)
        page.wait_for_timeout(2000)
        print("app loaded; Chat tab + variant 'Model D: full system' are the defaults")

        if "01" in want:
            print("01_coding_routing")
            new_session(page)
            ask(page, "Write a Python function that reverses a linked list")
            wait_text(page, "Routed to:")
            print("   routed to:", routed_model(page))
            frame_inspector(page)
            shot(page, "01_coding_routing.png")

        if "02" in want:
            print("02_search_routing")
            new_session(page)
            ask(page, "What is the capital of Australia?")
            wait_text(page, "Routed to:")
            print("   routed to:", routed_model(page))
            frame_inspector(page)
            shot(page, "02_search_routing.png")

        if "03" in want:
            print("03_memory")
            new_session(page)
            ask(page, "My name is Arjun and I work at PayLoop as a data engineer.")
            new_session(page)          # the point of the shot: a brand-new session
            ask(page, "Where do I work?")
            wait_text(page, "Memory hits:")
            frame_inspector(page, offset=170)
            shot(page, "03_memory.png")

        if "04" in want:
            print("04_rag")
            new_session(page)
            ask(page, "Who chairs the Helix board?")
            wait_text(page, "Retrieved passages:")
            open_passage_expanders(page)
            frame_label(page, "Retrieved passages:", offset=-60)
            shot(page, "04_rag.png")

        if "05" in want:
            print("05_writing_routing")
            new_session(page)
            ask(page, "Write a haiku about monsoon rain")
            wait_text(page, "Routed to:")
            print("   routed to:", routed_model(page))
            frame_inspector(page)
            shot(page, "05_writing_routing.png")

        if "06" in want:
            print("06_weights")
            before = routed_model(page)
            set_slider(page, "cost", "End")          # cost     -> 1.00
            set_slider(page, "accuracy", "Home", 2)  # accuracy -> 0.10
            new_session(page)
            ask(page, "Write a haiku about monsoon rain")
            wait_text(page, "Routed to:")
            after = routed_model(page)
            print(f"   routed model: {before} -> {after}")
            frame_inspector(page)
            shot(page, "06_weights.png")

        browser.close()
    print("done")


if __name__ == "__main__":
    main()
