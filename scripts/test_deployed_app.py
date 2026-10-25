#!/usr/bin/env python3
"""Robotic Test for Deployed Bridge GAD Application.

Tests the deployed application at https://bridge-gad.netlify.app/
using sample inputs and generates PDFs in downloads folder.

Usage:
    python scripts/test_deployed_app.py
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration
DEPLOYED_URL = "https://bridge-gad.netlify.app"
API_BASE = f"{DEPLOYED_URL}/.netlify/functions"
SAMPLES_DIR = Path("public/samples")
DOWNLOADS_DIR = Path("downloads")

# Sample input files to test
SAMPLE_FILES = [
    "sample_input.xlsx",
    "bridge_simple_12m.xlsx",
    "bridge_comprehensive.xlsx",
    "bridge_large.xlsx",
    "bridge_23span.xlsx",
    "template_simple_12m.xlsx",
    "template_continuous_3x12m.xlsx",
    "template_girder_4x18m.xlsx",
    "template_box_culvert_8m.xlsx",
    "template_arch_24m.xlsx",
]


def test_health_endpoint() -> bool:
    """Test the health endpoint of the deployed application."""
    try:
        health_url = f"{API_BASE}/health"
        logger.info(f"Testing health endpoint: {health_url}")
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Health check passed: {response.json()}")
            return True
        else:
            logger.error(f"❌ Health check failed: status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False


def test_predict_endpoint(excel_file: Path) -> dict[str, Any]:
    """Test the predict endpoint with a sample Excel file."""
    result = {
        "file": excel_file.name,
        "success": False,
        "status_code": None,
        "response_time": None,
        "error": None,
        "output_file": None,
    }

    start_time = time.time()

    try:
        predict_url = f"{API_BASE}/predict"
        logger.info(f"Testing predict endpoint with: {excel_file.name}")

        # Read Excel file and convert to JSON
        df = pd.read_excel(excel_file)
        # Convert to parameters dict (assuming first column is variable, second is value)
        params = {}
        if len(df.columns) >= 2:
            for _, row in df.iterrows():
                var = str(row.iloc[0]).strip()
                val = row.iloc[1]
                if var and not str(var).startswith("Unnamed"):
                    params[var] = val

        # Send request
        response = requests.post(
            predict_url,
            json={"parameters": params},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        result["status_code"] = response.status_code
        result["response_time"] = round(time.time() - start_time, 2)

        if response.status_code == 200:
            logger.info(f"✅ Predict request successful: {result['response_time']}s")
            result["success"] = True

            # Try to save response if it contains file data
            try:
                response_data = response.json()
                if "pdf_data" in response_data or "drawing_data" in response_data:
                    output_file = DOWNLOADS_DIR / f"{excel_file.stem}_response.json"
                    output_file.write_text(json.dumps(response_data, indent=2))
                    result["output_file"] = str(output_file)
                    logger.info(f"📄 Saved response to: {output_file}")
            except Exception:
                pass
        else:
            logger.error(f"❌ Predict request failed: status {response.status_code}")
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"

    except Exception as e:
        result["error"] = str(e)
        result["response_time"] = round(time.time() - start_time, 2)
        logger.error(f"❌ Predict endpoint error: {e}")

    return result


def test_frontend_load() -> bool:
    """Test if the frontend loads successfully."""
    try:
        logger.info(f"Testing frontend load: {DEPLOYED_URL}")
        response = requests.get(DEPLOYED_URL, timeout=10)
        if response.status_code == 200:
            content = response.text
            has_title = "<title>" in content
            has_app_link = "/app" in content or "app" in content.lower()
            logger.info(
                f"✅ Frontend loaded successfully (title: {has_title}, app link: {has_app_link})"
            )
            return True
        else:
            logger.error(f"❌ Frontend load failed: status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Frontend load error: {e}")
        return False


def generate_local_pdfs() -> list[dict[str, Any]]:
    """Generate PDFs locally using sample inputs (fallback if API fails)."""
    logger.info("🔄 Generating PDFs locally as fallback...")

    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    try:
        from bridge_gad.bridge_generator import BridgeGADGenerator
        from bridge_gad.dxf_to_pdf import RenderOptions, convert_dxf_to_pdf
    except ImportError as e:
        logger.error(f"❌ Cannot import local modules: {e}")
        return []

    results = []
    gen = BridgeGADGenerator()

    for sample_file in SAMPLE_FILES:
        sample_path = SAMPLES_DIR / sample_file
        if not sample_path.exists():
            logger.warning(f"⚠️  Sample file not found: {sample_file}")
            continue

        result = {
            "file": sample_file,
            "success": False,
            "dxf_file": None,
            "pdf_file": None,
            "error": None,
        }

        try:
            # Generate DXF
            dxf_output = DOWNLOADS_DIR / f"{sample_path.stem}_local.dxf"
            success = gen.generate_complete_drawing(sample_path, dxf_output)

            if success and dxf_output.exists():
                result["dxf_file"] = str(dxf_output)
                logger.info(f"✅ Generated DXF: {dxf_output.name}")

                # Convert to PDF with improved error handling (text entities skipped if rendering fails)
                pdf_output = DOWNLOADS_DIR / f"{sample_path.stem}_local.pdf"
                try:
                    # Use higher DPI and lineweight scale for better quality
                    improved_opts = RenderOptions(layout="A4_landscape", dpi=150, lweight_scale=1.0)
                    convert_dxf_to_pdf(dxf_output, pdf_output, opts=improved_opts)

                    if (
                        pdf_output.exists() and pdf_output.stat().st_size > 10000
                    ):  # Check if PDF has substantial content
                        result["pdf_file"] = str(pdf_output)
                        result["success"] = True
                        logger.info(
                            f"✅ Generated PDF: {pdf_output.name} ({pdf_output.stat().st_size} bytes)"
                        )
                    else:
                        result["error"] = (
                            f"PDF conversion failed - file too small: {pdf_output.stat().st_size if pdf_output.exists() else 0} bytes"
                        )
                        logger.error(f"❌ {result['error']}")
                except Exception as pdf_error:
                    result["error"] = f"PDF conversion exception: {pdf_error!s}"
                    logger.error(f"❌ {result['error']}")
            else:
                result["error"] = "DXF generation failed"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Error processing {sample_file}: {e}")

        results.append(result)

    return results


def main():
    """Main test execution."""
    logger.info("🤖 Robotic Test for Deployed Bridge GAD Application")
    logger.info(f"🌐 Target URL: {DEPLOYED_URL}")
    logger.info("=" * 70)

    # Create downloads directory
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    logger.info(f"📁 Downloads directory: {DOWNLOADS_DIR}")

    # Test results
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "deployed_url": DEPLOYED_URL,
        "tests": {},
        "sample_tests": [],
        "local_generation": [],
    }

    # Test 1: Frontend Load
    logger.info("\n📋 Test 1: Frontend Load")
    logger.info("-" * 70)
    frontend_ok = test_frontend_load()
    all_results["tests"]["frontend_load"] = frontend_ok

    # Test 2: Health Endpoint
    logger.info("\n📋 Test 2: Health Endpoint")
    logger.info("-" * 70)
    health_ok = test_health_endpoint()
    all_results["tests"]["health_endpoint"] = health_ok

    # Test 3: API Predict with Sample Files
    logger.info("\n📋 Test 3: API Predict with Sample Files")
    logger.info("-" * 70)

    if health_ok:
        for sample_file in SAMPLE_FILES:
            sample_path = SAMPLES_DIR / sample_file
            if sample_path.exists():
                result = test_predict_endpoint(sample_path)
                all_results["sample_tests"].append(result)
            else:
                logger.warning(f"⚠️  Sample file not found: {sample_file}")
    else:
        logger.warning("⚠️  Skipping API tests (health check failed)")

    # Test 4: Local PDF Generation (Fallback)
    logger.info("\n📋 Test 4: Local PDF Generation (Fallback)")
    logger.info("-" * 70)
    local_results = generate_local_pdfs()
    all_results["local_generation"] = local_results

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)

    api_success = sum(1 for r in all_results["sample_tests"] if r["success"])
    api_total = len(all_results["sample_tests"])

    local_success = sum(1 for r in all_results["local_generation"] if r["success"])
    local_total = len(all_results["local_generation"])

    logger.info(f"Frontend Load: {'✅' if frontend_ok else '❌'}")
    logger.info(f"Health Endpoint: {'✅' if health_ok else '❌'}")
    logger.info(f"API Predict Tests: {api_success}/{api_total} passed")
    logger.info(f"Local PDF Generation: {local_success}/{local_total} passed")

    # Save results
    results_file = DOWNLOADS_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.write_text(json.dumps(all_results, indent=2))
    logger.info(f"📄 Test results saved to: {results_file}")

    # Count total generated files
    pdf_count = len(list(DOWNLOADS_DIR.glob("*.pdf")))
    dxf_count = len(list(DOWNLOADS_DIR.glob("*.dxf")))
    logger.info(f"📁 Generated files: {pdf_count} PDFs, {dxf_count} DXFs")

    if local_success > 0:
        logger.info(f"✅ Successfully generated {local_success} PDF(s) in downloads folder")
        return 0
    else:
        logger.error("❌ No PDFs were generated")
        return 1


if __name__ == "__main__":
    sys.exit(main())
