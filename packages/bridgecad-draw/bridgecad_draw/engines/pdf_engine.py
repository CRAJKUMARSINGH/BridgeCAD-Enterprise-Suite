"""PDF/A-1b archival export (W07).

The drawing is rendered to PDF by ezdxf's PyMuPDF backend, then upgraded to
PDF/A-1b: the XMP packet declares ``pdfaid:part=1`` / ``pdfaid:conformance=B``
and the catalogue carries an ``OutputIntent`` of subtype ``GTS_PDFA1`` with an
sRGB ICC profile. Saves are reproducible, so two exports of the same drawing
are byte-identical.

veraPDF is the authority on conformance, but it is an external binary. This
module only guarantees the structural markers; ``scripts/check_pdfa.py`` runs
veraPDF when it is on PATH and skips (never silently passes) when it is not.

Usage
-----
    from bridgecad_draw.engines.pdf_engine import export_pdf_a, inspect_pdf_a

    export_pdf_a(doc, "out/plan.dxf.pdf")
    facts = inspect_pdf_a("out/plan.dxf.pdf")   # -> {"is_pdfa1b": True, ...}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: A1, the suite's sheet size (IRC SP:55).
DEFAULT_PAPER_MM = (841.0, 594.0)
DEFAULT_MARGIN_MM = 10.0

_XMP = """<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
   <pdfaid:part>1</pdfaid:part>
   <pdfaid:conformance>B</pdfaid:conformance>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def _backend():
    from ezdxf.addons.drawing import pymupdf as ezpm

    return ezpm


def render_layout_pdf(
    doc: Any,
    *,
    paper_mm: tuple[float, float] = DEFAULT_PAPER_MM,
    margin_mm: float = DEFAULT_MARGIN_MM,
) -> bytes:
    """Render the model space of *doc* to single-page PDF bytes."""
    from ezdxf.addons.drawing import Frontend, RenderContext, config, layout

    cfg = config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE,
        color_policy=config.ColorPolicy.BLACK,
        lineweight_scaling=0.5,
        min_lineweight=0.15,
        lineweight_policy=config.LineweightPolicy.ABSOLUTE,
    )
    backend = _backend().PyMuPdfBackend()
    Frontend(RenderContext(doc), backend, config=cfg).draw_layout(doc.modelspace(), finalize=True)
    page = layout.Page(*paper_mm, layout.Units.mm, margins=layout.Margins.all(margin_mm))
    return backend.get_pdf_bytes(page, settings=layout.Settings(fit_page=True))


def to_pdf_a1b(pdf_bytes: bytes) -> bytes:
    """Upgrade rendered *pdf_bytes* to PDF/A-1b and return the saved bytes."""
    import pymupdf
    from PIL import ImageCms

    pdf = pymupdf.open("pdf", pdf_bytes)
    pdf.set_xml_metadata(_XMP)

    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    icc_xref = pdf.get_new_xref()
    pdf.update_object(icc_xref, "<<>>")
    pdf.update_stream(icc_xref, icc)
    pdf.xref_set_key(icc_xref, "N", "3")

    oi_xref = pdf.get_new_xref()
    pdf.update_object(
        oi_xref,
        "<< /Type /OutputIntent /S /GTS_PDFA1 "
        "/OutputConditionIdentifier (sRGB IEC61966-2.1) "
        "/RegistryName (http://www.color.org) "
        f"/Info (sRGB IEC61966-2.1) /DestOutputProfile {icc_xref} 0 R >>",
    )
    root = pdf.pdf_catalog()
    pdf.xref_set_key(root, "OutputIntents", f"[{oi_xref} 0 R]")
    pdf.xref_set_key(root, "Metadata", f"{pdf.xref_xml_metadata()} 0 R")
    pdf.set_metadata({"title": "GAD", "author": "BridgeCAD", "producer": "BridgeCAD"})

    return pdf.tobytes(garbage=4, deflate=True, clean=True, no_new_id=True, reproducible=True)


def export_pdf_a(
    doc: Any,
    output_path: str | Path,
    *,
    paper_mm: tuple[float, float] = DEFAULT_PAPER_MM,
    margin_mm: float = DEFAULT_MARGIN_MM,
) -> Path:
    """Render *doc*, upgrade to PDF/A-1b, write it, and return the path."""
    data = to_pdf_a1b(render_layout_pdf(doc, paper_mm=paper_mm, margin_mm=margin_mm))
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def inspect_pdf_a(source: str | Path | bytes) -> dict[str, Any]:
    """Structural PDF/A-1b facts about *source* (path or bytes).

    This is the honest in-process check: it verifies the markers PDF/A-1b
    requires. It is not a substitute for veraPDF.
    """
    import pymupdf

    pdf = pymupdf.open("pdf", source) if isinstance(source, bytes) else pymupdf.open(str(source))
    try:
        root = pdf.pdf_catalog()
        keys = pdf.xref_get_keys(root)
        oi = pdf.xref_get_key(root, "OutputIntents")
        oi_xref = int(str(oi[1]).strip("[] \t").split()[0]) if oi[0] == "array" else 0
        subtype = pdf.xref_get_key(oi_xref, "S")[1] if oi_xref else ""
        dest = pdf.xref_get_key(oi_xref, "DestOutputProfile")[1] if oi_xref else ""
        dest_xref = int(dest.split()[0]) if dest else 0
        icc_n = pdf.xref_get_key(dest_xref, "N")[1] if dest_xref else ""
        xmp = pdf.get_xml_metadata()
        return {
            "pages": pdf.page_count,
            "encrypted": pdf.is_encrypted,
            "has_metadata": "Metadata" in keys,
            "has_output_intent": oi[0] == "array",
            "output_intent_subtype": subtype,
            "icc_components": icc_n,
            "pdfaid_part": "1" if "<pdfaid:part>1<" in xmp else "",
            "pdfaid_conformance": "B" if "<pdfaid:conformance>B<" in xmp else "",
        }
    finally:
        pdf.close()


def is_pdf_a1b(facts: dict[str, Any]) -> bool:
    """True when *facts* (from :func:`inspect_pdf_a`) satisfy PDF/A-1b markers."""
    return (
        facts["pages"] >= 1
        and not facts["encrypted"]
        and facts["has_metadata"]
        and facts["has_output_intent"]
        and facts["output_intent_subtype"] == "/GTS_PDFA1"
        and facts["icc_components"] == "3"
        and facts["pdfaid_part"] == "1"
        and facts["pdfaid_conformance"] == "B"
    )


__all__ = [
    "DEFAULT_MARGIN_MM",
    "DEFAULT_PAPER_MM",
    "export_pdf_a",
    "inspect_pdf_a",
    "is_pdf_a1b",
    "render_layout_pdf",
    "to_pdf_a1b",
]
