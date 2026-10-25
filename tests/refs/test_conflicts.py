"""Wing-20 — where a reference disagrees with the implementation.

A conflict is a finding, not a failure. These tests do not fail on an open
conflict; they fail on a conflict that was closed without a note.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.refs


def test_open_conflicts_are_counted():
    from bridgecad_refs.conflicts import open_conflicts
    open_ = open_conflicts()
    print(f"\n  {len(open_)} open reference conflict(s)")
    for c in open_:
        print(f"    {c.key}: generated {c.generated} vs stated {c.stated} ({c.citation_ref})")


def test_resolved_conflicts_carry_a_note():
    from bridgecad_refs.conflicts import open_conflicts
    for c in open_conflicts():
        if c.resolved_as:
            assert c.note and len(c.note) > 10, f"{c.key}: closed with no explanation"
