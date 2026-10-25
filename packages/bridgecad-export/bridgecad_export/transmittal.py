"""
bridgecad_export.transmittal — what was issued, and proof of it.

A transmittal without hashes cannot prove what was issued. Each sheet it names
carries the geometry digest the sheet was drawn from, bound the same way a
signoff is, so a recipient can tell whether the geometry moved after the issue.
"""
from __future__ import annotations

from .revisions import load


def build_transmittal(project, revision: str | None = None) -> dict:
    """Build the transmittal record for one revision of *project*.

    Parameters
    ----------
    project : object
        The drafting project the sheets are drawn from.
    revision : str, optional
        Revision code to issue. Defaults to the register's ``current``.

    Returns
    -------
    dict
        Keys: ``revision`` (the code), ``purpose`` (a rung of the issue ladder),
        ``issued_on`` (the revision's date) and ``sheets`` — a list of
        ``{"name", "geometry_sha"}`` for every sheet the revision names.

    Raises
    ------
    ValueError
        If *revision* is not recorded in the register.
    """
    from bridgecad_draw.contract import geometry_hash

    register = load()
    code = revision or register["current"]
    entry = next((r for r in register["revisions"] if r["code"] == code), None)
    if entry is None:
        raise ValueError(f"unknown revision {code!r}")

    return {
        "revision": code,
        "purpose": entry["purpose"],
        "issued_on": entry["date"],
        "sheets": [
            {"name": sheet, "geometry_sha": geometry_hash(project, sheet)}
            for sheet in entry["sheets"]
        ],
    }


__all__ = ["build_transmittal"]
