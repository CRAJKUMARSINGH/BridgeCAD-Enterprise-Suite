"""bridgecad_qa.required_content — the required-content manifest and its checker.

The acceptance spec (``CODE-JUNCTION/BRIDGECAD_GAD_ACCEPTANCE_RESOLUTION.md`` §4)
defines completeness by *required content*, not by sheet count.  Nine DXF files
of non-trivial size, a matching named RL chain and a clean layout zone check do
not by themselves prove that the details, dimensions and schedules a drawing
family requires are actually present on the sheets.

This module carries that requirement set as a versioned, reviewable manifest
(``required_content.json``) and measures each requirement against the generated
DXF files.  A requirement is credited only when it is **both**

* declared ``IMPLEMENTED`` in the manifest — nobody has to trust a measurement
  alone, and the manifest is the reviewed statement of intent; and
* measured present in the package — nobody has to trust a declaration alone.

A ``PARTIAL`` or ``MISSING`` declaration is reported as a gap, so the
``REQUIRED_CONTENT`` gate can never pass on a declared-but-unbuilt feature.
Requirements whose ``when`` condition does not match the resolved parameters
(e.g. a pile schedule on an open-foundation card) are reported ``applicable:
false`` and excluded from the pass set rather than silently passing.

The measurement is deliberately simple and observable: layers present on the
sheet, text strings present on the sheet, and sheet presence.  It does not
"understand" the drawing, so it cannot prove a detail is *correct* — only that
its declared layer/label/schedule is on the sheet.  Reviewer verdicts and the
engineering review remain separate gates.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

MANIFEST_VERSION = "1.0.0"
_DEFAULT_MANIFEST = Path(__file__).with_name("required_content.json")

#: Declaration statuses a requirement may carry in the manifest.
DECLARED_STATUSES = ("IMPLEMENTED", "PARTIAL", "MISSING")


class RequirementKind(str, Enum):
    """The measurement a requirement asks for."""

    SHEET_PRESENT = "sheet_present"
    LAYER = "layer"
    TEXT = "text"
    TEXT_REGEX = "text_regex"
    GEOMETRY = "geometry"


#: Layer prefixes that carry annotation, dimensions or sheet furniture rather
#: than drawn physical linework. A ``GEOMETRY`` requirement counts the layers
#: that are *not* in this set, so a schedule-only sheet (labels in a table)
#: cannot satisfy a requirement that asks for drawn geometry.
_ANNOTATION_PREFIXES = ("TEXT-", "TITLEBLK-", "DIM-", "BORDER-", "SYM-")

#: Layers whose text is title-block boilerplate (drawing number, revision,
#: sheet numbering, the project name).  A drawing-content requirement must not
#: be satisfied by "PROJECT: Open Foundation ..." in the title block, so text
#: search defaults to *drawing* scope and title-block text is opt-in.
_TITLE_BLOCK_LAYERS = frozenset({"TITLEBLK-TEXT", "TITLEBLK-BOX", "TEXT-TITLE"})

#: Text-search scopes.  ``drawing`` (the default) reads only text drawn on the
#: sheet proper; ``title_block`` reads only title-block boilerplate.  Keeping
#: them apart stops a project name in the title block satisfying a content
#: requirement for a detail on the sheet.
DRAWING = "drawing"
TITLE_BLOCK = "title_block"
SCOPES = (DRAWING, TITLE_BLOCK)


@dataclass(frozen=True)
class Requirement:
    """One required-content item for one drawing area."""

    id: str
    area: str
    kind: RequirementKind
    sheet: str
    value: str | None = None
    min_count: int = 1
    status: str = "MISSING"
    evidence: str = ""
    reviewer: str = ""
    when: dict[str, Any] = field(default_factory=dict)
    scope: str = DRAWING

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "Requirement":
        status = str(raw.get("status", "MISSING")).upper()
        if status not in DECLARED_STATUSES:
            raise ValueError(
                f"{raw.get('id')}: status must be one of {DECLARED_STATUSES}, "
                f"got {status!r}"
            )
        scope = str(raw.get("scope", DRAWING)).lower()
        if scope not in SCOPES:
            raise ValueError(
                f"{raw.get('id')}: scope must be one of {SCOPES}, got {scope!r}"
            )
        return cls(
            id=raw["id"],
            area=raw["area"],
            kind=RequirementKind(raw["kind"]),
            sheet=raw["sheet"],
            value=raw.get("value"),
            min_count=int(raw.get("min_count", 1)),
            status=status,
            evidence=raw.get("evidence", ""),
            reviewer=raw.get("reviewer", ""),
            when=dict(raw.get("when", {})),
            scope=scope,
        )


@dataclass
class SheetContent:
    """Measured content of one generated sheet."""

    stem: str
    path: Path
    layers: dict[str, int]
    #: ``(layer, text)`` pairs, so a text requirement can be scoped to the
    #: drawing proper or to the title block rather than matching anything.
    texts: list[tuple[str, str]]

    @property
    def entity_count(self) -> int:
        return sum(self.layers.values())

    @property
    def drawing_texts(self) -> list[str]:
        """Text drawn on the sheet, excluding title-block boilerplate."""
        return [t for lyr, t in self.texts if lyr not in _TITLE_BLOCK_LAYERS]

    @property
    def title_block_texts(self) -> list[str]:
        """Title-block text only."""
        return [t for lyr, t in self.texts if lyr in _TITLE_BLOCK_LAYERS]


@dataclass
class RequirementResult:
    """The measured verdict for one requirement against one package."""

    id: str
    area: str
    declared_status: str
    applicable: bool
    measured: int
    required_count: int
    detail: str

    @property
    def present(self) -> bool:
        return self.measured >= self.required_count

    @property
    def ok(self) -> bool:
        """Credited only when declared IMPLEMENTED *and* measured present."""
        return (
            self.applicable
            and self.declared_status == "IMPLEMENTED"
            and self.present
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "area": self.area,
            "declared_status": self.declared_status,
            "applicable": self.applicable,
            "measured": self.measured,
            "required_count": self.required_count,
            "present": self.present,
            "ok": self.ok,
            "detail": self.detail,
        }


@dataclass
class ContentReport:
    """The required-content verdict for one generated package."""

    manifest_version: str
    requirements: list[RequirementResult] = field(default_factory=list)
    sheets_found: list[str] = field(default_factory=list)

    @property
    def applicable(self) -> list[RequirementResult]:
        return [r for r in self.requirements if r.applicable]

    @property
    def failures(self) -> list[RequirementResult]:
        return [r for r in self.applicable if not r.ok]

    @property
    def passed(self) -> bool:
        """True only when every applicable requirement is declared IMPLEMENTED
        and measured present.  An empty applicable set is NOT a pass: a package
        whose manifest matches nothing has proven nothing."""
        return bool(self.applicable) and not self.failures

    def to_json(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "sheets_found": list(self.sheets_found),
            "applicable": len(self.applicable),
            "not_applicable": len(self.requirements) - len(self.applicable),
            "failures": len(self.failures),
            "passed": self.passed,
            "requirements": [r.to_json() for r in self.requirements],
        }

    def summary(self) -> str:
        fails = self.failures
        if self.passed:
            return (f"required content: {len(self.applicable)} applicable "
                    f"requirement(s) present on {len(self.sheets_found)} sheet(s)")
        detail = "; ".join(f"{r.id} ({r.declared_status}, measured {r.measured})"
                           for r in fails[:4])
        more = "" if len(fails) <= 4 else f" (+{len(fails) - 4} more)"
        return (f"required content: {len(fails)}/{len(self.applicable)} "
                f"applicable requirement(s) unmet — {detail}{more}")


# ── manifest loading ─────────────────────────────────────────────────────────

def load_manifest(path: str | Path | None = None) -> tuple[dict[str, Any], list[Requirement]]:
    """Load the versioned manifest. Returns ``(raw, requirements)``."""
    p = Path(path) if path is not None else _DEFAULT_MANIFEST
    raw = json.loads(Path(p).read_text(encoding="utf-8"))
    reqs = [Requirement.from_json(r) for r in raw.get("requirements", [])]
    ids = [r.id for r in reqs]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate requirement id(s): {sorted(dupes)}")
    return raw, reqs


# ── measurement ──────────────────────────────────────────────────────────────

def read_sheet(path: Path, stem: str) -> SheetContent:
    """Read one DXF's modelspace layers and text strings."""
    import ezdxf

    layers: dict[str, int] = {}
    texts: list[tuple[str, str]] = []
    doc = ezdxf.readfile(str(path))
    for e in doc.modelspace():
        layer = e.dxf.layer
        layers[layer] = layers.get(layer, 0) + 1
        kind = e.dxftype()
        if kind == "TEXT":
            texts.append((layer, str(e.dxf.text)))
        elif kind == "MTEXT":
            texts.append((layer, str(e.plain_text())))
    return SheetContent(stem=stem, path=path, layers=layers, texts=texts)


