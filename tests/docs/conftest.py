"""Shared helpers for the documentation verification suite.

Read-only. Nothing here mutates the repo — mutation lives in
test_gates_selfcheck.py, which works on a throwaway copy.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Staged into docs/ by scripts/mkdocs_hooks.py at build time. A link to one of
# these is not dead — the file just does not exist until the site is built.
STAGED_BY_HOOK = frozenset({
    "guide.md", "index.md", "contributing.md", "changelog.md",
    "security.md", "code-of-conduct.md", "docs-index.md",
})

# Build output and caches — never scan these.
SKIP_DIRS = frozenset({
    ".git", "node_modules", ".venv", "__pycache__",
    "site", "site-api", "_build", "htmlcov", ".benchmarks",
})

FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:")

# Tokens inside code blocks that name a repo path.
PATH_TOKEN = re.compile(
    r"(?<![\w/.-])("
    r"(?:\./|\.\./)?(?:[\w.-]+/)+[\w.-]+"
    r"|[\w.-]+\.(?:py|md|txt|toml|yml|yaml|json|cfg|ini|sh|rst|lock)"
    r")"
)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def iter_markdown(root: Path, *, include_archive: bool = True) -> Iterator[Path]:
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if set(rel.parts) & SKIP_DIRS:
            continue
        if not include_archive and "archive" in rel.parts:
            continue
        yield p


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def fenced_blocks(text: str) -> list[str]:
    return FENCE.findall(text)


def relative_md_links(text: str) -> list[str]:
    """Markdown link targets that point at a repo file (not a URL or anchor)."""
    out: list[str] = []
    for target in MD_LINK.findall(text):
        if target.startswith(("#", "mailto:")) or SCHEME.match(target):
            continue
        clean = target.split("#", 1)[0]
        if clean:
            out.append(clean)
    return out


def resolve_link(doc: Path, target: str, root: Path) -> Path | None:
    """Resolve a relative link. Returns None if it is not a repo-local file."""
    if target.startswith("/"):
        return None
    candidate = (doc.parent / target).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate
