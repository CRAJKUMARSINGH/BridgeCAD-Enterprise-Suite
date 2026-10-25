#!/usr/bin/env python3
"""Prove every documented defect is actually detectable by a guard.

Method: for each defect, copy the repo to a throwaway tree, reintroduce the
defect with a surgical mutation, run the guard, and assert it FAILS.

A control run comes first: the integrity suite must PASS on an unmutated copy.
Without the control, a guard that fails for unrelated reasons would score as
"detected" and the proof would be worthless.

Output: JSON with detected/total. Exit 0 only if the control passes and every
mutation is detected.

Usage:
    python scripts/prove_detection.py
    python scripts/prove_detection.py --json
    python scripts/prove_detection.py --only D01,D02,X03
    python scripts/prove_detection.py --keep            # keep temp trees
    python scripts/prove_detection.py --jobs 8
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INTEGRITY = "tests/docs/test_doc_integrity.py"

# Heavy or generated — never worth copying.
IGNORE_DIRS = frozenset(
    {
        ".git",
        "site",
        "site-api",
        "node_modules",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        ".benchmarks",
        "03_outputs",
        "outputs",
        "test_run_sample",
        "TEST_RUN_OUTPUT",
        "docs/api/_build",
    }
)


# ── mutation primitives ──────────────────────────────────────────────────────
def append(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.write_text(p.read_text(encoding="utf-8") + "\n" + text + "\n", encoding="utf-8")


def replace(root: Path, rel: str, old: str, new: str, count: int = -1) -> None:
    p = root / rel
    body = p.read_text(encoding="utf-8")
    if old not in body:
        raise AssertionError(f"{old!r} not found in {rel} — repo drifted from the harness")
    p.write_text(body.replace(old, new, count), encoding="utf-8")


def create(root: Path, rel: str, text: str = "") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ── mutations ────────────────────────────────────────────────────────────────
@dataclass
class Mutation:
    id: str
    what: str
    guard: str
    apply: Callable[[Path], None]
    severity: str = "medium"
    note: str = ""
    detected: bool = field(default=False, init=False)
    ms: int = field(default=0, init=False)
    detail: str = field(default="", init=False)


def _d01(root: Path) -> None:
    append(root, "docs/getting-started.md", '```bash\ncd "BridgeCAD Enterprise Suite"\n```')


def _d02(root: Path) -> None:
    append(root, "docs/getting-started.md", "[gone](no-such-file.md)")


def _d03(root: Path) -> None:
    append(root, "docs/getting-started.md", "```bash\npip install -r requirements_lean.txt\n```")


def _d04(root: Path) -> None:
    append(root, "README.md", "Issues: CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse")


def _d05(root: Path) -> None:
    append(
        root,
        "CHANGELOG.md",
        "[rc1]: https://github.com/bridgecad/enterprise-suite/releases/tag/v0.1.0-rc1",
    )


def _d06(root: Path) -> None:
    append(root, "README.md", "```bash\ngit clone https://github.com/YOUR_USERNAME/x.git\n```")


def _d07(root: Path) -> None:
    """Swap the two orientation rows so the front door leads with the legacy app.

    Replacing the phrase "repo root" is not enough: the README names it twice
    (`python -m bridgecad info  # interpreter, repo root, ...`), so a single
    substitution leaves the guard satisfied. Suite-first is a property of the
    row order, so the mutation has to move the rows.
    """
    active = (
        "| **BridgeCAD Enterprise Suite** | repo root | ✅ **ACTIVE** · v0.1.0-rc1 "
        "| `python -m bridgecad` |"
    )
    legacy = (
        "| Ultimate Bridge GAD Generator | `streamlit_app_ultimate.py` + `src/bridge_gad/` "
        "| 🏛️ LEGACY | `streamlit run streamlit_app_ultimate.py` |"
    )
    replace(root, "README.md", f"{active}\n{legacy}", f"{legacy}\n{active}", 1)


def _d08(root: Path) -> None:
    replace(root, "README.md", "python -m bridgecad", "python -m bc")
    replace(root, "GUIDE.md", "python -m bridgecad", "python -m bc")


def _d09(root: Path) -> None:
    append(root, "README.md", "**Version:** 3.0 Ultimate Edition")


def _d10(root: Path) -> None:
    replace(root, "GUIDE.md", "sheet3_", "TYP_")


def _d11(root: Path) -> None:
    create(root, "CONTRIBUTING_NEW.md", "# Contributing (new)\n")


def _d12(root: Path) -> None:
    create(root, "docs/orphan.md", "# Orphan\n\nNot in the index.\n")


def _d13(root: Path) -> None:
    append(root, "docs/deployment.md", "```bash\npython scripts/ghost.py\n```")


def _d14(root: Path) -> None:
    replace(root, "docs/README.md", "DOCS_INDEX", "THEINDEX")
    replace(root, "docs/README.md", "docs system", "the thing")


def _x01(root: Path) -> None:
    append(root, "README.md", "Contact: crajkumarsingh@hotmail.com")


def _x02(root: Path) -> None:
    create(
        root,
        ".github/ISSUE_TEMPLATE/_ghost.yml",
        'name: Ghost\ndescription: x\nlabels: ["ghost-label"]\nbody: []\n',
    )


def _x03(root: Path) -> None:
    replace(root, ".lychee.toml", "include_fragments = true", "include_fragments = false")


def _guard(test_name: str) -> str:
    return f"{INTEGRITY}::{test_name}"


MUTATIONS: list[Mutation] = [
    Mutation(
        "D01",
        "phantom suite directory in a code block",
        _guard("test_defect_01_no_phantom_suite_directory"),
        _d01,
        "critical",
    ),
    Mutation(
        "D02",
        "dead relative markdown link",
        _guard("test_defect_02_every_relative_markdown_link_resolves"),
        _d02,
        "critical",
    ),
    Mutation(
        "D03",
        "missing requirements file reference",
        _guard("test_defect_03_referenced_requirements_files_exist"),
        _d03,
        "critical",
    ),
    Mutation(
        "D04",
        "support routed to a foreign repo",
        _guard("test_defect_04_no_foreign_support_urls"),
        _d04,
        "critical",
    ),
    Mutation(
        "D05",
        "placeholder release URL",
        _guard("test_defect_05_no_placeholder_release_urls"),
        _d05,
        "high",
    ),
    Mutation(
        "D06",
        "YOUR_USERNAME in a clone command",
        _guard("test_defect_06_no_your_username_placeholder"),
        _d06,
        "high",
    ),
    Mutation(
        "D07",
        "README no longer suite-first",
        _guard("test_defect_07_readme_is_suite_first"),
        _d07,
        "high",
    ),
    Mutation(
        "D08",
        "zero-install entry point undocumented",
        _guard("test_defect_08_zero_install_entry_point_documented"),
        _d08,
        "high",
    ),
    Mutation(
        "D09",
        "conflicting version claim",
        _guard("test_defect_09_no_conflicting_version_claims"),
        _d09,
        "medium",
    ),
    Mutation(
        "D10",
        "non-canonical sheet name",
        _guard("test_defect_10_sheet_names_are_canonical"),
        _d10,
        "medium",
    ),
    Mutation(
        "D11",
        "_NEW variant file reappears",
        _guard("test_defect_11_no_new_variant_files"),
        _d11,
        "medium",
    ),
    Mutation(
        "D12",
        "orphan doc missing from the index",
        _guard("test_defect_12_docs_index_lists_every_doc"),
        _d12,
        "medium",
    ),
    Mutation(
        "D13",
        "referenced script does not exist",
        _guard("test_defect_13_referenced_scripts_exist"),
        _d13,
        "low",
    ),
    Mutation(
        "D14",
        "docs/README reverts to single purpose",
        _guard("test_defect_14_docs_readme_describes_the_docs_system"),
        _d14,
        "low",
    ),
    Mutation(
        "X01",
        "PII reintroduced into a tracked doc",
        _guard("test_no_pii_in_tracked_docs"),
        _x01,
        "cross",
    ),
    Mutation(
        "X02",
        "issue template uses an undefined label",
        _guard("test_issue_template_labels_are_all_defined"),
        _x02,
        "cross",
    ),
    Mutation(
        "X03",
        "anchor checking disabled in lychee config",
        _guard("test_lychee_config_has_required_keys"),
        _x03,
        "cross",
    ),
]


# ── harness ──────────────────────────────────────────────────────────────────
def _ignore(_dir: str, names: list[str]) -> list[str]:
    return [n for n in names if n in IGNORE_DIRS or n.endswith(".egg-info")]


def _copy(dest: Path) -> Path:
    target = dest / "repo"
    shutil.copytree(ROOT, target, ignore=_ignore, symlinks=True)
    return target


# The guard runs in a deliberately bare environment on POSIX so a stray shell
# variable cannot change the verdict. Windows cannot use that: `python.exe`
# resolves its packages through USERPROFILE/APPDATA, so replacing the whole
# environment hides the user site-packages and `-m pytest` dies before it can
# report anything — which would score every mutation as "detected" for the
# wrong reason. Inherit there; keep the bare env on the CI runner.
_BARE_ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"}


def _pytest(root: Path, target: str, timeout: int = 180) -> tuple[int, str]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"} if os.name == "nt" else _BARE_ENV
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            target,
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "--tb=line",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def run_control(tmp: Path) -> tuple[bool, str]:
    """The unmutated copy must pass. Otherwise the proof is meaningless."""
    root = _copy(tmp / "control")
    code, out = _pytest(root, INTEGRITY)
    return code == 0, out


def run_one(mut: Mutation, tmp: Path) -> Mutation:
    started = time.monotonic()
    try:
        root = _copy(tmp / mut.id)
        mut.apply(root)
        code, out = _pytest(root, mut.guard)
        mut.detected = code != 0
        if mut.detected:
            mut.detail = "guard fired"
        else:
            mut.detail = "GUARD DID NOT FIRE — layer 1 has a hole here"
    except Exception as exc:
        mut.detected = False
        mut.detail = f"harness error: {type(exc).__name__}: {exc}"
    mut.ms = int((time.monotonic() - started) * 1000)
    return mut


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--skip-control", action="store_true")
    args = ap.parse_args()

    selected = MUTATIONS
    if args.only:
        wanted = {x.strip().upper() for x in args.only.split(",")}
        selected = [m for m in MUTATIONS if m.id in wanted]
        if not selected:
            print(f"no matching mutation in {sorted(wanted)}", file=sys.stderr)
            return 2

    tmp = Path(tempfile.mkdtemp(prefix="bridgecad-proof-"))
    try:
        baseline_ok, baseline_out = (True, "")
        if not args.skip_control:
            if not args.json:
                print(
                    "control: unmutated copy must pass the integrity suite ...",
                    file=sys.stderr,
                    flush=True,
                )
            baseline_ok, baseline_out = run_control(tmp)
            if not baseline_ok and not args.json:
                print("  CONTROL FAILED — results below are unreliable.\n", file=sys.stderr)

        if not args.json:
            print(
                f"running {len(selected)} mutation(s) with {args.jobs} worker(s) ...",
                file=sys.stderr,
                flush=True,
            )

        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            results = list(pool.map(lambda m: run_one(m, tmp), selected))

        detected = sum(1 for m in results if m.detected)
        total = len(results)
        undetected = [m.id for m in results if not m.detected]
        ok = baseline_ok and detected == total

        payload = {
            "control_passed": baseline_ok,
            "detected": detected,
            "total": total,
            "undetected": undetected,
            "ok": ok,
            "results": [
                {
                    "id": m.id,
                    "defect": m.what,
                    "guard": m.guard,
                    "severity": m.severity,
                    "detected": m.detected,
                    "detail": m.detail,
                    "duration_ms": m.ms,
                }
                for m in results
            ],
        }
        if not baseline_ok:
            payload["control_output"] = baseline_out[-2000:]

        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"\n  control run: {'PASS' if baseline_ok else 'FAIL'}")
            for m in results:
                mark = "DETECTED" if m.detected else "MISSED  "
                print(f"  [{mark}] {m.id}  {m.what}")
                if not m.detected:
                    print(f"            {m.detail}")
            print(f"\n  {detected}/{total} defects detectable")
            if undetected:
                print(f"  holes in layer 1: {', '.join(undetected)}")
            if not baseline_ok:
                print("  CONTROL FAILED — fix the integrity suite first")
            print("  PROOF PASSED" if ok else "  PROOF FAILED")

        return 0 if ok else 1
    finally:
        if args.keep:
            print(f"\n  kept: {tmp}", file=sys.stderr)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
