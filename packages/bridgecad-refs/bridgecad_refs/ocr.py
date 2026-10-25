"""OCR route for references with no text layer.

PIPELINE, versioned. Bump OCR_PIPELINE_VERSION on any change; every OCR fact is
then stale and must be re-proposed, because a pipeline change silently alters
values and a silent value change is the worst kind.

    1. rasterise 400 dpi greyscale        (text on drawings is small; 300 loses 3s)
    2. deskew via long horizontal runs    (scanned sets are never square)
    3. adaptive binarise
    4. tesseract --psm 11 (sparse text), eng, word confidences retained
    5. numeric repair, restricted to numeric context
    6. conf gate: facts below threshold go to needs_manual, not to proposed

NUMERIC REPAIR AND ITS LIMIT
    Inside a token that already contains a digit, O->0, l->1, S->5, B->8.
    Outside numeric context nothing is touched, so "SOFFIT" stays "SOFFIT" and
    does not become "50FFIT". Every repair is recorded as `repaired_from`, so a
    reviewer sees the original glyphs, not the repaired guess.

WHY CONFIDENCE IS CARRIED
    An OCR value at 62% confidence and one at 98% are not the same evidence. The
    tolerance a value may be asserted at is derived from confidence and stated
    precision together.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

OCR_PIPELINE_VERSION = 1
DPI = 400
MIN_WORD_CONF = 70.0  # below this, a fact is needs_manual
ASSERT_CONF_FLOOR = 90.0  # below this, no 1 mm assertion

REPAIR_MAP = str.maketrans({"O": "0", "o": "0", "l": "1", "S": "5", "B": "8"})
DIGIT_CONTEXT = str.maketrans({"O": "0", "o": "0", "l": "1", "S": "5", "B": "8"})


@dataclass(frozen=True)
class OcrWord:
    text: str
    conf: float
    x0: float
    top: float
    x1: float
    bottom: float
    repaired_from: str | None = None


def available() -> bool:
    return shutil.which("tesseract") is not None


def rasterise(pdf_path: Path, dpi: int = DPI):
    """Page images via pypdfium2 — no poppler dependency to install."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    for page in pdf:
        yield page.render(scale=dpi / 72).to_pil().convert("L")


def deskew(image):
    """Straighten using the dominant near-horizontal run. Drawings are drawn
    square; a scanned set is not, and 1 degree over 400 mm is 7 mm of drift."""
    import numpy as np
    from PIL import Image

    a = np.asarray(image)
    edges = (a < 128).astype(np.uint8)
    row_sums = edges.sum(axis=1)
    if row_sums.max() == 0:
        return image
    best, best_angle = -1, 0.0
    for angle in [x / 4 for x in range(-12, 13)]:
        rot = image.rotate(angle, resample=Image.BILINEAR, expand=False, fillcolor=255)
        score = (np.asarray(rot) < 128).astype(np.uint8).sum(axis=1).max()
        if score > best:
            best, best_angle = score, angle
    return image.rotate(best_angle, resample=Image.BILINEAR, expand=False, fillcolor=255)


def binarise(image):
    return image.point(lambda p: 255 if p > 160 else 0, mode="L")


def repair_token(token: str) -> tuple[str, str | None]:
    """Repair only if the token is numeric-ish. Returns (text, original_or_None)."""
    if not any(ch.isdigit() for ch in token):
        return token, None
    if not all(ch.isdigit() or ch in ".mM%°" or ch in "OolSB" for ch in token):
        return token, None
    fixed = token.translate(DIGIT_CONTEXT)
    return (fixed, token) if fixed != token else (token, None)


def ocr_page(image) -> list[OcrWord]:
    import pytesseract
    from pytesseract import Output

    data = pytesseract.image_to_data(image, lang="eng", config="--psm 11", output_type=Output.DICT)
    words: list[OcrWord] = []
    for i, text in enumerate(data["text"]):
        if not text.strip():
            continue
        conf = float(data["conf"][i])
        if conf < 0:
            continue
        repaired, original = repair_token(text.strip())
        words.append(
            OcrWord(
                repaired,
                conf,
                float(data["left"][i]),
                float(data["top"][i]),
                float(data["left"][i] + data["width"][i]),
                float(data["top"][i] + data["height"][i]),
                original,
            )
        )
    return words


def engine_version() -> str:
    import pytesseract

    return pytesseract.get_tesseract_version().public


def rows_to_lines(words: list[OcrWord], tol: int = 8) -> list[tuple[str, list[OcrWord]]]:
    """Group words into lines by vertical proximity. Same contract as the text
    layer route, so the parsers are shared and neither path gets its own bugs."""
    rows: dict[int, list[OcrWord]] = {}
    for w in words:
        key = round(w.top / tol) * tol
        rows.setdefault(key, []).append(w)
    return [
        (
            " ".join(w.text for w in sorted(rows[k], key=lambda x: x.x0)),
            sorted(rows[k], key=lambda x: x.x0),
        )
        for k in sorted(rows)
    ]
