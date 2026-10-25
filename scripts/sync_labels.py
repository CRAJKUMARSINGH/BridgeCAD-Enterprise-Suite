#!/usr/bin/env python3
"""Create or update every label the repo references. Idempotent.

Issue-template front-matter labels are silently dropped if the label does not
exist, so this must run once on a fresh repo and after any label change.

Requires: gh CLI, authenticated. Run with --dry-run to preview.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

# (name, colour, description)
LABELS = [
    # type
    ("bug", "d73a4a", "Something is broken or produces wrong output"),
    ("enhancement", "a2eeef", "New capability or improvement"),
    ("documentation", "0075ca", "Docs only"),
    ("question", "d876e3", "Usage question"),
    ("chore", "ededed", "Build, CI, dependency or housekeeping"),
    # routing
    ("support", "0e8a16", "Needs a maintainer answer"),
    ("rks-legal", "14b8a6", "Professional services / legal enquiry"),
    ("plugin-request", "a855f7", "New bridge type request"),
    ("standards-discrepancy", "f59e0b", "Output disagrees with an IRC / MORTH clause"),
    # area
    ("area:core", "c5def5", "bridgecad-core — models, geometry, validation"),
    ("area:io", "c5def5", "bridgecad-io — Excel, CSV, JSON"),
    ("area:draw", "c5def5", "bridgecad-draw — DXF, sheets, layers"),
    ("area:bill", "c5def5", "bridgecad-bill — BOQ, rates"),
    ("area:qa", "c5def5", "bridgecad-qa — rules, compliance"),
    ("area:export", "c5def5", "bridgecad-export — bundle, manifest"),
    ("area:plugins", "c5def5", "bridgecad-plugins"),
    ("area:ai", "c5def5", "bridgecad-ai"),
    ("area:infra", "c5def5", "bridgecad-infra — db, cache, auth"),
    ("area:cli", "c5def5", "CLI"),
    ("area:api", "c5def5", "FastAPI gateway"),
    ("area:ui", "c5def5", "Streamlit or React console"),
    ("area:docs", "c5def5", "Documentation"),
    ("area:ci", "c5def5", "CI / workflows"),
    # status
    ("status:needs-repro", "fbca04", "Waiting on a reproduction"),
    ("status:needs-engineer-review", "fbca04", "Requires an engineer to judge"),
    ("status:blocked", "b60205", "Blocked on something else"),
    ("status:confirmed", "0e8a16", "Reproduced and accepted"),
    # priority
    ("priority:critical", "b60205", "Unsafe or non-compliant output"),
    ("priority:high", "d93f0b", "Wrong output, workaround exists"),
    ("priority:medium", "fbca04", "Normal"),
    ("priority:low", "c2e0c6", "Nice to have"),
    # contribution
    ("good-first-issue", "7057ff", "Good entry point for a new contributor"),
    ("help-wanted", "008672", "Extra attention welcome"),
    ("breaking-change", "e11d48", "Changes workbook schema or output shape"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    failures = 0
    for name, colour, desc in LABELS:
        cmd = ["gh", "label", "create", name, "--color", colour, "--description", desc, "--force"]
        if args.dry_run:
            print(f"  would sync: {name}")
            continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  FAIL {name}: {r.stderr.strip()}", file=sys.stderr)
            failures += 1
        else:
            print(f"  synced {name}")

    print(f"\n{len(LABELS) - failures}/{len(LABELS)} labels synced.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
