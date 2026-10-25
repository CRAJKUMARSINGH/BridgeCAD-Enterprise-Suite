"""
Documentation integrity — one test per audit defect.

Each docstring names the defect number from the 2026-10-22 audit, so a failure
tells you what regressed rather than just where.

These assert the repo IS correct. test_gates_selfcheck.py proves they CAN fail.
"""
from __future__ import annotations

import importlib.util
import re
import tomllib
from pathlib import Path

import pytest
import yaml

from .conftest import (
    PATH_TOKEN,
    STAGED_BY_HOOK,
    fenced_blocks,
    iter_markdown,
    read,
    relative_md_links,
    resolve_link,
)

ROOT_DOCS = ("README.md", "GUIDE.md", "CONTRIBUTING.md", "SECURITY.md",
             "CODE_OF_CONDUCT.md", "DOCS_INDEX.md", "CHANGELOG.md")


# ── defect 01 ────────────────────────────────────────────────────────────────
def test_defect_01_no_phantom_suite_directory(repo_root: Path):
    """No doc or workflow may reference a 'BridgeCAD Enterprise Suite' directory."""
    offenders = []

    for md in iter_markdown(repo_root, include_archive=False):
        for i, line in enumerate(read(md).splitlines(), 1):
            if '"BridgeCAD Enterprise Suite"' in line:
                offenders.append(f"{md.relative_to(repo_root)}:{i}")

    for wf in (repo_root / ".github" / "workflows").glob("*.yml"):
        body = read(wf)
        if 'working-directory: "BridgeCAD Enterprise Suite"' in body:
            offenders.append(str(wf.relative_to(repo_root)))

    assert not offenders, (
        "stale 'BridgeCAD Enterprise Suite' directory reference in:\n  "
        + "\n  ".join(offenders)
    )


# ── defect 02 ────────────────────────────────────────────────────────────────
def test_defect_02_every_relative_markdown_link_resolves(repo_root: Path):
    """Every relative .md link must resolve on disk (hook-staged names excepted)."""
    broken = []

    for md in iter_markdown(repo_root, include_archive=False):
        for target in relative_md_links(read(md)):
            if not target.endswith(".md"):
                continue
            if Path(target).name in STAGED_BY_HOOK:
                continue
            resolved = resolve_link(md, target, repo_root)
            if resolved is not None and not resolved.exists():
                broken.append(f"{md.relative_to(repo_root)} -> {target}")

    assert not broken, "dead relative markdown links:\n  " + "\n  ".join(broken)


# ── defect 03 ────────────────────────────────────────────────────────────────
def test_defect_03_referenced_requirements_files_exist(repo_root: Path):
    """`pip install -r <file>` in any code block must name a real file."""
    missing = []
    pattern = re.compile(r"-r\s+([\w./-]+\.txt)")

    for md in iter_markdown(repo_root, include_archive=False):
        for block in fenced_blocks(read(md)):
            for name in pattern.findall(block):
                if not (repo_root / name).exists():
                    missing.append(f"{md.relative_to(repo_root)} -> {name}")

    assert not missing, "missing requirements files:\n  " + "\n  ".join(missing)


# ── defect 04 ────────────────────────────────────────────────────────────────
def test_defect_04_no_foreign_support_urls(repo_root: Path):
    """Support must route to THIS repo, not the sibling Bridge_GAD repo."""
    offenders = []
    for name in ROOT_DOCS:
        p = repo_root / name
        if p.exists() and "Bridge_GAD_Yogendra_Borse" in read(p):
            offenders.append(name)
    assert not offenders, f"foreign support URLs in: {offenders}"


# ── defect 05 ────────────────────────────────────────────────────────────────
def test_defect_05_no_placeholder_release_urls(repo_root: Path):
    """The github.com/bridgecad/enterprise-suite placeholder must be gone."""
    bad = "github.com/bridgecad/enterprise-suite"
    offenders = [
        str(p.relative_to(repo_root))
        for p in list(repo_root.rglob("*.md")) + [repo_root / "pyproject.toml"]
        if p.is_file()
        and not (set(p.relative_to(repo_root).parts) & {".git", "node_modules", "site"})
        and bad in read(p)
    ]
    assert not offenders, f"placeholder release URLs in: {offenders}"


