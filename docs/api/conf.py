"""Sphinx config — API reference only. Prose lives in the MkDocs site."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Make every workspace package importable for autodoc.
for pkg in (ROOT / "packages").iterdir():
    if pkg.is_dir():
        sys.path.insert(0, str(pkg))
sys.path.insert(0, str(ROOT))

project = "BridgeCAD Enterprise Suite"
author = "CRAJKUMARSINGH"
copyright = "MIT licensed"
release = "0.1.0rc1"
version = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
    "exclude-members": "__weakref__, model_config, model_fields",
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_rtype = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "furo"
html_static_path = ["_static"]
html_title = f"{project} — API reference"

# Sphinx 8 compat for typehints_format rename.
try:
    autodoc_typehints_format = "short"
except Exception:  # pragma: no cover
    pass
