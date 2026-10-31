#!/usr/bin/env python3
"""Validate a PDF against PDF/A-1b.

Two levels of evidence, in order:

  1. **Structural markers**, checked in-process — catalogue ``Metadata``, an
     ``OutputIntent`` of subtype ``GTS_PDFA1`` with a three-component ICC
     destination profile, and ``pdfaid:part=1`` / ``pdfaid:conformance=B`` in
     the XMP packet. A file missing any of these is rejected outright.
  2. **veraPDF**, the authority on conformance, run when it is on ``PATH``. An
     absent veraPDF is reported as ``skip``, never as a pass — the marker check
     above still gates the file, but nobody should read the run as independent
     conformance evidence.

    python scripts/check_pdfa.py out/plan.dxf.pdf
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
_DRAW = ROOT / "packages" / "bridgecad-draw"
if _DRAW.exists() and str(_DRAW) not in sys.path:
    sys.path.insert(0, str(_DRAW))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path, help="the PDF to validate")
    args = ap.parse_args(argv)

    if not args.pdf.is_file():
        print(f"  [FAIL] no such file: {args.pdf}")
        return 1

    from bridgecad_draw.engines.pdf_engine import inspect_pdf_a, is_pdf_a1b

    facts = inspect_pdf_a(args.pdf)
    if not is_pdf_a1b(facts):
        print(f"  [FAIL] PDF/A-1b structural markers missing: {facts}")
        return 1
    print("  [PASS] PDF/A-1b structural markers present")

    verapdf = shutil.which("verapdf")
    if verapdf is None:
        print("  [SKIP] veraPDF not installed — conformance not independently verified")
        return 0

    proc = subprocess.run(
        [verapdf, "--format", "text", "-f", "1b", str(args.pdf)],
        capture_output=True,
        text=True,
    )
    detail = (proc.stdout or proc.stderr).strip()[-400:]
    if proc.returncode == 0:
        print(f"  [PASS] veraPDF 1b: {detail}")
        return 0
    print(f"  [FAIL] veraPDF 1b: {detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
