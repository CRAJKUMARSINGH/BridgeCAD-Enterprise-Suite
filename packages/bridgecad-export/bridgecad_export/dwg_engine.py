"""DWG export through the ODA File Converter (W08) — "where licensing permits".

DWG is a closed format. BridgeCAD never ships a DWG writer; it drives the
*Open Design Alliance File Converter*, which the user installs and licenses
themselves. When it is absent the export raises a clear error and the caller
(a CLI, an API route, a test) can fall back to DXF — DXF is the delivered
format and DWG is a convenience conversion.

Discovery order: the ``ODA_FILE_CONVERTER`` environment variable (full path to
the executable), then ``ODAFileConverter`` on ``PATH``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ODA_ENV_VAR = "ODA_FILE_CONVERTER"
"""Environment variable holding the full path to the ODA File Converter."""

ODA_EXECUTABLES = ("ODAFileConverter", "ODAFileConverter.exe")

_MISSING = (
    "DWG export needs the ODA File Converter (proprietary, licensed separately). "
    "Install it, then either put 'ODAFileConverter' on PATH or set "
    f"{ODA_ENV_VAR} to its full path. DXF output remains available without it."
)


def oda_converter() -> Path | None:
    """Return the ODA File Converter executable, or ``None`` when unavailable."""
    override = os.environ.get(ODA_ENV_VAR)
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate
        found = shutil.which(override)
        if found:
            return Path(found)
    for exe in ODA_EXECUTABLES:
        found = shutil.which(exe)
        if found:
            return Path(found)
    return None


def dwg_available() -> bool:
    """True when a licensed ODA File Converter can be located."""
    return oda_converter() is not None


def export_dwg(
    dxf_path: str | Path,
    dwg_path: str | Path,
    *,
    out_version: str = "ACAD2018",
    timeout_s: int = 180,
) -> Path:
    """Convert *dxf_path* to DWG at *dwg_path* using the ODA File Converter.

    Raises ``RuntimeError`` (with install/licensing instructions) when the
    converter cannot be found, and ``FileNotFoundError`` when *dxf_path* does
    not exist.
    """
    converter = oda_converter()
    if converter is None:
        raise RuntimeError(_MISSING)

    src = Path(dxf_path)
    if not src.is_file():
        raise FileNotFoundError(f"DXF not found: {src}")
    dest = Path(dwg_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # The converter works folder-to-folder, so stage a single file either side.
    with tempfile.TemporaryDirectory() as in_dir, tempfile.TemporaryDirectory() as out_dir:
        staged = Path(in_dir) / src.name
        shutil.copy2(src, staged)
        cmd = [
            str(converter),
            in_dir,
            out_dir,
            out_version,
            "DWG",
            "0",  # Recurse
            "1",  # Audit
            "*.dxf",
        ]
        # Fixed argv, no shell interpolation: nothing user-controlled reaches a shell.
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=False)
        produced = sorted(Path(out_dir).glob("*.dwg"))
        if proc.returncode != 0 or not produced:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            raise RuntimeError(
                f"ODA File Converter failed (exit {proc.returncode}): "
                + ("; ".join(detail[-3:]) if detail else "no DWG produced")
            )
        shutil.move(str(produced[0]), dest)
    return dest


__all__ = ["ODA_ENV_VAR", "dwg_available", "export_dwg", "oda_converter"]
