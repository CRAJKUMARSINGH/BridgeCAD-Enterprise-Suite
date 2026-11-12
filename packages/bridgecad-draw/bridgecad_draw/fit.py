"""
bridgecad_draw.fit — standard-scale selection for Sheet 2 / Sheet 8.

Problem (type 010 — 270 m, 9 spans):
  ``sc_h = draw_w / total_len`` produces an arbitrary scale (e.g. 1:382).
  ``draw_title_block(scale_str="1:100")`` then lies — the printed caption
  disagrees with the actual geometry.  At 1:382 the pier shaft is 3.9 mm
  wide, 21 chainage labels land in a 20 mm band, and 8 ΔREF strings all
  stack at the same x.

Fix:
  ``choose_fit()`` selects the **largest standard-rung scale** that keeps
  text ≥ ``MIN_TEXT_MM`` and annotation spacing ≥ ``MIN_ANNOT_GAP_MM``.
  When even the coarsest rung (1:500) cannot fit without band-breaking, it
  returns ``Fit(..., broken=True, bands=N)`` and the sheet is drawn in N
  horizontal strips with 2 m overlap and match-lines.

  The title block then prints ``"1:{fit.denom} H  1:{fit.denom//v_exag} V"``
  — no discrepancy is possible.

Usage inside a sheet generator::

    from .fit import choose_fit, Fit

    fit = choose_fit(total_len, draw_w, n_annotations=span_count + 2)
    sc_h  = fit.mm_per_m
    # title block:
    scale_str = f"{fit.scale_str} H  1:{fit.denom // int(v_exag)} V"
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Standard IRC SP:55 scale ladder for plan-view sheets.
LADDER: tuple[int, ...] = (50, 75, 100, 150, 200, 250, 300, 400, 500)

MIN_TEXT_MM: float = 2.5       # floor for adaptive text height
MIN_ANNOT_GAP_MM: float = 8.0  # minimum clear gap between adjacent pier labels


@dataclass(frozen=True)
class Fit:
    """Result of ``choose_fit()``.

    Attributes
    ----------
    denom : int
        Scale denominator (e.g. 100 for 1:100).
    mm_per_m : float
        Sheet millimetres per real metre (= 1000 / denom).
    broken : bool
        ``True`` when the total length exceeds one band at the coarsest rung.
        The generator must split the view into ``bands`` horizontal strips.
    bands : int
        Number of drawing bands needed (always 1 when ``broken`` is ``False``).
    """
    denom: int
    mm_per_m: float
    broken: bool
    bands: int

    @property
    def scale_str(self) -> str:
        """Human-readable scale string, e.g. ``'1:100'``."""
        return f"1:{self.denom}"


def choose_fit(
    length_m: float,
    draw_w_mm: float,
    n_annotations: int = 0,
    min_text_mm: float = MIN_TEXT_MM,
    min_annot_gap_mm: float = MIN_ANNOT_GAP_MM,
) -> Fit:
    """Return the largest standard scale that keeps the sheet legible.

    Parameters
    ----------
    length_m : float
        Total drawn length in metres (e.g. ``total_length_m`` for Sheet 2).
    draw_w_mm : float
        Available drawing width on the sheet in millimetres.
    n_annotations : int
        Approximate number of pier / span labels along the axis.
        Used to gate the minimum inter-annotation spacing.
    min_text_mm : float
        Minimum allowable text height in sheet mm.  Below this the adaptive
        ``th = max(2.5, sc_h * 0.4)`` formula collapses to illegibility.
    min_annot_gap_mm : float
        Minimum clear gap between adjacent labels along the chainage axis.

    Returns
    -------
    Fit
        The best single-band fit, or a broken-band fit when necessary.
    """
    for denom in LADDER:
        mm_per_m = 1000.0 / denom
        # (1) Does the bridge fit horizontally?
        if length_m * mm_per_m > draw_w_mm:
            continue
        # (2) Will text height be legible?  th = max(min_text_mm, mm_per_m * 0.4)
        if mm_per_m * 0.4 < min_text_mm:
            continue
        # (3) Will per-pier annotations have enough room?
        if n_annotations > 1:
            gap = (length_m * mm_per_m) / n_annotations
            if gap < min_annot_gap_mm:
                continue
        return Fit(denom=denom, mm_per_m=mm_per_m, broken=False, bands=1)

    # No single rung works — use the coarsest and split into bands.
    denom = LADDER[-1]
    mm_per_m = 1000.0 / denom
    band_len_m = draw_w_mm / mm_per_m          # real metres per band
    n_bands = math.ceil(length_m / max(band_len_m * 0.95, 0.001))
    return Fit(denom=denom, mm_per_m=mm_per_m, broken=True, bands=max(2, n_bands))


def band_windows(
    total_m: float,
    draw_w_mm: float,
    mm_per_m: float,
    overlap_m: float = 2.0,
) -> list[tuple[float, float]]:
    """Return (start_m, end_m) chainage windows for multi-band rendering.

    Each band overlaps the next by ``overlap_m`` metres so a match-line can
    be drawn at both cut edges without losing geometry.

    Parameters
    ----------
    total_m : float
        Total bridge length in metres.
    draw_w_mm : float
        Available band width in mm.
    mm_per_m : float
        Scale factor (= 1000 / denom).
    overlap_m : float
        Metres of geometry repeated in the overlap zone.
    """
    band_w_m = draw_w_mm / mm_per_m
    step_m = max(band_w_m - overlap_m, 1.0)
    windows: list[tuple[float, float]] = []
    start = 0.0
    while start < total_m:
        end = min(start + band_w_m, total_m)
        windows.append((start, end))
        start += step_m
        if end >= total_m:
            break
    return windows


__all__ = ["Fit", "LADDER", "choose_fit", "band_windows"]
