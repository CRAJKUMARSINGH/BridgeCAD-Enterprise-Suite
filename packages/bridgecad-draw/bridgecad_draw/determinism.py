"""Deterministic DXF serialisation.

An ezdxf ASCII DXF is *not* byte-stable across two renders of the same input:
the writer stamps volatile values that carry no geometry —

  * ``$TDCREATE`` / ``$TDUPDATE`` / ``$TDUCREATE`` / ``$TDUUPDATE`` — Julian
    date doubles written when the document is created and saved;
  * ``$FINGERPRINTGUID`` / ``$VERSIONGUID`` — regenerated at write time, so
    pinning the header does not help;
  * the ``999`` comment ezdxf writes with its own version and an ISO timestamp.

Two renders of the same project must produce identical bytes (W07 deliverable,
DoD: "Two renders of the same input produce identical bytes"). This module
serialises to text and replaces the volatile values with fixed sentinels, so
the comparison is of geometry alone.

Usage
-----
    from bridgecad_draw.determinism import canonical_dxf_bytes, write_deterministic

    a = canonical_dxf_bytes(doc_a)
    b = canonical_dxf_bytes(doc_b)
    assert a == b
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

#: A DXF group-40 (double) date, e.g. ``2451544.500000``.
_JULIAN = "2451544.5"

_GUID = re.compile(r"\{[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\}")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?")

#: Header variables whose value is a creation/save stamp, normalised to
#: ``_JULIAN`` regardless of when the document was written.
VOLATILE_HEADER_VARS = ("$TDCREATE", "$TDUPDATE", "$TDUCREATE", "$TDUUPDATE")

_ZERO_GUID = "{00000000-0000-0000-0000-000000000000}"
_EPOCH = "2000-01-01T00:00:00.000000+00:00"


def dxf_text(doc: Any) -> str:
    """Serialise *doc* to an ASCII DXF string without touching the filesystem."""
    stream = io.StringIO()
    doc.write(stream, fmt="asc")
    return stream.getvalue()


def normalize(text: str) -> str:
    """Replace volatile DXF values with fixed sentinels.

    The replacement is exact for GUIDs and timestamps and structural for the
    ``$TD*`` header variables (the group-40 value on the following line).
    """
    text = _GUID.sub(_ZERO_GUID, text)
    text = _TIMESTAMP.sub(_EPOCH, text)
    for var in VOLATILE_HEADER_VARS:
        text = re.sub(
            rf"{re.escape(var)}\r?\n[ \t]*40\r?\n[^\r\n]*",
            f"{var}\n 40\n{_JULIAN}",
            text,
        )
    return text


def canonical_dxf_bytes(doc: Any) -> bytes:
    """Canonical bytes for *doc* — equal iff the geometry is equal."""
    return normalize(dxf_text(doc)).encode("utf-8")


def write_deterministic(doc: Any, output_path: str | Path) -> Path:
    """Write the canonical DXF for *doc* and return the resolved path."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(canonical_dxf_bytes(doc))
    return p


__all__ = [
    "VOLATILE_HEADER_VARS",
    "canonical_dxf_bytes",
    "dxf_text",
    "normalize",
    "write_deterministic",
]