def read_package(dxf_dir: str | Path, stems: Iterable[str]) -> dict[str, SheetContent]:
    """Read every sheet whose filename ends with a manifest sheet stem.

    ``generate_package`` writes ``<prefix>_<stem>.dxf``, so a package is matched
    by stem suffix rather than by a fixed prefix.
    """
    out: dict[str, SheetContent] = {}
    d = Path(dxf_dir)
    if not d.is_dir():
        return out
    for stem in stems:
        matches = [p for p in d.glob("*.dxf") if p.stem.endswith(stem)]
        if matches:
            out[stem] = read_sheet(sorted(matches)[0], stem)
    return out


def _applies(when: dict[str, Any], params: dict[str, Any]) -> bool:
    """Evaluate a requirement's applicability against the resolved parameters.

    ``when`` maps a parameter name to either a list of allowed values (string
    comparison) or a ``{"min": n}`` / ``{"max": n}`` numeric bound.  Multiple
    keys are ANDed.  An empty ``when`` always applies.
    """
    for key, allowed in when.items():
        actual = params.get(key)
        if isinstance(allowed, dict):
            try:
                value = float(actual)
            except (TypeError, ValueError):
                return False
            if "min" in allowed and value < float(allowed["min"]):
                return False
            if "max" in allowed and value > float(allowed["max"]):
                return False
        else:
            if isinstance(allowed, (list, tuple, set)):
                if str(actual) not in {str(a) for a in allowed}:
                    return False
            elif str(actual) != str(allowed):
                return False
    return True


