"""
bridgecad — single facade namespace over the BridgeCAD Enterprise Suite.

PURPOSE
-------
Instead of memorising import chains like:

    from bridgecad_core.models import BridgeProject
    from bridgecad_core.types  import DeckType
    from bridgecad_draw.booklet import generate_package
    from bridgecad_qa.compliance import score
    from bridgecad_io.json_adapter import dump_project
    from bridgecad_bill.processor import extract_and_price

the user writes:

    import bridgecad as bc

    project = bc.models.BridgeProject(...)
    project.types  # or bc.types.DeckType.SOLID_SLAB_RCC
    bc.draw.generate_package(project, out)
    bc.qa.score(project)
    bc.io.json_adapter.dump_project(project, path)
    bc.bill.extract_and_price(project)

The facade keeps sub-modules lazy-imported to avoid loading 18k LOC on
`import bridgecad` (useful for CLI startup latency).

IMPLEMENTATION NOTE
-------------------
Two `sys.path` bootstrap approaches are supported:

1. PIP WORKSPACE MODE:  pip install -e <repo-root>
   → setuptools `package-dir` mappings in pyproject.toml make `bridgecad_core`,
     `bridgecad_io`, … importable directly.  Facade sub-modules are lazy aliases.

2. SCRIPT MODE (default for root scripts):  `python _generate_11span_gad.py`
   → sitecustomize.py at repo-root auto-injects all the package directories
     into sys.path before user-imports fire. Facade works identically.

Both modes are 100 % API compatible; no source change required when moving
between "workstation script" → "installed docker image".
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

# ---------------------------------------------------------------------------
# Version & banner — always eager (cheap, useful for --version output).
# ---------------------------------------------------------------------------
__version__ = "0.1.0-rc1"
__suite__   = "BridgeCAD Enterprise Suite"
__moniker__ = "M1 · 11-span RCC Solid Slab · Major Bridge GAD"

# ---------------------------------------------------------------------------
# Lazy module aliases.  We use ModuleType.__getattr__ (PEP 562) so the first
# time the user writes `bc.types` we import `bridgecad_types` /
# `bridgecad_core.types` only at that moment.
# ---------------------------------------------------------------------------
#   facade-submodule name  ->  actual python import path
_SUBMODULE_MAP: dict[str, str] = {
    # core
    "types":             "bridgecad_core.types",
    "models":            "bridgecad_core.models",
    "validation":        "bridgecad_core.validation",
    "quantities":        "bridgecad_core.quantities",
    "costs":             "bridgecad_core.costs",
    "geometry":          "bridgecad_core.geometry",
    "standards":         "bridgecad_core.standards",
    # io
    "io":                "bridgecad_io",
    # draw
    "draw":              "bridgecad_draw",
    # bill
    "bill":              "bridgecad_bill",
    # qa
    "qa":                "bridgecad_qa",
    # export
    "export":            "bridgecad_export",
    # plugins
    "plugins":           "bridgecad_plugins",
    # ai
    "ai":                "bridgecad_ai",
    # infra
    "infra":             "bridgecad_infra",
    # apps (thin — only imported when user calls `bridgecad-cli`)
    "cli":               "bridgecad_cli",
    "api":               "bridgecad_api",
}

# Cache already-loaded facade sub-modules (one instance per submodule, reused)
_LOADED: dict[str, Any] = {}


def _import_facade(name: str) -> Any:
    """Lazy importer returning the real sub-module bound under facade name."""
    real_path = _SUBMODULE_MAP[name]
    try:
        module = importlib.import_module(real_path)
    except ModuleNotFoundError as exc:  # pragma: no cover - env fault
        raise ModuleNotFoundError(
            f"bridgecad.{name} requires package `{real_path}` on sys.path.  "
            "Run `pip install -e .` from the repo root, or make sure "
            "sitecustomize.py bootstrap has been executed."
        ) from exc
    # Several sub-packages (io, draw, bill, qa, plugins, geometry) have their
    # own sub-modules that are NOT auto-imported in their respective
    # __init__.py files.  Because users expect `bc.io.json_adapter` etc. to
    # resolve without an extra `from bridgecad.io import json_adapter`, we
    # eagerly load the known submodules here.
    sub_imports: dict[str, list[str]] = {
        "io":        ["json_adapter", "csv_adapter",
                      "excel_reader", "excel_writer", "excel_template"],
        "draw":      ["booklet", "layers", "primitives", "dxf_engine",
                      "titleblocks", "engines", "sheets"],
        "bill":      ["processor", "rates_db", "statements", "models",
                      "formatters"],
        "qa":        ["compliance", "rules_engine", "reports",
                      "recommendations"],
        "plugins":   ["registry", "runner", "installer", "manifest_schema"],
        "ai":        ["estimator", "optimizer", "comparator", "param_suggester"],
        "infra":     ["logging_setup", "db", "cache", "storage",
                      "repositories", "queue", "metrics", "auth"],
        "geometry":  ["plan", "long_section", "cross_section", "foundation"],
        "standards": ["irc_05", "irc_21", "irc_sp55", "morth_specs"],
        "export":    ["booklet", "bundler", "orchestrator", "versioner"],
        "cli":       ["main"],
        "api":       ["main"],
    }
    for sub in sub_imports.get(name, []):
        try:
            importlib.import_module(real_path + "." + sub)
        except Exception:  # pragma: no cover - env-specific, fail-safe
            pass

    # Register it as `bridgecad.{name}` so `from bridgecad import types` works
    # and `help(bridgecad.types)` shows the correct path.
    import sys as _sys
    facade_key = __name__ + "." + name
    _sys.modules.setdefault(facade_key, module)
    return module


def __getattr__(name: str) -> Any:
    # Fast-path cache
    if name in _LOADED:
        return _LOADED[name]
    # Known sub-module alias
    if name in _SUBMODULE_MAP:
        mod = _import_facade(name)
        _LOADED[name] = mod
        return mod
    # Legacy convenience: `from bridgecad import BridgeProject`
    # -> forward to `bridgecad_core.models.BridgeProject` (only concrete,
    # non-ambiguous names).  Use explicit bc.models.X otherwise.
    _LEAF_FORWARDERS = {
        # models / aggregates
        "BridgeProject", "ProjectMetadata", "SurveyInputs", "Location",
        "DesignStandards", "Loads", "Superstructure", "Span",
        "Substructure", "Pier", "Abutment", "BearingSchedule", "FoundationDetails",
        "HydraulicDesign", "HydrologyData", "HydraulicLevels", "ScourDesign",
        "Materials", "BarSchedule", "EnvironmentalConditions",
        "ValidationResult", "ValidationFinding",
        "Calculations", "ConcreteQuantities", "ReinforcementQuantities",
        "BOMItem", "BOQItem",
        # types — enums that actually exist in bridgecad_core.types
        "BridgeCategory", "BridgeSubcategory",
        "SuperstructureType", "GirderType", "DeckJointSpacing",
        "PierType", "PierCapType", "PierShaftShape",
        "AbutmentType", "AbutmentPedestalType",
        "FoundationType",
        "KerbType", "CrashBarrierType", "FootpathType",
        "ConcreteGrade", "SteelGrade", "ExposureClass",
        "WearingCoatType", "WearingCoatGrade",
        "SeismicZone", "SeismicImportanceFactor",
        "CarriagewayLaneConfig", "CarriagewaySkewConfig", "SkewDirection",
        "VerticalAlignmentType",
        "WaterwayCrossingType", "RiverCrossingClass",
        "RiverBedMaterialSizeType", "RiverBankType", "RiverTrainingWorkType",
        "ValidationSeverity",
        # validation / quantities
        "run_all", "VALIDATION_REGISTRY",
    }
    if name in _LEAF_FORWARDERS:
        # Resolve by scanning through a small list of owners (no cyclic dep risk)
        for owner in ("models", "types", "validation", "quantities", "costs"):
            parent_mod = __getattr__(owner)  # recursive, cached next time
            if hasattr(parent_mod, name):
                obj = getattr(parent_mod, name)
                globals()[name] = obj  # cache at module top-level
                return obj
    raise AttributeError(f"module `bridgecad` has no attribute `{name}`")


def __dir__() -> list[str]:
    base = sorted(set(globals()) | set(_SUBMODULE_MAP.keys()))
    return base


# ---------------------------------------------------------------------------
# Nice banner for the CLI (imported via __main__.app)
# ---------------------------------------------------------------------------
if TYPE_CHECKING:  # pragma: no cover - mypy only
    from . import types, models, validation, quantities, costs  # noqa: F401
    from . import geometry, standards, io, draw, bill, qa, export, plugins  # noqa: F401
    from . import ai, infra, cli, api  # noqa: F401

__all__ = [
    # facade modules
    *list(_SUBMODULE_MAP.keys()),
    # banner info
    "__version__", "__suite__", "__moniker__",
]