def test_defect_05b_pyproject_urls_are_correct(repo_root: Path):
    data = tomllib.loads(read(repo_root / "pyproject.toml"))
    urls = data.get("project", {}).get("urls", {})
    assert urls, "pyproject has no [project.urls]"
    wrong = {k: v for k, v in urls.items() if "CRAJKUMARSINGH" not in v}
    assert not wrong, f"pyproject URLs not pointing at the real repo: {wrong}"


# ── defect 06 ────────────────────────────────────────────────────────────────
def test_defect_06_no_your_username_placeholder(repo_root: Path):
    offenders = [
        str(p.relative_to(repo_root))
        for p in list(repo_root.rglob("*.md")) + list(repo_root.rglob("*.toml"))
        if p.is_file()
        and not (set(p.relative_to(repo_root).parts) & {".git", "node_modules", "site"})
        and "YOUR_USERNAME" in read(p)
    ]
    assert not offenders, f"YOUR_USERNAME placeholder in: {offenders}"


# ── defect 07 ────────────────────────────────────────────────────────────────
def test_defect_07_readme_is_suite_first(repo_root: Path):
    """The front door must lead with the Suite and label the legacy app as legacy."""
    body = read(repo_root / "README.md")
    assert "GUIDE.md" in body, "README does not link the master guide"
    assert "repo root" in body.lower(), "README lacks the repo-root orientation note"
    assert "legacy" in body.lower(), "README does not label the legacy generation"
    # The Suite must be named before the legacy app in the orientation table.
    assert body.index("ACTIVE") < body.index("LEGACY")


# ── defect 08 ────────────────────────────────────────────────────────────────
def test_defect_08_zero_install_entry_point_documented(repo_root: Path):
    for name in ("README.md", "GUIDE.md"):
        assert "python -m bridgecad" in read(repo_root / name), (
            f"{name} does not document the zero-install entry point"
        )


# ── defect 09 ────────────────────────────────────────────────────────────────
def test_defect_09_no_conflicting_version_claims(repo_root: Path):
    """README must not claim a version that contradicts the CHANGELOG."""
    readme = read(repo_root / "README.md")
    assert "3.0 Ultimate" not in readme, "README still claims v3.0 Ultimate Edition"
    assert "0.1.0-rc1" in readme or "0.1.0rc1" in readme, "README lacks the rc1 version"


# ── defect 10 ────────────────────────────────────────────────────────────────
def test_defect_10_sheet_names_are_canonical(repo_root: Path):
    """The canonical sheet1..sheet7 names must be documented, and the legacy
    IDX/GAD/TYP naming flagged as legacy."""
    guide = read(repo_root / "GUIDE.md")
    for n in range(1, 8):
        assert f"sheet{n}_" in guide, f"GUIDE.md does not name sheet{n}"
    assert "IDX" in guide and "legacy" in guide.lower()


# ── defect 11 ────────────────────────────────────────────────────────────────
def test_defect_11_no_new_variant_files(repo_root: Path):
    """No X_NEW.md anywhere — retired in favour of archive/."""
    offenders = [p.name for p in repo_root.glob("*_NEW.md")]
    offenders += [p.name for p in (repo_root / "packages").rglob("*_NEW.md")]
    assert not offenders, f"_NEW variant files still present: {offenders}"


def test_defect_11b_no_duplicate_makefiles(repo_root: Path):
    assert (repo_root / "Makefile").exists(), "Makefile missing"
    assert not (repo_root / "Makefile.nested").exists(), "Makefile.nested not retired"


# ── defect 12 ────────────────────────────────────────────────────────────────
def test_defect_12_docs_index_lists_every_doc(repo_root: Path):
    index = read(repo_root / "DOCS_INDEX.md")
    docs_dir = repo_root / "docs"
    missing = [
        p.name for p in sorted(docs_dir.glob("*.md"))
        if p.name not in index
    ]
    assert not missing, f"docs not listed in DOCS_INDEX.md: {missing}"


