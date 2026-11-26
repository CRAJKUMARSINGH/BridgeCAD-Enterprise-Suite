#!/usr/bin/env python3
"""Netlify Deploy Readiness Test.

Checks the Netlify build configuration and the gateway's public drawing routes.
Runs as part of CI (see .github/workflows/ci.yml) and can be run locally:

    python scripts/test_netlify_readiness.py

Exit codes:
    0 — all configured checks passed
    1 — one or more checks failed
"""

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, ok, detail))
    icon = PASS if ok else FAIL
    print(f"  {icon}  {name}" + (f"  -- {detail}" if detail else ""))
    return ok


def section(title: str) -> None:
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")


# ── 1. Git submodule check ────────────────────────────────────────────────────
section("1. Git — no broken submodules")

gitmodules = ROOT / ".gitmodules"
check(
    ".gitmodules does not exist",
    not gitmodules.exists(),
    "file present — may cause Netlify clone failure" if gitmodules.exists() else "",
)

result = subprocess.run(["git", "ls-files", "--stage"], cwd=ROOT, capture_output=True, text=True)
gitlinks = [line for line in result.stdout.splitlines() if line.startswith("160000")]
check(
    "No gitlink (mode 160000) entries in index",
    len(gitlinks) == 0,
    f"found: {[line.split()[-1] for line in gitlinks]}" if gitlinks else "",
)

# ── 2. netlify.toml ───────────────────────────────────────────────────────────
section("2. netlify.toml")

toml = ROOT / "netlify.toml"
check("netlify.toml exists", toml.exists())
publish_dir = None
if toml.exists():
    content = toml.read_text(encoding="utf-8")
    publish_dir = tomllib.loads(content).get("build", {}).get("publish")
    check("Netlify publishes the Vite build", publish_dir == "frontend/dist")
    check("functions dir defined", "functions" in content)
    check("redirect /api/* defined", "/api/*" in content)
    check("security headers defined", "X-Frame-Options" in content)

# ── 3. Netlify Functions ──────────────────────────────────────────────────────
section("3. Netlify Functions")

fns_dir = ROOT / "netlify" / "functions"
check("netlify/functions/ exists", fns_dir.exists())
check("predict.js exists", (fns_dir / "predict.js").exists())
check("health.js exists", (fns_dir / "health.js").exists())

for fn in ["predict.js", "health.js"]:
    fn_path = fns_dir / fn
    if fn_path.exists():
        src = fn_path.read_text()
        check(f"{fn} exports handler", "exports.handler" in src)
        proxy_path = fns_dir.parent / "lib" / "drawing-proxy.cjs"
        config_src = (
            proxy_path.read_text() if "proxyDrawing" in src and proxy_path.is_file() else src
        )
        check(f"{fn} uses FASTAPI_URL env var", "FASTAPI_URL" in config_src)

# ── 4. Vite frontend source ─────────────────────────────────────────────────
section("4. Vite frontend source")

if publish_dir == "frontend/dist":
    frontend = (ROOT / publish_dir).parent
    for relative in (
        "index.html",
        "package-lock.json",
        "src/main.tsx",
        "public/samples/sample_input.xlsx",
    ):
        check(f"Frontend contains {relative}", (frontend / relative).is_file())

# ── 5. Python package integrity ───────────────────────────────────────────────
section("5. Python package integrity")

result = subprocess.run(
    [
        sys.executable,
        "-c",
        "import bridgecad; from bridgecad_api.main import app; "
        "paths = app.openapi()['paths']; "
        "assert 'post' in paths['/predict'] and 'post' in paths['/draw/ga']; "
        "assert 'get' in paths['/health']; print('ok')",
    ],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
check(
    "Enterprise gateway exposes the Netlify drawing routes",
    result.returncode == 0 and "ok" in result.stdout,
    result.stderr.strip()[:120] if result.returncode != 0 else "",
)

# ── 6. No PII in source ───────────────────────────────────────────────────────
section("6. No PII in tracked source files")

result = subprocess.run(
    ["git", "grep", "-l", r"@hotmail\|@gmail\|+91[0-9]\{10\}"],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
# Exclude: CI guard, this script itself, README/docs, and the defect-detection
# harnesses that must carry the patterns verbatim as fixtures/definitions.
_excluded_prefixes = (
    ".github/workflows/",  # CI guard contains the pattern as a literal string
    "README",
    "docs/",  # intentional contact info
    "scripts/test_netlify",  # this script contains the pattern as a grep arg
    "scripts/prove_detection.py",  # mutation fixture injects the literal pattern
    "tests/docs/test_doc_integrity.py",  # gate defines the literal patterns
    ".agents/",  # audit artifacts/vendored diffs, not shipped source
)
pii_files = [
    f
    for f in result.stdout.splitlines()
    if not any(f.startswith(p) for p in _excluded_prefixes)
    and not f.endswith(".md")  # status/report MDs are gitignored anyway
]
check("No PII in source", len(pii_files) == 0, f"found in: {pii_files}" if pii_files else "")

# ── 7. requirements.txt — no duplicates ──────────────────────────────────────
section("7. requirements.txt — no duplicate packages")

import re

pkgs: list[str] = []
for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        name = re.split(r"[>=<!;\[]", line)[0].lower().replace("-", "_")
        pkgs.append(name)
dupes = [p for p in set(pkgs) if pkgs.count(p) > 1]
check("No duplicate requirements", len(dupes) == 0, f"duplicates: {dupes}" if dupes else "")

# ── 8. .gitignore covers outputs and BridgeCanvas ────────────────────────────
section("8. .gitignore hygiene")

gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
check("outputs/*.dxf ignored", "outputs/*.dxf" in gitignore)
check("BridgeCanvas/ ignored", "BridgeCanvas/" in gitignore)
check("__pycache__/ ignored", "__pycache__/" in gitignore)
check("Telemetry file ignored", "Bridge_GAD_Telemetry.json" in gitignore)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
failed = [name for name, ok, _ in results if not ok]

print(f"  Result: {passed}/{total} checks passed")
if failed:
    print("\n  Failed checks:")
    for name in failed:
        print(f"    {FAIL}  {name}")
    print(f"\n  {'='*60}")
    print("  Netlify configuration checks failed")
    print(f"  {'='*60}\n")
    sys.exit(1)
else:
    print(f"\n  {'='*60}")
    print("  Netlify configuration checks passed")
    print(f"  {'='*60}\n")
    sys.exit(0)
