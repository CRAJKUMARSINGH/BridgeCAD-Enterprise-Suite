"""MkDocs hook: stage root-level docs into docs/ and rewrite their links.

Why: MkDocs serves only docs_dir. GUIDE.md, README.md, CONTRIBUTING.md and
CHANGELOG.md live at the repo root and must appear in the site.

Hazard this exists to solve: once README.md becomes docs/index.md, a link to
`docs/getting-started.md` is wrong — from docs/ it is `getting-started.md`.
Copying without rewriting produces a site full of 404s.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

STAGE = {
    "GUIDE.md": "guide.md",
    "README.md": "index.md",
    "CONTRIBUTING.md": "contributing.md",
    "CHANGELOG.md": "changelog.md",
    "SECURITY.md": "security.md",
    "CODE_OF_CONDUCT.md": "code-of-conduct.md",
    "DOCS_INDEX.md": "docs-index.md",
}

# Rewrite markdown link targets only — never code blocks, where `docs/x.md`
# is a genuine repo path.
LINK = re.compile(r"\]\(([^)]+)\)")

TARGET_MAP = {
    "GUIDE.md": "guide.md",
    "README.md": "index.md",
    "CONTRIBUTING.md": "contributing.md",
    "CONTRIBUTING_NEW.md": "contributing.md",
    "CHANGELOG.md": "changelog.md",
    "SECURITY.md": "security.md",
    "CODE_OF_CONDUCT.md": "code-of-conduct.md",
    "DOCS_INDEX.md": "docs-index.md",
}

REPO = "https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite"


def _rewrite(target: str) -> str:
    """Rewrite a markdown link target for the docs/ location.

    Order matters: check the `../` climbs BEFORE any stripping, or a link that
    climbs above docs/ gets silently mis-relative-ised.
    """
    if target.startswith(("http://", "https://", "#", "mailto:")):
        return target

    anchor = ""
    if "#" in target:
        target, anchor = target.split("#", 1)
        anchor = "#" + anchor

    # docs/x.md -> x.md   (we are already inside docs/)
    if target.startswith("docs/"):
        rest = target[len("docs/") :]
        return TARGET_MAP.get(rest, rest) + anchor

    # archive/ is excluded from the site -> absolute repo URL
    if target.startswith("archive/"):
        return f"{REPO}/blob/main/{target}{anchor}"

    if target.startswith("../"):
        stripped = target[3:]
        # ../docs/x.md
        if stripped.startswith("docs/"):
            rest = stripped[len("docs/") :]
            return TARGET_MAP.get(rest, rest) + anchor
        # ../../a/b.md and deeper -> absolute
        if "/" in stripped:
            return f"{REPO}/blob/main/{stripped}{anchor}"
        # ../GUIDE.md -> guide.md
        return TARGET_MAP.get(stripped, stripped) + anchor

    return TARGET_MAP.get(target, target) + anchor


def on_pre_build(config, **kwargs):  # noqa: ARG001 - MkDocs hook signature
    DOCS.mkdir(exist_ok=True)
    staged = []

    for src_name, dst_name in STAGE.items():
        src = ROOT / src_name
        if not src.exists():
            continue
        body = src.read_text(encoding="utf-8")
        body = LINK.sub(lambda m: f"]({_rewrite(m.group(1))})", body)
        (DOCS / dst_name).write_text(body, encoding="utf-8")
        staged.append(dst_name)

    print(f"[mkdocs] staged {len(staged)} root doc(s): {', '.join(staged)}")
