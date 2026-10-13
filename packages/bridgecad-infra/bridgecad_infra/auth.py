"""
bridgecad_infra.auth — API-key authentication + simple role check.

Keys are stored in environment variable BRIDGECAD_API_KEYS as
comma-separated "key:role" pairs, e.g.:
  BRIDGECAD_API_KEYS="abc123:admin,def456:viewer"

Roles: admin > engineer > viewer
"""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ApiKey:
    key:  str
    role: str   # "admin" | "engineer" | "viewer"

    @property
    def is_admin(self)    -> bool: return self.role == "admin"
    @property
    def is_engineer(self) -> bool: return self.role in ("admin", "engineer")


_ROLE_ORDER = {"admin": 3, "engineer": 2, "viewer": 1}


def _load_keys() -> dict[str, ApiKey]:
    """Load API keys from BRIDGECAD_API_KEYS env var."""
    raw = os.environ.get("BRIDGECAD_API_KEYS", "")
    keys: dict[str, ApiKey] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            k, r = pair.split(":", 1)
            k, r = k.strip(), r.strip().lower()
            if k and r in ("admin", "engineer", "viewer"):
                # Store hash for constant-time comparison
                keys[k] = ApiKey(key=k, role=r)
    # Always add a dev key when no keys configured
    if not keys:
        dev_key = os.environ.get("BRIDGECAD_DEV_KEY", "dev-insecure-key")
        keys[dev_key] = ApiKey(key=dev_key, role="admin")
    return keys


_KEYS: dict[str, ApiKey] = _load_keys()


def verify_api_key(key: str) -> Optional[ApiKey]:
    """Return ApiKey if valid, None otherwise. Uses constant-time comparison."""
    for stored_key, api_key in _KEYS.items():
        if secrets.compare_digest(key, stored_key):
            return api_key
    return None


def require_role(key: str, min_role: str = "viewer") -> ApiKey:
    """Raise PermissionError if key is invalid or insufficient role."""
    api_key = verify_api_key(key)
    if api_key is None:
        raise PermissionError("Invalid API key")
    if _ROLE_ORDER.get(api_key.role, 0) < _ROLE_ORDER.get(min_role, 0):
        raise PermissionError(
            f"Role '{api_key.role}' insufficient; need '{min_role}'"
        )
    return api_key


def generate_api_key() -> str:
    """Generate a cryptographically secure random API key."""
    return secrets.token_urlsafe(32)


__all__ = ["ApiKey", "verify_api_key", "require_role", "generate_api_key"]
