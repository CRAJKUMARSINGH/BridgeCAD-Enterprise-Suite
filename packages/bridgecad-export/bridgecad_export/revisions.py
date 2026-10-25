"""Revision and issue state — the gate between a drawing set and a construction set.

PURPOSE LADDER, and what each level requires:
    PRELIMINARY   anything. Honest about being unfinished.
    TENDER        every sheet promoted. Signoffs optional but listed.
    FOR_CONSTRUCTION  every sheet promoted AND signed AND not stale. Accepted
                      gaps are allowed but must be listed on the transmittal.
    AS_BUILT      FOR_CONSTRUCTION requirements plus a field-verified stamp.

A set may not claim a purpose its sheets do not satisfy. This is the rule that
stops "Construction ready" being a string someone typed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REGISTER = REPO / "tests" / "draw" / "revisions.json"
SPEC = REPO / "tests" / "draw" / "sheets.spec.json"

PURPOSES = ("PRELIMINARY", "TENDER", "FOR_CONSTRUCTION", "AS_BUILT")
LADDER = {p: i for i, p in enumerate(PURPOSES)}


@dataclass
class Blockers:
    purpose: str
    blockers: list[str]

    @property
    def ok(self) -> bool:
        return not self.blockers


def load() -> dict:
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def _signoff_module():
    """Load ``tests/draw/signoff.py`` by path.

    ``from tests.draw import signoff`` is unreliable here: several workspace
    packages ship their own ``tests`` package, which shadows the repo-root one
    whenever a package directory precedes the root on ``sys.path``. Loading by
    path is the same technique the test contract uses for its e2e fixtures.
    """
    import importlib.util
    import sys

    path = REPO / "tests" / "draw" / "signoff.py"
    spec = importlib.util.spec_from_file_location("bridgecad_signoff", path)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves the defining module from sys.modules, so register it
    # before executing the body.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _signed_by_sheet() -> dict:
    """Signoffs keyed by sheet. A record that will not validate is not a signoff."""
    signoff = _signoff_module()
    signed: dict = {}
    for path in sorted(signoff.SIGNOFF_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            so = signoff.Signoff(**json.loads(path.read_text(encoding="utf-8")))
        except (TypeError, ValueError):
            continue
        signed[so.sheet] = so
    return signed


def blockers_for(purpose: str, *, signoffs=None) -> Blockers:
    """What stops the set claiming `purpose`. Empty list means it may."""
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    out: list[str] = []

    if LADDER[purpose] >= LADDER["TENDER"]:
        for sheet, entry in sorted(spec["sheets"].items()):
            if entry["status"] != "promoted":
                out.append(f"{sheet}: scaffold — draw it before claiming {purpose}")

    if LADDER[purpose] >= LADDER["FOR_CONSTRUCTION"]:
        signed = _signed_by_sheet()
        for sheet, entry in sorted(spec["sheets"].items()):
            so = signed.get(sheet)
            if so is None:
                out.append(f"{sheet}: promoted but unreviewed")
            elif so.outcome != "confirmed" and not so.exceptions:
                out.append(f"{sheet}: reviewed with exceptions but none listed")
        for sheet, entry in sorted(spec["sheets"].items()):
            for key, reason in entry.get("accepted_gaps", {}).items():
                out.append(f"GAP {sheet}/{key}: {reason}")

    return Blockers(purpose, out)


def manifest_label(purpose: str) -> str:
    """The string the bundle carries. Derived, never typed."""
    blockers = blockers_for(purpose)
    if blockers.ok:
        return f"Issued for {purpose.replace('_', ' ').title()}"
    return f"{purpose.replace('_', ' ').title()} — {len(blockers.blockers)} open item(s)"
