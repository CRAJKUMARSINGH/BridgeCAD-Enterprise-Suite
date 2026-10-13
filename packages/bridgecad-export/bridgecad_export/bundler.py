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


__all__ = ["create_bundle"]
