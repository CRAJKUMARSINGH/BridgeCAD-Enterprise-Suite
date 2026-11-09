"""
bridgecad_infra.repositories — ProjectRepo, BridgeRepo, HistoryRepo.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

from .db import (
    BridgeRecord,
    GenerationHistory,
    ProjectIndexRecord,
    ProjectRecord,
    create_all_tables,
    get_session,
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
            return (
                s.query(ProjectRecord).order_by(ProjectRecord.created_at.desc()).limit(limit).all()
            )

    def upsert_from_bridge_project(self, project: Any) -> ProjectRecord:
        """Create or update from a BridgeProject Pydantic model."""
        pm = project.project_master
        code = str(getattr(pm, "project_code", "") or "UNKNOWN")
        existing = self.get_by_code(code)
        kwargs = {
            "project_title": str(getattr(pm, "project_title", "") or ""),
            "bridge_name": str(getattr(pm, "bridge_name", "") or ""),
            "chainage_km": float(getattr(pm, "chainage_km", 0) or 0),
            "state_code": getattr(getattr(pm, "state_code", None), "name", "") or "",
            "client": getattr(getattr(pm, "client", None), "name", "") or "",
            "phase": getattr(getattr(pm, "project_phase", None), "name", "") or "",
        }
        if existing:
            _ensure_tables()
            with get_session() as s:
                s.query(ProjectRecord).filter_by(project_code=code).update(kwargs)
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

    def create_from_bridge_project(
        self, project_id: int, project: Any, qa_score: int = 0
    ) -> BridgeRecord:
        gi = project.geometry_input
        bs = project.bridge_selection
        return self.create(
            project_id=project_id,
            bridge_type=getattr(getattr(bs, "bridge_type", None), "name", "") or "",
            span_count=int(gi.span_count),
            total_length_m=float(gi.total_length_m),
            overall_width_m=float(gi.overall_width_m),
            foundation_type=getattr(getattr(bs, "foundation_type", None), "name", "") or "",
            qa_score=qa_score,
        )


class HistoryRepo:
    """CRUD for GenerationHistory."""

    def record(
        self,
        project_id: int,
        action: str,
        status: str,
        bridge_id: int | None = None,
        output_path: str = "",
        qa_score: int = 0,
        duration_ms: int = 0,
        error_message: str = "",
    ) -> GenerationHistory:
        _ensure_tables()
        with get_session() as s:
            rec = GenerationHistory(
                project_id=project_id,
                bridge_id=bridge_id,
                action=action,
                status=status,
                output_path=output_path,
                qa_score=qa_score,
                duration_ms=duration_ms,
                error_message=error_message,
            )
            s.add(rec)
            s.flush()
            s.refresh(rec)
            return rec

    def list_for_project(self, project_id: int, limit: int = 50) -> list[GenerationHistory]:
        _ensure_tables()
        with get_session() as s:
            return (
                s.query(GenerationHistory)
                .filter_by(project_id=project_id)
                .order_by(GenerationHistory.created_at.desc())
                .limit(limit)
                .all()
            )


def _computed_names() -> set[str]:
    """Every computed_field name on BridgeProject and its section models."""
    names: set[str] = set()
    try:
        from bridgecad_core.models import BridgeProject

        def walk(model: Any) -> None:
            for cf in getattr(model, "model_computed_fields", {}):
                names.add(cf)
            for f in getattr(model, "model_fields", {}).values():
                ann = getattr(f, "annotation", None)
                inner = getattr(ann, "__args__", None)
                for cand in ([ann] if ann else []) + list(inner or []):
                    if hasattr(cand, "model_fields"):
                        walk(cand)

        walk(BridgeProject)
    except Exception:
        pass
    return names


_COMPUTED_NAMES: set[str] | None = None


def _strip_computed_fields(project: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Recursively drop computed_field keys so payloads re-validate cleanly."""
    global _COMPUTED_NAMES
    if _COMPUTED_NAMES is None:
        _COMPUTED_NAMES = _computed_names()
    names = _COMPUTED_NAMES

    def clean(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: clean(v) for k, v in node.items() if k not in names}
        if isinstance(node, list):
            return [clean(v) for v in node]
        return node

    return clean(payload)


