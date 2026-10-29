"""
Golden-case model pinning — canonical-JSON drift gate (GUIDE.md §12).

The golden cases in ``tests/draw/golden/<slug>.json`` pin *selected* expected
values by hand. This script adds the missing half: a byte-stable pin of the
**whole** BridgeProject model built from each case's fixture, so any drift in
any field — not only the hand-picked ones — fails the build with a field-level
diff.

Workflow:
  1. REGENERATE (``--regenerate``): build each case's model, serialise it to
     canonical JSON, write it under ``tests/draw/golden/pins/``.
  2. VERIFY (default, CI): rebuild and diff against the pin. Drift = red.

Drift policy: a pin is byte-stable canonical JSON. If a change SHOULD alter the
model, regenerate deliberately and commit the pin in the same PR with the reason
in the PR description. Silent drift is a bug.

Usage:
  python scripts/pin_golden.py                 # verify every golden case
  python scripts/pin_golden.py --regenerate    # rewrite pins after a change
  python scripts/pin_golden.py simple_12m      # verify one case by slug
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "draw" / "golden"
PIN_DIR = GOLDEN / "pins"
E2E_LOADER = REPO / "tests" / "e2e" / "run_e2e.py"


def golden_slugs() -> list[str]:
    """Every golden case slug; the ``pins/`` subdirectory is not a case."""
    return sorted(p.stem for p in GOLDEN.glob("*.json"))


def _fixture_path(golden: dict) -> Path:
    rel = golden.get("fixture")
    if not rel:
        raise KeyError("golden case has no 'fixture' path")
    return REPO / rel


def _build_model(path: Path):
    """Fixture → BridgeProject, using the repo's canonical loaders.

    ``.json`` fixtures go through the tests/e2e loader (the same one
    ``tests/draw/contract.py`` uses); ``.xlsx`` workbooks go through the
    production ``bridgecad_io.read_excel`` entry point.
    """
    if path.suffix.lower() == ".xlsx":
        from bridgecad_io import read_excel

        return read_excel(path)

    spec = importlib.util.spec_from_file_location("bridgecad_e2e_loader", E2E_LOADER)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load e2e fixture loader: {E2E_LOADER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = json.loads(path.read_text(encoding="utf-8"))
    return module._build_from_fixture(data)


def canonical_json(project) -> str:
    """Serialize a BridgeProject to canonical (stable-key) JSON."""
    from bridgecad_core.models import BridgeProject

    if not isinstance(project, BridgeProject):
        raise TypeError(f"expected BridgeProject, got {type(project).__name__}")
    payload = project.model_dump(mode="json", round_trip=True)
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def pin_path(slug: str) -> Path:
    return PIN_DIR / f"{slug}.model.json"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def regenerate(slug: str) -> str:
    golden = json.loads((GOLDEN / f"{slug}.json").read_text(encoding="utf-8"))
    if golden.get("overrides"):
        print(f"  note: {slug} has facade overrides; pinning the base fixture model")
    text = canonical_json(_build_model(_fixture_path(golden)))
    PIN_DIR.mkdir(parents=True, exist_ok=True)
    pin_path(slug).write_text(text, encoding="utf-8")
    return digest(text)


def verify(slug: str) -> list[str]:
    golden = json.loads((GOLDEN / f"{slug}.json").read_text(encoding="utf-8"))
    text = canonical_json(_build_model(_fixture_path(golden)))
    pin = pin_path(slug)
    if not pin.exists():
        return [f"{slug}: NO PIN — run `python scripts/pin_golden.py --regenerate`"]
    pinned = pin.read_text(encoding="utf-8")
    if pinned.strip() == text.strip():
        return []
    diff = "\n".join(
        difflib.unified_diff(
            pinned.splitlines(),
            text.splitlines(),
            fromfile=f"pinned/{slug}",
            tofile=f"current/{slug}",
            lineterm="",
        )
    )
    return [f"{slug}: MODEL DRIFT (sha256 {digest(pinned)} → {digest(text)})\n{diff[:4000]}"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Pin/verify golden BridgeProject models.")
    ap.add_argument(
        "--regenerate", action="store_true", help="rewrite pins (deliberate change only)"
    )
    ap.add_argument("slugs", nargs="*", default=None, help="golden slugs (default: all)")
    args = ap.parse_args()

    slugs = args.slugs or golden_slugs()
    if not slugs:
        print("no golden cases found", file=sys.stderr)
        return 1

    failures: list[str] = []
    for slug in slugs:
        try:
            if args.regenerate:
                print(f"PINNED {slug} sha256:{regenerate(slug)}")
            else:
                failures.extend(verify(slug))
        except Exception as exc:  # parse errors must fail loudly, never skip
            failures.append(f"{slug}: ERROR {type(exc).__name__}: {exc}")

    for failure in failures:
        print(failure, file=sys.stderr)
    if not args.regenerate:
        print(f"golden model verify: {len(slugs) - len(failures)}/{len(slugs)} OK")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
