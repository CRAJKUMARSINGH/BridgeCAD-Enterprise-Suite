"""
bridgecad_infra.repositories — ProjectRepo, BridgeRepo, HistoryRepo.
"""
from __future__ import annotations

from typing import Any

from .db import (
    get_session, ProjectRecord, BridgeRecord, GenerationHistory,
    create_all_tables,
)


def _ensure_tables():
    create_all_tables()


class ProjectRepo:
    """CRUD for ProjectRecord."""

    def create(self, project_code: str, **kwargs) -> ProjectRecord:
        _ensure_tables()
        with get_session() as s:
            rec = ProjectRecord(project_code=project_code, **kwargs)
            s.add(rec)
            s.flush()
            s.refresh(rec)
            return rec

    def get_by_code(self, code: str) -> ProjectRecord | None:
        _ensure_tables()
        with get_session() as s:
            return s.query(ProjectRecord).filter_by(project_code=code).first()

    def list_all(self, limit: int = 100) -> list[ProjectRecord]:
        _ensure_tables()
        with get_session() as s:
            return s.query(ProjectRecord).order_by(
                ProjectRecord.created_at.desc()).limit(limit).all()

    def upsert_from_bridge_project(self, project: Any) -> ProjectRecord:
        """Create or update from a BridgeProject Pydantic model."""
        pm = project.project_master
        code  = str(getattr(pm, "project_code", "") or "UNKNOWN")
        existing = self.get_by_code(code)
        kwargs = {
            "project_title": str(getattr(pm, "project_title", "") or ""),
            "bridge_name":   str(getattr(pm, "bridge_name",   "") or ""),
            "chainage_km":   float(getattr(pm, "chainage_km",   0) or 0),
            "state_code":    getattr(getattr(pm, "state_code",  None), "name", "") or "",
            "client":        getattr(getattr(pm, "client",      None), "name", "") or "",
            "phase":         getattr(getattr(pm, "project_phase",None),"name", "") or "",
        }
        if existing:
            _ensure_tables()
            with get_session() as s:
                s.query(ProjectRecord).filter_by(
                    project_code=code).update(kwargs)
            return existing
        return self.create(code, **kwargs)


class BridgeRepo:
    """CRUD for BridgeRecord."""

    def create(self, project_id: int, **kwargs) -> BridgeRecord:
        _ensure_tables()
        with get_session() as s:
            rec = BridgeRecord(project_id=project_id, **kwargs)
            s.add(rec)
            s.flush()
            s.refresh(rec)
            return rec

    def create_from_bridge_project(self, project_id: int,
                                    project: Any,
                                    qa_score: int = 0) -> BridgeRecord:
        gi = project.geometry_input
        bs = project.bridge_selection
        return self.create(
            project_id      = project_id,
            bridge_type     = getattr(getattr(bs, "bridge_type", None), "name", "") or "",
            span_count      = int(gi.span_count),
            total_length_m  = float(gi.total_length_m),
            overall_width_m = float(gi.overall_width_m),
            foundation_type = getattr(getattr(bs, "foundation_type", None), "name", "") or "",
            qa_score        = qa_score,
        )


class HistoryRepo:
    """CRUD for GenerationHistory."""

    def record(self, project_id: int, action: str, status: str,
               bridge_id: int | None = None,
               output_path: str = "",
               qa_score: int = 0,
               duration_ms: int = 0,
               error_message: str = "") -> GenerationHistory:
        _ensure_tables()
        with get_session() as s:
            rec = GenerationHistory(
                project_id=project_id, bridge_id=bridge_id,
                action=action, status=status, output_path=output_path,
                qa_score=qa_score, duration_ms=duration_ms,
                error_message=error_message,
            )
            s.add(rec)
            s.flush()
            s.refresh(rec)
            return rec

    def list_for_project(self, project_id: int,
                          limit: int = 50) -> list[GenerationHistory]:
        _ensure_tables()
        with get_session() as s:
            return (
                s.query(GenerationHistory)
                .filter_by(project_id=project_id)
                .order_by(GenerationHistory.created_at.desc())
                .limit(limit)
                .all()
            )


__all__ = ["ProjectRepo", "BridgeRepo", "HistoryRepo"]
