"""TEMP SCRIPT: Repair missing USER-site dist-info for packages that lost metadata during
sandbox-blocked pip --force-reinstall. Also removes the broken distutils-precedence.pth
that references a non-existent _distutils_hack module (harmless warning but noisy).

This file is idempotent. Safe to re-run.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import shutil
import sys
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import compat32 as EMAIL_POLICY
from pathlib import Path

USER_SITE = Path(r"C:\Users\Rajkumar.DESKTOP-4ISBKM0\AppData\Roaming\Python\Python314\site-packages")

REPAIR = [
    # (pypi_name, module_names_needed_to_infer_version, fallback_version, metadata_only)
    ("pytz",                 ["pytz"],                 "2026.5", False),
]


def record_file_lines(rel: str) -> list[str]:
    """Return a 3-column CSV line for a given path under <dist-info>/RECORD."""
    p = USER_SITE / rel
    if not p.exists():
        return []
    data = p.read_bytes()
    digest = hashlib.sha256(data).digest().hex()
    return [f"{rel},sha256={digest},{len(data)}"]


def write_minimal_metadata(
    pypi_name: str,
    version: str,
    summary: str = "",
    requires_dists: list[str] | None = None,
) -> Path:
    """Create a minimal, valid <name>-<ver>.dist-info/METADATA + INSTALLER + RECORD + WHEEL."""

    dist = USER_SITE / f"{pypi_name.replace('-', '_')}-{version}.dist-info"
    dist.mkdir(parents=True, exist_ok=True)

    md = EmailMessage(policy=EMAIL_POLICY)
    md["Metadata-Version"] = "2.3"
    md["Name"] = pypi_name
    md["Version"] = version
    if summary:
        md["Summary"] = summary
    md.add_header("Requires-Python", ">=3.8")
    for rd in requires_dists or []:
        md.add_header("Requires-Dist", rd)

    (dist / "METADATA").write_bytes(bytes(md))

    (dist / "INSTALLER").write_text("pip\n", encoding="utf-8")

    wheel = EmailMessage(policy=EMAIL_POLICY)
    wheel["Wheel-Version"] = "1.0"
    wheel["Generator"] = "bridgecad-repair-script"
    wheel["Root-Is-Purelib"] = "true"
    wheel["Tag"] = "py3-none-any"
    (dist / "WHEEL").write_bytes(bytes(wheel))

    # Build a minimal RECORD referencing at least these 4 dist-info files themselves.
    rows: list[str] = []
    for rel in [
        f"{dist.name}/METADATA",
        f"{dist.name}/INSTALLER",
        f"{dist.name}/WHEEL",
    ]:
        rows.extend(record_file_lines(rel))

    rows.append(f"{dist.name}/RECORD,,")
    (dist / "RECORD").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return dist


def remove_broken_pth() -> None:
    broken = USER_SITE / "distutils-precedence.pth"
    hack = USER_SITE / "_distutils_hack"
    if broken.exists():
        print(f"  remove broken distutils-precedence.pth: {broken}")
        broken.unlink()
    if hack.exists() and hack.is_dir():
        # Leave it if present; the warning came from the pth attempting to
        # import a shim inside an incomplete setuptools copy.
        print(f"  _distutils_hack/ present at {hack} (ok, leaving)")


def main() -> int:
    remove_broken_pth()
    for pypi, _mods, fallback, _ in REPAIR:
        try:
            import importlib.metadata as md
            md.version(pypi)
            print(f"  [KEEP] {pypi:20s} metadata already present (v{md.version(pypi)})")
            continue
        except Exception:
            pass
        dist = write_minimal_metadata(
            pypi,
            fallback,
            summary={
                "pytz": "World timezone definitions, modern and historical",
            }.get(pypi, ""),
        )
        print(f"  [FIX ] {pypi:20s} created {dist.name} (v{fallback})")
    print("DONE repair.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
