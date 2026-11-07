"""bridgecad_core.profiles — jurisdiction code profiles.

A profile is a YAML file under ``profiles/`` that carries the rule constants a
jurisdiction expects (cap depth, weep spacing, pile rules, ...).  The QA engine
reads limits through :func:`resolve` so one project can be checked against
IRC:112 or AASHTO LRFD without code changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_PROFILE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class CodeProfile:
    """Typed view over one profile YAML."""

    name: str
    jurisdiction: str
    values: dict[str, float]

    def __getattr__(self, item: str) -> float:
        try:
            return float(self.values[item])
        except KeyError as exc:
            raise AttributeError(item) from exc

    def get(self, key: str, default: float = 0.0) -> float:
        return float(self.values.get(key, default))


@lru_cache(maxsize=8)
def load_profile(name: str) -> CodeProfile:
    """Load ``profiles/<name>.yaml`` (cached)."""
    path = _PROFILE_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"unknown code profile '{name}' (looked in {path})")
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    values = {k: v for k, v in raw.items() if k not in ("name", "jurisdiction")}
    return CodeProfile(
        name=str(raw.get("name", name)),
        jurisdiction=str(raw.get("jurisdiction", "")),
        values=values,
    )


def profile_for(project: Any) -> CodeProfile:
    """The profile *project* selects via ``project_master.code_profile``."""
    name = getattr(getattr(project, "project_master", None), "code_profile", None) or "irc_112"
    try:
        return load_profile(str(name))
    except FileNotFoundError:
        return load_profile("irc_112")


def resolve(key: str, project: Any, default: float = 0.0) -> float:
    """Read one profile constant for *project*."""
    return profile_for(project).get(key, default)


__all__ = ["CodeProfile", "load_profile", "profile_for", "resolve"]
