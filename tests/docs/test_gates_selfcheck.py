"""
Layer 2 — prove the gates actually fail when the repo is broken.

Layer 1 asserts the repo is currently correct. If the gate silently stops
working, layer 1 keeps passing forever and you learn nothing. These tests
deliberately break a throwaway copy and assert the gate catches it.

Every test here is a mutation: one small break, one asserted failure.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .conftest import REPO_ROOT

pytestmark = pytest.mark.docs


# ── fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def mini_repo(tmp_path: Path) -> Path:
    """A minimal tree with the shape the path audit cares about."""
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "packages" / "bridgecad-core").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (root / "docs" / "ok.md").write_text(
        "# ok\n\n```bash\npip install -r requirements.txt\n```\n", encoding="utf-8"
    )
    return root


def _audit(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_doc_paths.py"),
         "--root", str(root)],
        capture_output=True, text=True,
    )


def _load_hook():
    spec = importlib.util.spec_from_file_location(
        "mkdocs_hooks", REPO_ROOT / "scripts" / "mkdocs_hooks.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── path audit: the gate must fire ───────────────────────────────────────────
def test_path_audit_passes_on_a_clean_tree(mini_repo: Path):
    result = _audit(mini_repo)
    assert result.returncode == 0, result.stdout + result.stderr


def test_path_audit_catches_phantom_directory(mini_repo: Path):
    """MUTATION: reference a directory that does not exist."""
    (mini_repo / "docs" / "bad.md").write_text(
        "# bad\n\n```bash\ncd BridgeCAD Enterprise Suite\n```\n", encoding="utf-8"
    )
    result = _audit(mini_repo)
    assert result.returncode == 1, "phantom directory not caught"
    assert "BridgeCAD Enterprise Suite" in result.stdout


def test_path_audit_catches_missing_requirements_file(mini_repo: Path):
    """MUTATION: reference requirements_lean.txt, which does not exist."""
    (mini_repo / "docs" / "bad.md").write_text(
        "# bad\n\n```bash\npip install -r requirements_lean.txt\n```\n", encoding="utf-8"
    )
    result = _audit(mini_repo)
    assert result.returncode == 1, "missing requirements file not caught"
    assert "requirements_lean.txt" in result.stdout


def test_path_audit_catches_missing_script_reference(mini_repo: Path):
    """MUTATION: reference a script that was never created."""
    (mini_repo / "docs" / "bad.md").write_text(
        "# bad\n\n```bash\npython scripts/nope.py\n```\n", encoding="utf-8"
    )
    assert _audit(mini_repo).returncode == 1


# ── link rewriting: pure-function mutation tests ─────────────────────────────
def test_rewrite_docs_prefix_is_stripped():
    assert _load_hook()._rewrite("docs/getting-started.md") == "getting-started.md"


def test_rewrite_root_doc_maps_to_staged_name():
    assert _load_hook()._rewrite("../GUIDE.md") == "guide.md"


def test_rewrite_climbing_above_docs_becomes_absolute():
    """REGRESSION: '../../a/b.md' must not be mis-relative-ised into 'a/b.md'."""
    out = _load_hook()._rewrite("../../actions/workflows/suite-ci.yml")
    assert out.startswith("https://github.com/"), out
    assert out.endswith("actions/workflows/suite-ci.yml")


def test_rewrite_archive_becomes_absolute():
    out = _load_hook()._rewrite("archive/GAPS_OPPORTUNITIES_FIXES.md")
    assert out.startswith("https://github.com/")


def test_rewrite_preserves_anchor():
    assert _load_hook()._rewrite("GUIDE.md#section-3") == "guide.md#section-3"


def test_rewrite_leaves_external_urls_alone():
    hook = _load_hook()
    url = "https://example.com/x.md"
    assert hook._rewrite(url) == url
    assert hook._rewrite("#anchor") == "#anchor"


def test_rewrite_is_idempotent_on_staged_names():
    hook = _load_hook()
    once = hook._rewrite("docs/deployment.md")
    assert hook._rewrite(once) == once


# ── defect-02 gate must actually fire ────────────────────────────────────────
def test_dead_link_detection_fires_on_a_broken_link(tmp_path: Path):
    """MUTATION: a doc links a file that does not exist."""
    root = tmp_path / "r"
    root.mkdir()
    (root / "a.md").write_text("[gone](missing.md)\n", encoding="utf-8")

    from .conftest import relative_md_links, resolve_link
    doc = root / "a.md"
    targets = relative_md_links(doc.read_text(encoding="utf-8"))
    assert targets == ["missing.md"]
    assert not resolve_link(doc, targets[0], root).exists()


# ── label gate must fire ─────────────────────────────────────────────────────
def test_label_gate_catches_undefined_label(tmp_path: Path):
    """MUTATION: a template uses a label sync_labels.py never creates."""
    spec = importlib.util.spec_from_file_location(
        "sync_labels", REPO_ROOT / "scripts" / "sync_labels.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    defined = {n for n, _, _ in mod.LABELS}

    assert "bug" in defined
    assert "totally-made-up-label" not in defined


# ── the workflow gate must fire ──────────────────────────────────────────────
def test_workflow_script_gate_catches_missing_file(tmp_path: Path):
    """MUTATION: a workflow runs a script that does not exist."""
    wf = tmp_path / "w.yml"
    wf.write_text("steps:\n  - run: python scripts/ghost.py\n", encoding="utf-8")

    import re
    pattern = re.compile(r"(?:python3?|bash|sh)\s+([\w./-]+\.(?:py|sh))")
    refs = pattern.findall(wf.read_text(encoding="utf-8"))
    assert refs == ["scripts/ghost.py"]
    assert not (tmp_path / refs[0]).exists()


# ── the suite must not silently no-op ────────────────────────────────────────
def test_suite_finds_markdown_to_scan(repo_root: Path):
    """If the globs broke, every test would pass vacuously."""
    from .conftest import iter_markdown
    found = list(iter_markdown(repo_root, include_archive=False))
    assert len(found) >= 10, f"only found {len(found)} markdown files — globs broken?"


def test_repo_root_resolves_correctly():
    assert (REPO_ROOT / "pyproject.toml").exists()
    assert (REPO_ROOT / "scripts").is_dir()
