"""
bridgecad_infra.logging_setup — Structured logging with structlog fallback.

If structlog is available: uses JSON structured output.
Otherwise: falls back to standard logging with a clean formatter.

Usage:
    from bridgecad_infra.logging_setup import get_logger
    log = get_logger("bridgecad.draw")
    log.info("sheet_generated", sheet=1, size_kb=48)
"""
from __future__ import annotations

import logging
import sys
from typing import Any


try:
    import structlog
    _STRUCTLOG = True
except ImportError:
    _STRUCTLOG = False


def configure(
    level: str     = "INFO",
    json_output: bool = False,
) -> None:
    """Configure application-wide logging. Call once at startup."""
    lvl = getattr(logging, level.upper(), logging.INFO)

    if _STRUCTLOG and json_output:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
        )
    else:
        # Standard logging fallback
        fmt = "%(asctime)s %(levelname)-8s %(name)s  %(message)s"
        logging.basicConfig(
            level=lvl,
            format=fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )


def get_logger(name: str) -> Any:
    """Return a logger (structlog bound logger or stdlib Logger)."""
    if _STRUCTLOG:
        return structlog.get_logger(name)
    return logging.getLogger(name)


__all__ = ["configure", "get_logger"]
