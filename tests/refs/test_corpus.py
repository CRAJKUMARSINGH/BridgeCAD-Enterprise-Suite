"""Wing-20 — the corpus's own integrity.

A reference you cannot prove the provenance of is an anecdote. Hashes and a
commit SHA make the corpus reproducible: someone else can fetch the same bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.refs

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "references"
INDEX = json.loads((REF / "index.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def test_every_raw_file_is_indexed():
    on_disk = {p.relative_to(REF).as_posix() for p in (REF / "raw").rglob("*") if p.is_file()}
    indexed = {r["path"] for r in INDEX["references"]}
    assert on_disk == indexed, f"unindexed: {on_disk - indexed} / missing: {indexed - on_disk}"


def test_indexed_files_match_their_hash():
    for r in INDEX["references"]:
        path = REF / r["path"]
        assert path.exists(), r["path"]
        assert sha256(path) == r["sha256"], (
            f"{r['path']}: hash drifted — the reference changed under the corpus"
        )


def test_every_reference_records_provenance():
    for r in INDEX["references"]:
        assert r["repo"], f"{r['id']}: no source repo"
        assert r["commit"], f"{r['id']}: no commit — provenance is unverifiable"
        assert r["fetched_on"], r["id"]
        assert r["sheet_type"], f"{r['id']}: unknown sheet type"


def test_reference_ids_are_unique():
    ids = [r["id"] for r in INDEX["references"]]
    assert len(ids) == len(set(ids))


def test_declared_pages_match_reality():
    for r in INDEX["references"]:
        if r["path"].endswith(".pdf"):
            import pypdf
            assert len(pypdf.PdfReader(REF / r["path"]).pages) == r["pages"], r["id"]


def test_every_reference_is_used_by_something():
    """An unreferenced file is corpus bloat — or a missing expectation."""
    used = set()
    for f in (REF / "expected").glob("*.json"):          # now per bridge, same schema
        for item in json.loads(f.read_text(encoding="utf-8"))["values"]:
            used.add(item["citation"]["ref"])
    for f in (REF / "cases").glob("*.json"):
        used.update(json.loads(f.read_text(encoding="utf-8"))["source_sheets"])
    orphans = {r["id"] for r in INDEX["references"]} - used
    assert not orphans, f"references with no expectations citing them: {sorted(orphans)}"


def test_every_reference_belongs_to_a_set_and_bridge():
    """Provenance at the set level, not just the file level. Two files from the
    same GAD set are one bridge; two files from different sets are not, and the
    difference matters when values disagree."""
    for r in INDEX["references"]:
        assert r.get("set_id"), f"{r['id']}: no set"
        assert r.get("bridge_id"), f"{r['id']}: no bridge"
        assert r.get("licence"), f"{r['id']}: no licence note"
    sets = {r["set_id"] for r in INDEX["references"]}
    for s in sets:
        assert len({r["bridge_id"] for r in INDEX["references"] if r["set_id"] == s}) == 1, (
            f"set {s} claims more than one bridge — or the set/bridge split is wrong"
        )
