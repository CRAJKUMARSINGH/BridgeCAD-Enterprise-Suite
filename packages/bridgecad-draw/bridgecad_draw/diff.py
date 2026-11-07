"""bridgecad_draw.diff — classify entity differences between two sheet renders.

Matching is by fingerprint multiset first; removed/added pairs of the same
dxftype+layer within 50 mm are classified MOVED rather than ADDED+REMOVED,
and same-geometry/different-style pairs are RESTYLED.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from .fingerprint import EntitySig

_MOVE_TOL_MM = 50.0


class ChangeKind(StrEnum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MOVED = "MOVED"
    RESTYLED = "RESTYLED"  # layer, colour, linetype, text content


@dataclass(frozen=True)
class Change:
    sheet_no: int
    key: str
    layer: str
    dxftype: str
    kind: ChangeKind
    description: str = ""
    from_xy: tuple[float, float] | None = None
    to_xy: tuple[float, float] | None = None


def _multiset_diff(
    old: dict[str, EntitySig], new: dict[str, EntitySig]
) -> tuple[list[EntitySig], list[EntitySig]]:
    """Fingerprints in old-not-new and new-not-old (multiset semantics)."""
    from collections import Counter

    old_c: Counter[str] = Counter(v.fp for v in old.values())
    new_c: Counter[str] = Counter(v.fp for v in new.values())
    removed_fps = list((old_c - new_c).elements())
    added_fps = list((new_c - old_c).elements())
    removed = [v for v in old.values() if v.fp in removed_fps]
    added = [v for v in new.values() if v.fp in added_fps]

    # multiset correctness: keep only as many entries as the count allows
    def _trim(sigs: list[EntitySig], fps: list[str]) -> list[EntitySig]:
        counts: dict[str, int] = {}
        for fp in fps:
            counts[fp] = counts.get(fp, 0) + 1
        out: list[EntitySig] = []
        for sig in sigs:
            if counts.get(sig.fp, 0) > 0:
                counts[sig.fp] -= 1
                out.append(sig)
        return out

    return _trim(removed, removed_fps), _trim(added, added_fps)


def _dist(a: EntitySig, b: EntitySig) -> float:
    return math.hypot(a.cx - b.cx, a.cy - b.cy)


def diff_sheets(
    old: dict[str, EntitySig],
    new: dict[str, EntitySig],
    sheet_no: int = 0,
) -> list[Change]:
    """Classify the entity differences between two signature maps."""
    removed, added = _multiset_diff(old, new)
    changes: list[Change] = []

    # Pair same-type/layer removed+added within 50 mm as MOVED
    still_added = list(added)
    for rem in removed:
        best_i = -1
        best_d = _MOVE_TOL_MM
        for i, add in enumerate(still_added):
            if add.dxftype != rem.dxftype or add.layer != rem.layer:
                continue
            d = _dist(rem, add)
            if d < best_d:
                best_d, best_i = d, i
        if best_i >= 0:
            add = still_added.pop(best_i)
            changes.append(
                Change(
                    sheet_no=sheet_no,
                    key=add_key(new, add),
                    layer=rem.layer,
                    dxftype=rem.dxftype,
                    kind=ChangeKind.MOVED,
                    description=f"moved {best_d:.0f} mm",
                    from_xy=(rem.cx, rem.cy),
                    to_xy=(add.cx, add.cy),
                )
            )
        else:
            # RESTYLED: same geometry fingerprint, different full fingerprint
            restyled = next(
                (a for a in still_added if a.geo_fp == rem.geo_fp and a.fp != rem.fp), None
            )
            if restyled is not None:
                still_added.remove(restyled)
                changes.append(
                    Change(
                        sheet_no=sheet_no,
                        key=add_key(new, restyled),
                        layer=restyled.layer,
                        dxftype=restyled.dxftype,
                        kind=ChangeKind.RESTYLED,
                        description="style/text change at same geometry",
                        from_xy=(rem.cx, rem.cy),
                        to_xy=(restyled.cx, restyled.cy),
                    )
                )
            else:
                changes.append(
                    Change(
                        sheet_no=sheet_no,
                        key=old_key(old, rem),
                        layer=rem.layer,
                        dxftype=rem.dxftype,
                        kind=ChangeKind.REMOVED,
                        from_xy=(rem.cx, rem.cy),
                    )
                )

    for add in still_added:
        changes.append(
            Change(
                sheet_no=sheet_no,
                key=add_key(new, add),
                layer=add.layer,
                dxftype=add.dxftype,
                kind=ChangeKind.ADDED,
                to_xy=(add.cx, add.cy),
            )
        )
    return changes


def _key_of(mapping: dict[str, EntitySig], sig: EntitySig) -> str:
    for k, v in mapping.items():
        if v is sig:
            return k
    return "?"


def old_key(old: dict[str, EntitySig], sig: EntitySig) -> str:
    return _key_of(old, sig)


def add_key(new: dict[str, EntitySig], sig: EntitySig) -> str:
    return _key_of(new, sig)


__all__ = ["Change", "ChangeKind", "diff_sheets"]