def _measure(req: Requirement, sheets: dict[str, SheetContent]) -> tuple[int, str]:
    """Return ``(count, detail)`` for one requirement."""
    content = sheets.get(req.sheet)
    if content is None:
        return 0, f"{req.sheet}: sheet not found in package"
    if req.kind is RequirementKind.SHEET_PRESENT:
        return 1, f"{req.sheet}: present ({content.entity_count} entities)"
    if req.kind is RequirementKind.LAYER:
        n = content.layers.get(str(req.value), 0)
        return n, f"{req.sheet}: layer {req.value!r} × {n}"
    if req.kind in (RequirementKind.TEXT, RequirementKind.TEXT_REGEX):
        pool = (content.title_block_texts if req.scope == TITLE_BLOCK
                else content.drawing_texts)
        label = "title-block" if req.scope == TITLE_BLOCK else "drawing"
        if req.kind is RequirementKind.TEXT:
            n = sum(1 for t in pool if t == req.value)
        else:
            rx = re.compile(str(req.value), re.IGNORECASE)
            n = sum(1 for t in pool if rx.search(t))
        return n, f"{req.sheet}: {label} text /{req.value}/ × {n}"
    if req.kind is RequirementKind.GEOMETRY:
        drawn = [lyr for lyr in content.layers
                 if not lyr.startswith(_ANNOTATION_PREFIXES)]
        return len(drawn), f"{req.sheet}: drawn layers {sorted(drawn)}"
    return 0, f"{req.sheet}: unknown requirement kind {req.kind}"


def annotate_family(params: dict[str, Any]) -> dict[str, Any]:
    """Return *params* with ``abutment_shape_family`` filled in.

    The value comes from the same ``family_for()`` the renderers use, so a
    ``when`` condition on the abutment shape family tracks the shape that was
    actually drawn rather than a hand-kept list.  An explicitly supplied value
    is respected.
    """
    out = dict(params)
    if "abutment_shape_family" not in out:
        from bridgecad_core.geometry.abutment_profiles import family_for

        out["abutment_shape_family"] = family_for(out.get("abutment_type"))
    return out


def evaluate(
    dxf_dir: str | Path,
    params: dict[str, Any],
    *,
    manifest_path: str | Path | None = None,
    manifest: tuple[dict[str, Any], list[Requirement]] | None = None,
) -> ContentReport:
    """Measure every manifest requirement against one generated package."""
    raw, reqs = manifest if manifest is not None else load_manifest(manifest_path)
    params = annotate_family(params)
    sheets = read_package(dxf_dir, sorted({r.sheet for r in reqs}))
    report = ContentReport(
        manifest_version=str(raw.get("manifest_version", MANIFEST_VERSION)),
        sheets_found=sorted(sheets),
    )
    for req in reqs:
        if not _applies(req.when, params):
            report.requirements.append(RequirementResult(
                id=req.id, area=req.area, declared_status=req.status,
                applicable=False, measured=0, required_count=req.min_count,
                detail=f"not applicable for {sorted(req.when)}={ {k: params.get(k) for k in req.when} }",
            ))
            continue
        count, detail = _measure(req, sheets)
        report.requirements.append(RequirementResult(
            id=req.id, area=req.area, declared_status=req.status,
            applicable=True, measured=count, required_count=req.min_count,
            detail=detail,
        ))
    return report


__all__ = [
    "ContentReport",
    "DECLARED_STATUSES",
    "DRAWING",
    "MANIFEST_VERSION",
    "Requirement",
    "RequirementKind",
    "RequirementResult",
    "SCOPES",
    "SheetContent",
    "TITLE_BLOCK",
    "annotate_family",
    "evaluate",
    "load_manifest",
    "read_package",
    "read_sheet",
]
