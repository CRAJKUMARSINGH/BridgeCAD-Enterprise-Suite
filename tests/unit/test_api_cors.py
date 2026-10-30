"""Regression tests for the Suite API gateway's CORS origin resolution (KERO-001).

The legacy surface (``src/bridge_gad/api.py``) refuses a wildcard origin in
production, and README_RAJKUMAR.md §2 documents the same behaviour for the
Suite ("enforced in code"). The active gateway shipped ``allow_origins=["*"]``
with ``allow_credentials=True`` — insecure, and rejected by browsers — until
this fix. These tests pin the hardened behaviour so the wildcard cannot creep
back in.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

REPO = Path(__file__).resolve().parents[2]
_GATEWAY = REPO / "apps" / "api-gateway"


@pytest.fixture(scope="module")
def gateway():
    """Import the gateway with a neutral environment.

    ``main.py`` resolves CORS origins at import time, so the environment must be
    clean before the module is first loaded or a production-like env in the
    caller's shell would make collection itself fail.
    """
    saved = {k: os.environ.pop(k, None) for k in ("ENV", "API_CORS_ORIGINS")}
    try:
        if str(_GATEWAY) not in sys.path:
            sys.path.insert(0, str(_GATEWAY))
        import bridgecad_api.main as api_main

        yield api_main
    finally:
        for key, value in saved.items():
            if value is not None:
                os.environ[key] = value


def test_dev_default_origins_when_unset(gateway, monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("API_CORS_ORIGINS", raising=False)
    assert gateway._cors_origins() == gateway._DEV_ORIGINS


def test_env_origins_are_honoured_outside_production(gateway, monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("API_CORS_ORIGINS", "https://a.example, https://b.example")
    assert gateway._cors_origins() == ["https://a.example", "https://b.example"]


def test_production_requires_explicit_origins(gateway, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("API_CORS_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="must be set"):
        gateway._cors_origins()


def test_production_refuses_wildcard(gateway, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("API_CORS_ORIGINS", "https://a.example,*")
    with pytest.raises(RuntimeError, match="must not contain"):
        gateway._cors_origins()


def test_production_accepts_explicit_allowlist(gateway, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("API_CORS_ORIGINS", "https://bridgecad.example")
    assert gateway._cors_origins() == ["https://bridgecad.example"]


def test_middleware_never_pairs_wildcard_with_credentials(gateway):
    cors = [
        mw
        for mw in gateway.app.user_middleware
        if getattr(mw.cls, "__name__", "") == "CORSMiddleware"
    ]
    assert cors, "CORSMiddleware is not wired into the app"
    kwargs = cors[0].kwargs
    assert kwargs["allow_origins"] != ["*"]
    assert kwargs["allow_credentials"] is False
