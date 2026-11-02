"""Persona-weighted random UI walker. Writes a replayable JSON trace.

Ported from the Venice-patch robotic test plan, adapted for this flat repo
(no ``BridgeCAD Enterprise Suite/`` subdirectory — the harness sits in
``scripts/robot/``). Needs a running Streamlit console and a Chromium install:

    python -m playwright install chromium
    streamlit run apps/streamlit-ui/app.py --server.port 8517 --server.headless true
    python scripts/robot/run_robot.py --url http://localhost:8517 --out artifacts/robot
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from personas import Tier, num, pick_persona, text


def enabled_widgets(page) -> list[str]:
    return page.evaluate(
        """() => [...document.querySelectorAll(
        '[data-testid="stButton"] button, [data-testid="stNumberInput"] input,'
      + '[data-testid="stTextInput"] input, [data-testid="stSelectbox"] select,'
      + '[data-testid="stSlider"] input, [data-testid="stCheckbox"] input')]
      .filter(el => !el.disabled).map(el => el.getAttribute('data-testid'))"""
    )


def act(page, rng, tier, testid, trace, step):
    kind = testid.replace("st", "").lower()
    try:
        loc = page.locator(f'[data-testid="{testid}"]').first
        if "button" in kind:
            loc.click()
            trace.append({"step": step, "action": "click", "el": testid})
        elif "numberinput" in kind:
            v = num(rng, tier, rng.choice(["span", "width"]))
            loc.fill(v)
            loc.press("Enter")
            trace.append({"step": step, "action": "fill", "el": testid, "value": v})
        elif "textinput" in kind:
            v = text(rng, tier)
            loc.fill(v)
            loc.press("Enter")
            trace.append({"step": step, "action": "fill", "el": testid, "value": v})
        elif "checkbox" in kind:
            loc.click()
            trace.append({"step": step, "action": "toggle", "el": testid})
        page.wait_for_timeout(350)
    except Exception as e:
        trace.append({"step": step, "action": "error", "el": testid, "error": str(e)})


def run(tier: Tier, url: str, out: pathlib.Path) -> bool:
    persona, rng = pick_persona(tier)
    trace: list[dict] = []
    failures: list[dict] = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1440, "height": 900})
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(url, wait_until="networkidle")
        tabs = page.get_by_role("tab")
        for step in range(persona.max_steps):
            r = rng.random()
            if r < persona.w_tab and tabs.count():
                tabs.nth(rng.randrange(tabs.count())).click()
                trace.append({"step": step, "action": "tab"})
            elif r < persona.w_tab + persona.w_interact:
                ws = enabled_widgets(page)
                if ws:
                    act(page, rng, tier, rng.choice(ws), trace, step)
            else:
                page.keyboard.press("End")
            if page.get_by_test_id("stException").count():
                shot = out / f"{tier.value}_step{step}.png"
                page.screenshot(path=str(shot), full_page=True)
                failures.append(
                    {
                        "step": step,
                        "shot": str(shot),
                        "text": page.get_by_test_id("stException").inner_text()[:2000],
                    }
                )
                break
        if errs:
            failures.append({"js_errors": errs})
        b.close()
    report = {
        "persona": tier.value,
        "seed": persona.seed,
        "steps_run": len(trace),
        "failures": failures,
        "trace": trace,
    }
    (out / f"{tier.value}_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return not failures


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8517")
    ap.add_argument("--out", default="artifacts/robot")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ok = all(run(t, a.url, out) for t in Tier)
    print("ROBOT:", "PASS" if ok else "FAIL — see artifacts/robot")
    sys.exit(0 if ok else 1)
