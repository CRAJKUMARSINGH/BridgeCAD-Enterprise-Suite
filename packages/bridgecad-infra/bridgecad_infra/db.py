"""
bridgecad_infra.db — SQLAlchemy engine + session factory.

Dev: SQLite at ~/.bridgecad/bridgecad.db
Prod: Postgres via DATABASE_URL environment variable

Usage:
    from bridgecad_infra.db import get_session, engine
    with get_session() as session:
        session.add(...)
        session.commit()
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ---------------------------------------------------------------------------
# Database URL resolution
# ---------------------------------------------------------------------------

def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # Default: SQLite in user home
    db_dir = Path.home() / ".bridgecad"
    db_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_dir / 'bridgecad.db'}"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_ENGINE = None


def _get_engine():
    global _ENGINE
    if _ENGINE is None:
        url = _db_url()
        kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _ENGINE = create_engine(url, echo=False, **kwargs)
        # Enable WAL mode for SQLite (better concurrency)
        if url.startswith("sqlite"):
            @event.listens_for(_ENGINE, "connect")
            def _set_wal(dbapi_con, _):
                dbapi_con.execute("PRAGMA journal_mode=WAL")
    return _ENGINE


engine = _get_engine()  # module-level convenience


# ---------------------------------------------------------------------------
# ORM base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class ProjectRecord(Base):
    __tablename__ = "projects"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    project_code = Column(String(30), unique=True, nullable=False, index=True)
    project_title= Column(String(150))
    bridge_name  = Column(String(120))
    chainage_km  = Column(Float)
    state_code   = Column(String(10))
    client       = Column(String(50))
    phase        = Column(String(50))
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())

    bridges      = relationship("BridgeRecord", back_populates="project",
                                cascade="all, delete-orphan")
    histories    = relationship("GenerationHistory", back_populates="project",
                                cascade="all, delete-orphan")


class BridgeRecord(Base):
    __tablename__ = "bridges"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    project_id      = Column(Integer, ForeignKey("projects.id"), nullable=False)
    bridge_type     = Column(String(50))
    span_count      = Column(Integer)
    total_length_m  = Column(Float)
    overall_width_m = Column(Float)
    foundation_type = Column(String(50))
    qa_score        = Column(Integer)
    parameters_json = Column(JSON)
    created_at      = Column(DateTime, server_default=func.now())

    project  = relationship("ProjectRecord", back_populates="bridges")
    histories= relationship("GenerationHistory", back_populates="bridge",
                            cascade="all, delete-orphan")


class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    project_id    = Column(Integer, ForeignKey("projects.id"), nullable=False)
    bridge_id     = Column(Integer, ForeignKey("bridges.id"), nullable=True)
    action        = Column(String(50))   # "draw", "validate", "export", "bill"
    status        = Column(String(20))   # "success", "failed"
    output_path   = Column(Text)
    qa_score      = Column(Integer)
    duration_ms   = Column(Integer)
    error_message = Column(Text)
    created_at    = Column(DateTime, server_default=func.now())

    project = relationship("ProjectRecord", back_populates="histories")
    bridge  = relationship("BridgeRecord",  back_populates="histories")


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=_get_engine(),
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables() -> None:
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=_get_engine())


__all__ = [
    "Base", "ProjectRecord", "BridgeRecord", "GenerationHistory",
    "get_session", "create_all_tables", "engine",
]
