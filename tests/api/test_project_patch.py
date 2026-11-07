"""API contract tests for the project session endpoints (Venice patch).

Covers: POST /project/load → token, PATCH /project/{token}/{section}/{field}
with live checks + QA verdict, POST /io/import/{sheet}, POST /draw/preview/{sheet},
and the /projects index (list / duplicate / soft-delete / restore).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("bridgecad_io")

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """TestClient over a temp SQLite index + one uploaded workbook."""
    db = tmp_path_factory.mktemp("db") / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db}"
    for p in (
        REPO / "apps" / "api-gateway",
        REPO / "tests" / "e2e",
        REPO / "packages" / "bridgecad-io",
        REPO / "packages" / "bridgecad-core",
        REPO / "packages" / "bridgecad-infra",
        REPO / "packages" / "bridgecad-draw",
        REPO / "packages" / "bridgecad-bill",
    ):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    import run_e2e  # noqa: PLC0415
    from bridgecad_io.excel_template import generate_template  # noqa: PLC0415
    from fastapi.testclient import TestClient  # noqa: PLC0415

    fixture = json.loads((REPO / "tests" / "e2e" / "fixtures" / "continuous_3x12m.json").read_text())
    project = run_e2e._build_from_fixture(fixture)
    wb = tmp_path_factory.mktemp("wb") / "bridge.xlsx"
    generate_template(wb, project=project)
    payload = wb.read_bytes()

    import bridgecad_api.main as api_main  # noqa: PLC0415

    with TestClient(api_main.app) as c:
        yield c, payload


def test_project_load_and_patch(client):
    c, payload = client
    r = c.post("/project/load", files={"file": ("b.xlsx", payload)})
    assert r.status_code == 200
    token = r.json()["token"]

    r = c.patch(
        f"/project/{token}/substructure/abutment_cap_depth_mm",
        json={"value": 700},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["field"] == "abutment_cap_depth_mm"
    assert body["value"] == 700
    assert isinstance(body["checks"], list)
    assert "score" in body["qa"]


def test_patch_unknown_field_404(client):
    c, payload = client
    r = c.post("/project/load", files={"file": ("b.xlsx", payload)})
    token = r.json()["token"]
    r = c.patch(f"/project/{token}/substructure/not_a_field", json={"value": 1})
    assert r.status_code == 404


def test_import_sheet(client):
    c, payload = client
    r = c.post("/io/import/1", files={"file": ("b.xlsx", payload)})
    assert r.status_code == 200
    body = r.json()
    assert body["sheet"] == 1
    assert "project_code" in body["section"]


def test_import_sheet_missing_404(client):
    c, payload = client
    r = c.post("/io/import/99", files={"file": ("b.xlsx", payload)})
    assert r.status_code == 404


def test_preview_sheet(client):
    c, payload = client
    r = c.post("/draw/preview/5", files={"file": ("b.xlsx", payload)})
    assert r.status_code == 200
    assert "svg" in r.headers.get("content-type", "")
    assert r.text.lstrip().startswith(("<svg", "<?xml"))


def test_project_index_lifecycle(client):
    c, payload = client
    c.post("/project/load", files={"file": ("b.xlsx", payload)})
    rows = c.get("/projects").json()["projects"]
    assert rows, "index should contain the loaded project"
    idx = rows[0]["id"]

    r = c.post(f"/projects/{idx}/duplicate")
    assert r.status_code == 200
    assert r.json()["project"]["origin_project_id"] == idx

    r = c.delete(f"/projects/{idx}")
    assert r.status_code == 200
    slugs = {p["slug"] for p in c.get("/projects").json()["projects"]}
    assert rows[0]["slug"] not in slugs

    r = c.post(f"/projects/{idx}/restore")
    assert r.status_code == 200
