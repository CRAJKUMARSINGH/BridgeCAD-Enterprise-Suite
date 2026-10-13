"""
bridgecad_qa.rules_engine — Thin adapter between bridgecad_core.validation
and the QA package. Runs all 30 checks and returns a ValidationReport.
"""
from __future__ import annotations
from typing import Any


def run_qa(project: Any):
    """Run all registered checks against *project* and return ValidationReport."""
    from bridgecad_core.validation import run_all
    return run_all(project)


__all__ = ["run_qa"]