def test_defect_12b_mkdocs_nav_covers_all_docs(repo_root: Path):
    """Every site doc must be reachable from the nav."""
    cfg = yaml.safe_load(read(repo_root / "mkdocs.yml"))
    nav_text = yaml.safe_dump(cfg.get("nav", []))
    excluded = (cfg.get("exclude_docs") or "")

    orphans = []
    for p in sorted((repo_root / "docs").glob("*.md")):
        if p.name in excluded:
            continue
        if p.name not in nav_text:
            orphans.append(p.name)

    assert not orphans, f"docs missing from mkdocs nav: {orphans}"


# ── defect 13 ────────────────────────────────────────────────────────────────
def test_defect_13_referenced_scripts_exist(repo_root: Path):
    """Any scripts/*.py or scripts/*.sh named in a code block must exist."""
    missing = []
    pattern = re.compile(r"(scripts/[\w.-]+\.(?:py|sh))")

    for md in iter_markdown(repo_root, include_archive=False):
        for block in fenced_blocks(read(md)):
            for ref in pattern.findall(block):
                if not (repo_root / ref).exists():
                    missing.append(f"{md.relative_to(repo_root)} -> {ref}")

    assert not missing, "missing scripts:\n  " + "\n  ".join(missing)


# ── defect 14 ────────────────────────────────────────────────────────────────
def test_defect_14_docs_readme_describes_the_docs_system(repo_root: Path):
    body = read(repo_root / "docs" / "README.md")
    assert "DOCS_INDEX" in body or "docs system" in body.lower(), (
        "docs/README.md still only describes the manual builder"
    )


# ── cross-cutting ────────────────────────────────────────────────────────────
def test_guide_declares_authority(repo_root: Path):
    guide = read(repo_root / "GUIDE.md")
    assert "wins" in guide.lower(), "GUIDE.md does not declare itself authoritative"


def test_guide_has_freshness_table(repo_root: Path):
    assert "verified against" in read(repo_root / "GUIDE.md").lower()


def test_no_pii_in_tracked_docs(repo_root: Path):
    patterns = ("crajkumarsingh@hotmail", "9414163019")
    offenders = []
    for name in ROOT_DOCS:
        p = repo_root / name
        if not p.exists():
            continue
        body = read(p)
        for pat in patterns:
            if pat in body:
                offenders.append(f"{name} :: {pat}")
    assert not offenders, f"PII in tracked docs: {offenders}"


def test_issue_template_labels_are_all_defined(repo_root: Path):
    """A template label that is not in sync_labels.py is silently dropped."""
    spec = importlib.util.spec_from_file_location(
        "sync_labels", repo_root / "scripts" / "sync_labels.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    defined = {name for name, _, _ in mod.LABELS}

    used: set[str] = set()
    for tpl in (repo_root / ".github" / "ISSUE_TEMPLATE").glob("*.yml"):
        data = yaml.safe_load(read(tpl)) or {}
        used.update(data.get("labels") or [])

    undefined = sorted(used - defined)
    assert not undefined, f"labels used but never created: {undefined}"


def test_lychee_config_has_required_keys(repo_root: Path):
    cfg = tomllib.loads(read(repo_root / ".lychee.toml"))
    assert cfg.get("include_fragments") is True, "anchor checking disabled"
    assert cfg.get("exclude_mail") is True
    assert 429 in cfg.get("accept", []), "rate-limit responses treated as dead"


def test_all_workflows_are_valid_yaml(repo_root: Path):
    for wf in (repo_root / ".github" / "workflows").glob("*.yml"):
        data = yaml.safe_load(read(wf))
        assert isinstance(data, dict), f"{wf.name} is not a mapping"
        assert "on" in data or True in data, f"{wf.name} has no trigger"


def test_workflow_script_references_exist(repo_root: Path):
    """A workflow that runs a missing script fails before anything useful."""
    missing = []
    pattern = re.compile(r"(?:python3?|bash|sh)\s+([\w./-]+\.(?:py|sh))")

    for wf in (repo_root / ".github" / "workflows").glob("*.yml"):
        for ref in pattern.findall(read(wf)):
            if not (repo_root / ref).exists():
                missing.append(f"{wf.name} -> {ref}")

    assert not missing, "workflows reference missing scripts:\n  " + "\n  ".join(missing)


def test_archive_has_a_readme(repo_root: Path):
    archive = repo_root / "archive"
    if archive.exists():
        assert (archive / "README.md").exists(), "archive/ has no provenance README"
