"""Verify the live drafting demo and review downloads on a static server."""

from __future__ import annotations

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright

DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


def check_demo(url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=os.getenv("BRIDGECAD_TEST_CHROMIUM"))
        with browser.new_context(accept_downloads=True) as context:
            page = context.new_page()
            page.route("**/api/**", lambda route: route.abort())
            page.goto(f"{url}/#home")
            page.get_by_role("link", name="Open live drafting").click()
            expect(page.get_by_role("heading", name="Live drafting")).to_be_visible()
            expect(page.get_by_role("button", name="GAD + plan")).to_have_attribute(
                "aria-pressed", "true"
            )
            svg = page.get_by_role("button", name="SVG", exact=True)
            dxf = page.get_by_role("button", name="DXF", exact=True)
            spans = page.get_by_label("Span lengths in order")
            spans.fill("999999999x12")
            expect(page.get_by_text("Showing the last valid drawing.")).to_be_visible()
            expect(svg).to_be_disabled()
            expect(dxf).to_be_disabled()
            spans.fill("3 x 12")
            for button, suffix in ((svg, "svg"), (dxf, "dxf")):
                expect(button).to_be_enabled()
                with page.expect_download() as event:
                    button.click()
                download = event.value
                assert download.suggested_filename.endswith(f"-review-draft.{suffix}")
                assert b"REVIEW DRAFT" in download.path().read_bytes()


def main() -> None:
    if not (DIST / "index.html").is_file():
        raise SystemExit("Build the frontend before running the browser check.")
    with ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=DIST)
    ) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            check_demo(f"http://127.0.0.1:{server.server_port}")
        finally:
            server.shutdown()
            thread.join()
    print("Browser-only demo, validation and SVG/DXF downloads passed.")


if __name__ == "__main__":
    main()
