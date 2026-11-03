"""Gateway contract oracles bound to the live routes.

The Venice-patch kit asserted ``/api/v1/design`` and ``/api/v1/export/*`` — those
routes do not exist here. The real surface is ``/bridges``, ``/draw``,
``/bills``, ``/qa``, ``/exports``, ``/plugins`` plus ``/health`` and ``/version``
(``apps/api-gateway/bridgecad_api/main.py``). Every upload is an ``.xlsx``
workbook and every error is an RFC 7807 ``application/problem+json`` body
(``bridgecad_api/problems.py``).
"""

from __future__ import annotations

import asyncio
import io
import zipfile

import pytest

pytestmark = pytest.mark.robot


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------
def test_health_lists_loaded_packages(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"]
    assert "bridgecad_core" in body["packages_loaded"]


def test_version_reports_codename(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json()["version"] == "0.1.0-rc1"


def test_openapi_document_builds(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    for route in ("/health", "/bridges/parse", "/draw/gad", "/exports/bundle"):
        assert route in paths


# ---------------------------------------------------------------------------
# Bridges
# ---------------------------------------------------------------------------
def test_parse_returns_project_summary(client, upload):
    r = client.post("/bridges/parse", files=upload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["project"]["span_count"] >= 1
    assert body["project"]["total_length_m"] > 0


def test_validate_returns_score_and_findings(client, upload):
    r = client.post("/bridges/validate", files=upload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert 0 <= body["score"] <= 100
    assert body["findings"], "no QA findings returned"
    for finding in body["findings"]:
        assert finding["check_id"]
        assert finding["severity"] in {"CRITICAL", "HIGH", "WARNING", "MEDIUM", "LOW", "INFO"}


# ---------------------------------------------------------------------------
# Deliverables
# ---------------------------------------------------------------------------
def test_draw_gad_returns_dxf_zip(client, upload):
    r = client.post("/draw/gad", files=upload)
    assert r.status_code == 200, r.text
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert zf.testzip() is None
    sheets = [n for n in zf.namelist() if n.endswith(".dxf")]
    assert sheets, "no DXF sheets in the package"


def test_bills_generate_returns_priced_boq(client, upload):
    r = client.post("/bills/generate", files=upload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sections"], "BOQ has no sections"
    assert body["grand_total"] > 0


def test_qa_report_returns_html(client, upload):
    r = client.post("/qa/report", files=upload)
    assert r.status_code == 200, r.text
    assert "text/html" in r.headers["content-type"]
    assert "<html" in r.text.lower()


def test_export_bundle_contains_all_sections(client, upload):
    r = client.post("/exports/bundle", files=upload)
    assert r.status_code == 200, r.text
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    assert zf.testzip() is None
    names = zf.namelist()
    assert "manifest.json" in names
    assert any(n.startswith("drawings/") and n.endswith(".dxf") for n in names)


# ---------------------------------------------------------------------------
# Plugins
# ---------------------------------------------------------------------------
def test_plugins_are_listed(client):
    r = client.get("/plugins/")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] >= 1
    for plugin in body["plugins"]:
        assert plugin["id"] and plugin["name"] and plugin["version"]


def test_plugin_detail_and_unknown(client):
    listed = client.get("/plugins/").json()["plugins"]
    known = listed[0]["id"]
    r = client.get(f"/plugins/{known}")
    assert r.status_code == 200, r.text
    assert r.json()["id"] == known

    missing = client.get("/plugins/does-not-exist")
    assert missing.status_code == 404


# ---------------------------------------------------------------------------
# Upload hardening + RFC 7807 error shape
# ---------------------------------------------------------------------------
def test_wrong_suffix_is_415_problem_json(client):
    bad = {"file": ("notes.pdf", b"%PDF-1.4 not a workbook", "application/pdf")}
    r = client.post("/bridges/parse", files=bad)
    assert r.status_code == 415, r.text
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    for key in ("type", "title", "status", "detail", "instance"):
        assert key in body, f"missing RFC 7807 field {key}"
    assert body["status"] == 415


def test_missing_file_is_422_problem_json(client):
    r = client.post("/bridges/parse")
    assert r.status_code == 422, r.text
    assert r.headers["content-type"].startswith("application/problem+json")


def test_upload_size_cap_is_enforced():
    """50 MB is the contract; exercise the guard with a small cap so the test
    does not ship a 50 MB payload."""
    from starlette.datastructures import UploadFile as StarletteUploadFile

    from bridgecad_api.problems import (
        MAX_UPLOAD_BYTES,
        UploadTooLargeError,
        enforce_upload_limits,
    )

    assert MAX_UPLOAD_BYTES == 50 * 1024 * 1024

    oversized = StarletteUploadFile(filename="big.xlsx", file=io.BytesIO(b"x" * 11))
    with pytest.raises(UploadTooLargeError):
        asyncio.run(enforce_upload_limits(oversized, max_bytes=10))


def test_invalid_scale_is_400(client, upload):
    """A scale outside 1:10 … 1:2500 is a typo, not an internal error.

    This path raises FastAPI's own ``HTTPException`` (not an ``ApiError``), so it
    keeps FastAPI's ``{"detail": …}`` body rather than the problem+json shape.
    """
    r = client.post("/draw/gad", files=upload, params={"scale": 1})
    assert r.status_code == 400, r.text
    assert "detail" in r.json()
