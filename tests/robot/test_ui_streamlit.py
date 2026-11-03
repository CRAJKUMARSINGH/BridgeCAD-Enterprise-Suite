"""In-process UI sweep via Streamlit's native ``AppTest``.

The console navigates with a ``st.radio`` ("Navigate") rather than ``st.tabs``,
so the AppTest policy is adjusted accordingly: every radio option is a page, and
each must render without a traceback. No browser and no server, so this is fast
enough for the robot lane.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.robot, pytest.mark.slow]

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

REPO = Path(__file__).resolve().parents[2]
APP = REPO / "apps" / "streamlit-ui" / "app.py"
TIMEOUT = 60


@pytest.fixture
def at():
    """A freshly booted console; each test gets its own state."""
    app = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    app.run()
    return app


def test_app_boots_clean(at):
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.markdown) > 0, "the console rendered nothing"


def test_every_page_renders_without_traceback(at, artifacts):
    pages = list(at.radio[0].options)
    assert pages, "navigation control has no pages"
    for page in pages:
        at.radio[0].set_value(page).run()
        assert not at.exception, f"{page} raised: {[e.value for e in at.exception]}"
    artifacts.dump("ui_pages.json", {"count": len(pages), "pages": pages})


def test_unicode_free_text_is_accepted(at):
    """The drawing page takes a free-text output prefix; unicode must not crash it."""
    page = next((p for p in at.radio[0].options if "Drawing Gen" in p), None)
    if page is None:
        pytest.skip("no drawing page in the console")
    at.radio[0].set_value(page).run()
    if not at.text_input:
        pytest.skip("drawing page has no free-text input")
    at.text_input[0].set_value("पुल–૭").run()
    assert not at.exception, [e.value for e in at.exception]
