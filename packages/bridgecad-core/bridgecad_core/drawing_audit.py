"""Optional drawing evidence consumed by core validation."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from importlib.metadata import entry_points
from typing import Protocol, Self

from .models import BridgeProject


class AuditTextBox(Protocol):
    @property
    def sheet(self) -> str: ...

    @property
    def text(self) -> str: ...

    def overlaps(self, other: Self, tol: float = 0.5) -> bool: ...


class DrawingAudit(Protocol):
    @property
    def rendered(self) -> bool: ...

    @property
    def text_boxes(self) -> Sequence[AuditTextBox]: ...

    @property
    def outside_frame(self) -> list[str]: ...

    @property
    def band_counts(self) -> dict[str, int]: ...

    @property
    def nts_claims(self) -> list[tuple[str, bool]]: ...

    def invalid_scales(self) -> list[tuple[str, int]]: ...

    def unregistered_layers(self) -> list[str]: ...


_auditor: Callable[[BridgeProject], DrawingAudit] | None = None


def register_layout_auditor(auditor: Callable[[BridgeProject], DrawingAudit]) -> None:
    """Provide drawing evidence when the drawing module loads from source."""
    global _auditor
    _auditor = auditor


def layout_audit_requested() -> bool:
    return os.environ.get("BRIDGECAD_LAYOUT_AUDIT", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def collect_layout_audit(project: BridgeProject) -> DrawingAudit | None:
    """Read drawing evidence from the registered or installed auditor, if enabled."""
    try:
        if _auditor is None and layout_audit_requested():
            provider = next(iter(entry_points(group="bridgecad.layout_audit", name="dxf")), None)
            if provider is not None:
                register_layout_auditor(provider.load())
        return _auditor(project) if _auditor is not None else None
    except Exception:
        # An unavailable audit leaves the corresponding checks unevaluated.
        return None
