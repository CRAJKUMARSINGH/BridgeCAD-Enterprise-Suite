"""
bridgecad_export.bundler — ZIP bundle creator with manifest.json.
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


def create_bundle(
    output_dir: Path,
    prefix: str,
    results: dict[str, list[Path]],
) -> Path:
    """Create a ZIP bundle containing all generated files + a manifest.

    Parameters
    ----------
    output_dir : Path
    prefix : str
    results : dict
        Keys: "dxf", "bill", "qa" → list of Path objects

    Returns
    -------
    Path
        Path to the created ZIP file.
    """
    bundle_path = output_dir / f"{prefix}_bundle.zip"
    manifest: dict[str, Any] = {
        "generated_at":  datetime.now().isoformat(),
        "prefix":        prefix,
        "contents":      {},
    }

    all_files: list[Path] = []
    for category, paths in results.items():
        manifest["contents"][category] = [p.name for p in paths]
        all_files.extend(paths)

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in all_files:
            if fp.exists():
                # Archive with subfolder structure preserved under output_dir
                try:
                    arcname = fp.relative_to(output_dir)
                except ValueError:
                    arcname = fp.name
                zf.write(fp, arcname)

        # Write manifest
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return bundle_path


# packages/bridgecad-export/bridgecad_export/bundler.py
REPO = Path(__file__).resolve().parents[3]
SPEC = REPO / "tests" / "draw" / "sheets.spec.json"


def review_label(project) -> str:
    """The export label for *project*, derived from the issue state.

    Never typed by hand: a set that still has open blockers is labelled
    honestly, so the bundle cannot claim more than the sheets support.
    """
    from bridgecad_export.revisions import blockers_for, load, manifest_label
    register = load()
    purpose = register["purpose"]
    if blockers_for(purpose).ok:
        return manifest_label(purpose)
    return "Generated — not reviewed for construction"


def build_manifest(project) -> dict:
    """The manifest the bundle carries, derived from the spec and issue state.

    ``scaffold_sheets`` is read from ``tests/draw/sheets.spec.json`` at runtime
    so the manifest cannot drift from the single place scaffold status lives.
    """
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    scaffold_sheets = sorted(
        sheet for sheet, entry in spec["sheets"].items()
        if entry["status"] == "scaffold"
    )
    return {
        "scaffold_sheets": scaffold_sheets,
        "review_label": review_label(project),
    }


__all__ = ["create_bundle", "review_label", "build_manifest"]