class ProjectIndexRepo:
    """CRUD for the project_index table (guide #8).

    Rows are written by the save path, never by hand.  ``payload_json`` holds
    the serialized BridgeProject so duplicate/export can rebuild it without a
    second store.
    """

    @staticmethod
    def _slugify(text: str) -> str:
        import re

        slug = re.sub(r"[^a-z0-9]+", "-", (text or "project").lower()).strip("-")
        return slug[:60] or "project"

    @staticmethod
    def _unique_slug(s: Any, base: str) -> str:
        slug = base
        n = 2
        while s.query(ProjectIndexRecord).filter_by(slug=slug).first() is not None:
            slug = f"{base}-{n}"
            n += 1
        return slug

    @staticmethod
    def _row_dict(rec: ProjectIndexRecord) -> dict[str, Any]:
        return {
            "id": rec.id,
            "slug": rec.slug,
            "bridge_name": rec.bridge_name,
            "bridge_type": rec.bridge_type,
            "span_summary": rec.span_summary,
            "total_length_m": rec.total_length_m,
            "overall_width_m": rec.overall_width_m,
            "revision_tag": rec.revision_tag,
            "origin_project_id": rec.origin_project_id,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        }

    def upsert_from_bridge_project(self, project: Any) -> dict[str, Any]:
        """Write exactly one index row for *project*; ``updated_at`` advances."""

        pm = project.project_master
        gi = project.geometry_input
        bs = project.bridge_selection
        code = str(getattr(pm, "project_code", "") or "UNKNOWN")
        spans = [float(s) for s in (gi.span_lengths_m or [])]
        span_summary = (
            f"{len(spans)} x {spans[0]:.1f} m"
            if spans and len(set(spans)) == 1
            else f"{gi.span_count} spans"
        )
        payload = project.model_dump(mode="json")
        payload = _strip_computed_fields(project, payload)

        _ensure_tables()
        with get_session() as s:
            existing = (
                s.query(ProjectIndexRecord)
                .filter(
                    (
                        ProjectIndexRecord.payload_json["project_master"][
                            "project_code"
                        ].as_string()
                        == code
                    )
                    | (ProjectIndexRecord.slug == self._slugify(code))
                )
                .first()
            )
            fields = {
                "bridge_name": str(getattr(pm, "bridge_name", "") or ""),
                "bridge_type": getattr(getattr(bs, "bridge_type", None), "name", "") or "",
                "span_summary": span_summary,
                "total_length_m": float(gi.total_length_m or 0),
                "overall_width_m": float(gi.overall_width_m or 0),
                "revision_tag": getattr(getattr(pm, "revision", None), "name", "") or "",
                "payload_json": payload,
            }
            if existing is not None:
                for k, v in fields.items():
                    setattr(existing, k, v)
                s.flush()
                s.refresh(existing)
                return self._row_dict(existing)
            rec = ProjectIndexRecord(
                slug=self._unique_slug(s, self._slugify(code)),
                **fields,
            )
            s.add(rec)
            s.flush()
            s.refresh(rec)
            return self._row_dict(rec)

    def list_projects(self, limit: int = 25, offset: int = 0) -> list[dict[str, Any]]:
        """Index fields only — never the full project body. Soft-deleted excluded."""
        from sqlalchemy import desc

        _ensure_tables()
        with get_session() as s:
            rows = (
                s.query(ProjectIndexRecord)
                .filter(ProjectIndexRecord.deleted_at.is_(None))
                .order_by(desc(ProjectIndexRecord.updated_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._row_dict(r) for r in rows]

    def get_payload(self, idx: int) -> dict[str, Any] | None:
        _ensure_tables()
        with get_session() as s:
            rec = s.get(ProjectIndexRecord, idx)
            if rec is None or rec.deleted_at is not None or not rec.payload_json:
                return None
            return rec.payload_json

    def soft_delete(self, idx: int) -> bool:
        from datetime import datetime

        _ensure_tables()
        with get_session() as s:
            rec = s.get(ProjectIndexRecord, idx)
            if rec is None or rec.deleted_at is not None:
                return False
            rec.deleted_at = datetime.now(UTC)
            return True

    def restore(self, idx: int) -> bool:
        _ensure_tables()
        with get_session() as s:
            rec = s.get(ProjectIndexRecord, idx)
            if rec is None or rec.deleted_at is None:
                return False
            rec.deleted_at = None
            return True

    def duplicate(self, idx: int) -> dict[str, Any] | None:
        """Deep-copy the stored project, reset identity, index the copy."""
        payload = self.get_payload(idx)
        if payload is None:
            return None
        from bridgecad_core.models import BridgeProject
        from bridgecad_core.types import RevisionTag

        project = BridgeProject.model_validate(payload)
        pm = project.project_master

        # Unique project_code that still matches CLIENT-YYYY-###
        base = str(pm.project_code)
        m = __import__("re").match(r"^(.*-)(\d+)$", base)
        prefix, num = (m.group(1), int(m.group(2))) if m else (base + "-", 1)
        new_code = f"{prefix}{num + 1:0{len(m.group(2)) if m else 3}d}"
        _ensure_tables()
        with get_session() as s:
            while (
                s.query(ProjectIndexRecord)
                .filter(
                    ProjectIndexRecord.payload_json["project_master"]["project_code"].as_string()
                    == new_code
                )
                .first()
                is not None
            ):
                num += 1
                new_code = f"{prefix}{num:0{len(m.group(2)) if m else 3}d}"

        data = project.model_dump(mode="python")
        data = _strip_computed_fields(project, data)
        pm_data = data["project_master"]
        pm_data["project_code"] = new_code
        name = str(pm_data.get("bridge_name") or "")
        pm_data["bridge_name"] = (name[:117] + " (copy)") if len(name) <= 117 else name[:120]
        pm_data["drawing_no"] = None
        pm_data["revision"] = RevisionTag.R0
        pm_data["date_issued"] = None
        # designed_by / checked_by / approved_by retained per spec
        # Revision register / fingerprints are NOT copied (new project).

        new_project = BridgeProject.model_validate(data)
        row = self.upsert_from_bridge_project(new_project)
        # mark origin and return the refreshed row
        _ensure_tables()
        with get_session() as s:
            rec = s.get(ProjectIndexRecord, row["id"])
            if rec is not None:
                rec.origin_project_id = idx
                s.flush()
                s.refresh(rec)
                return self._row_dict(rec)
        return row


__all__ = ["ProjectRepo", "BridgeRepo", "HistoryRepo", "ProjectIndexRepo"]
