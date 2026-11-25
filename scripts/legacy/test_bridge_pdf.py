"""
Test script to generate best bridge design and output as PDF
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from bridge_gad.bridge_generator import BridgeGADGenerator


def generate_bridge_dxf():
    """Generate bridge DXF from best available input"""
    print("=" * 60)
    print("Bridge GAD Generator - PDF Test")
    print("=" * 60)

    # Use the best sample input
    input_file = Path("inputs/sample_input.xlsx")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_dxf = output_dir / "best_bridge.dxf"

    print(f"\n📁 Input: {input_file}")
    print(f"📁 Output: {output_dxf}")

    # Generate bridge
    print("\n🔨 Generating bridge design...")
    generator = BridgeGADGenerator()

    try:
        success = generator.generate_complete_drawing(input_file, output_dxf)

        if success:
            print("✅ Bridge DXF generated successfully!")
            return output_dxf
        else:
            print("❌ Failed to generate bridge DXF")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return None


def convert_dxf_to_pdf(dxf_file):
    """Convert DXF to PDF using ezdxf"""
    print("\n🔄 Converting DXF to PDF...")

    try:
        import ezdxf
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

        # Load DXF
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()

        # Create output PDF path
        pdf_file = dxf_file.with_suffix(".pdf")

        # Setup rendering
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)

        # Render
        Frontend(ctx, out).draw_layout(msp, finalize=True)

        # Save as PDF
        fig.savefig(pdf_file, dpi=300, bbox_inches="tight")
        plt.close(fig)

        print(f"✅ PDF created: {pdf_file}")
        return pdf_file

    except ImportError:
        print("⚠️  matplotlib not available, trying alternative method...")
        return convert_dxf_to_pdf_alternative(dxf_file)
    except Exception as e:
        print(f"❌ PDF conversion error: {e}")
        import traceback

        traceback.print_exc()
        return None


def convert_dxf_to_pdf_alternative(dxf_file):
    """Alternative PDF conversion using reportlab"""
    print("🔄 Using alternative PDF conversion...")

    try:
        import ezdxf
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.pdfgen import canvas

        # Load DXF
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()

        # Create PDF
        pdf_file = dxf_file.with_suffix(".pdf")
        c = canvas.Canvas(str(pdf_file), pagesize=landscape(A4))

        # Get drawing bounds
        extents = msp.query("*")
        if extents:
            # Simple text representation
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 500, "Bridge General Arrangement Drawing")
            c.setFont("Helvetica", 12)
            c.drawString(100, 470, f"Generated from: {dxf_file.name}")
            c.drawString(100, 450, f"Total entities: {len(list(msp))}")

            # Add note
            c.setFont("Helvetica", 10)
            c.drawString(
                100,
                400,
                "Note: For full visualization, open the DXF file in AutoCAD or similar CAD software.",
            )
            c.drawString(100, 380, f"DXF file location: {dxf_file.absolute()}")

        c.save()
        print(f"✅ PDF created: {pdf_file}")
        return pdf_file

    except Exception as e:
        print(f"❌ Alternative PDF conversion failed: {e}")
        return None


def main():
    """Main test function"""
    # Generate DXF
    dxf_file = generate_bridge_dxf()

    if not dxf_file:
        print("\n❌ Failed to generate bridge")
        return False

    # Convert to PDF
    pdf_file = convert_dxf_to_pdf(dxf_file)

    if pdf_file:
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"\n📄 DXF File: {dxf_file.absolute()}")
        print(f"📄 PDF File: {pdf_file.absolute()}")
        print("\nYou can now:")
        print("1. Open the PDF to view the bridge design")
        print("2. Open the DXF in AutoCAD for detailed editing")
        return True
    else:
        print("\n⚠️  DXF generated but PDF conversion failed")
        print(f"📄 DXF File: {dxf_file.absolute()}")
        print("\nYou can still open the DXF file in AutoCAD or similar CAD software")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
