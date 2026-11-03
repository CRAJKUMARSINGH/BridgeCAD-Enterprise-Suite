"""Fixtures for the robotic oracle lane (``tests/robot``).

Retargeted to the *live* contract. The Venice-patch kit in
``CODE-JUNCTION/Venice-patch/instructions.txt`` was written against an
illustrative surface (``design_girder()``, ``/api/v1/design``,
``/api/v1/export/*``) that this tree never implemented. The oracles here bind
instead to what actually ships:

* engine  — ``bridgecad_core`` public exports (validation, geometry, quantities,
  standards)
* API     — the real FastAPI app in ``apps/api-gateway/bridgecad_api/main.py``
* fixtures — the canonical ``tests/e2e`` project loader, reused via importlib so
  the builder lives in exactly one place.

The lane needs the ``dev, api, ui, draw`` extras (notably ``httpx`` for
``TestClient`` and ``ezdxf`` for the drawing oracles) and is therefore excluded
from the default ``suite-ci.yml`` unit job and run by ``robot.yml`` instead.
"""

from __future__ import annotations

import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "e2e" / "fixtures" / "simple_12m.json"
E2E_RUNNER = REPO / "tests" / "e2e" / "run_e2e.py"
ARTIFACTS = REPO / "artifacts" / "robot"

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _load_project():
    """Build a validated ``BridgeProject`` from the canonical fixture JSON.

    Reuses ``tests/e2e/run_e2e.py:_build_from_fixture`` through importlib — the
    same technique ``tests/unit/conftest.py`` and ``tests/draw/contract.py`` use.
    """
    spec = importlib.util.spec_from_file_location("bridgecad_e2e_fixtures_robot", E2E_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return module._build_from_fixture(data)


@pytest.fixture(scope="session")
def project():
    """A valid 1 × 12 m simple-span ``BridgeProject`` shared across the session."""
    return _load_project()


@pytest.fixture
def blank_project():
    """A fresh, isolated copy of the canonical project for mutation oracles."""
    return _load_project()


@pytest.fixture
def span_variant(project):
    """Factory returning a copy of ``project`` with a rewritten span layout.

    Keeps ``span_count`` consistent with ``len(span_lengths_m)`` — the model
    validates the two against each other.
    """

    def _make(lengths: list[float]):
        clone = project.model_copy(deep=True)
        clone.geometry_input = clone.geometry_input.model_copy(
            update={
                "span_count": len(lengths),
                "span_lengths_m": [Decimal(str(x)) for x in lengths],
            }
        )
        return clone

    return _make


@pytest.fixture(scope="session")
def api_app():
    """The real ASGI application object from the gateway."""
    pytest.importorskip("fastapi")
    from bridgecad_api.main import app

    return app


@pytest.fixture
def client(api_app):
    """``TestClient`` against the real app, with server exceptions surfaced as
    responses rather than raised — the problem handlers own the error shape."""
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    with TestClient(api_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def xlsx_bytes(project) -> bytes:
    """The canonical workbook for ``project``.

    ``.xlsx`` is the only suffix the gateway accepts, so every upload oracle
    round-trips through the real writer rather than a hand-rolled fixture.
    """
    pytest.importorskip("openpyxl")
    import tempfile

    from bridgecad_io import write_excel

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "project.xlsx"
        write_excel(project, path)
        return path.read_bytes()


@pytest.fixture
def upload(xlsx_bytes):
    """Ready-made ``files=`` payload for the gateway upload routes."""
    return {"file": ("project.xlsx", xlsx_bytes, XLSX_MIME)}


@pytest.fixture(scope="session")
def artifacts():
    """Minimal JSON artifact sink under the git-ignored ``artifacts/robot/``."""

    class _Sink:
        root = ARTIFACTS

        @staticmethod
        def dump(name: str, payload) -> Path:
            ARTIFACTS.mkdir(parents=True, exist_ok=True)
            path = ARTIFACTS / name
            path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            return path

    return _Sink()
