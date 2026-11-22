"""bridgecad_ai.drawing_review — review a drawing sheet against project requirements.

Two layers:
  1. Deterministic rule checks on facts read from the DXF (always run, offline).
  2. Optional AI review through the Lovable AI Gateway (``LOVABLE_API_KEY``),
     which looks for omissions/inconsistencies the rules cannot express and
     returns extra checklist items. AI items are marked ``source="ai"`` and are
     advisory — they never override a rule result.

CLI:  python -m bridgecad_ai.drawing_review SHEET.dxf REQUIREMENTS.json [--ai]
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

GATEWAY_URL = "https://ai.gateway.lovable.dev/v1/responses"
DEFAULT_MODEL = "openai/gpt-6-astra"
_SCALE_RE = re.compile(r"1\s*:\s*(\d+)")


@dataclass
class CheckItem:
    id: str
    title: str
    status: str  # "pass" | "fail" | "warn"
    detail: str = ""
    severity: str = "major"  # "critical" | "major" | "minor"
    source: str = "rule"


@dataclass
class DrawingFacts:
    layers: list[str]
    texts: list[str]
    dimension_count: int
    hard_text_dimensions: int
    dimension_values: list[float]
    entity_counts: dict[str, int]
    scales: list[int] = field(default_factory=list)


def extract_facts(dxf_path: str | Path) -> DrawingFacts:
    import ezdxf

    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    counts: dict[str, int] = {}
    texts: list[str] = []
    dims = list(msp.query("DIMENSION"))
    for e in msp:
        counts[e.dxftype()] = counts.get(e.dxftype(), 0) + 1
        if e.dxftype() == "TEXT":
            texts.append(e.dxf.text)
        elif e.dxftype() == "MTEXT":
            texts.append(e.plain_text())
    hard = sum(1 for d in dims if (d.dxf.get("text", "<>") or "<>") not in ("<>", ""))
    values: list[float] = []
    for d in dims:
        try:
            values.append(round(float(d.get_measurement()), 3))
        except Exception:
            pass
    scales = sorted({int(m.group(1)) for t in texts for m in _SCALE_RE.finditer(t)})
    layers = sorted({e.dxf.layer for e in msp})
    return DrawingFacts(layers, texts, len(dims), hard, values, counts, scales)


def rule_checks(facts: DrawingFacts, req: dict[str, Any]) -> list[CheckItem]:
    items: list[CheckItem] = []
    blob = "\n".join(facts.texts).upper()

    def add(i, title, ok, detail, sev="major", warn=False):
        items.append(CheckItem(i, title, "pass" if ok else ("warn" if warn else "fail"), detail, sev))

    add("R01", "Sheet carries dimensions", facts.dimension_count > 0,
        f"{facts.dimension_count} DIMENSION entities", "critical")
    if facts.dimension_count:
        add("R02", "Dimensions are measured (not hard-typed text)",
            facts.hard_text_dimensions == 0,
            f"{facts.hard_text_dimensions}/{facts.dimension_count} carry text overrides",
            "minor", warn=True)
    if req.get("scale"):
        want = int(_SCALE_RE.search(str(req["scale"])).group(1)) if _SCALE_RE.search(str(req["scale"])) else None
        add("R03", "Stated scale matches requirement", want in facts.scales,
            f"required 1:{want}, found {['1:%d' % s for s in facts.scales] or 'none'}")
        if len(facts.scales) > 1:
            add("R04", "Single consistent scale caption", False,
                f"multiple scales captioned: {facts.scales}", "minor", warn=True)
    for key, label in (("drawing_no", "Drawing number"), ("bridge_name", "Bridge name"),
                       ("project_title", "Project title")):
        if req.get(key):
            add(f"R1{len(items)}", f"{label} in title block", str(req[key]).upper() in blob,
                f"expected '{req[key]}'")
    for note in req.get("required_notes", []):
        add(f"N{len(items)}", f"Note present: {note}", note.upper() in blob, "", "major")
    for layer in req.get("required_layers", []):
        add(f"L{len(items)}", f"Layer present: {layer}", layer in facts.layers, "", "minor")
    for name, value in (req.get("key_dimensions_m") or {}).items():
        sc = req.get("scale_denom") or 1
        want_paper = float(value) * 1000.0 / float(sc)
        hit = any(abs(v - want_paper) <= max(0.5, want_paper * 0.01) for v in facts.dimension_values)
        add(f"D{len(items)}", f"Dimension shown: {name} = {value} m", hit,
            "no DIMENSION measures this value" if not hit else "", "major")
    return items


def _ai_prompt(facts: DrawingFacts, req: dict[str, Any], rules: list[CheckItem]) -> str:
    return (
        "You are a senior bridge drawing checker (IRC/MORTH practice). Using the "
        "extracted drawing facts and project requirements, list likely omissions or "
        "inconsistencies NOT already covered by the rule results. Be specific; do not "
        "invent facts that are not supported by the data.\n\n"
        f"REQUIREMENTS:\n{json.dumps(req, indent=1)}\n\n"
        f"FACTS:\n{json.dumps({**asdict(facts), 'texts': facts.texts[:300]}, indent=1)}\n\n"
        f"RULE RESULTS:\n{json.dumps([asdict(r) for r in rules], indent=1)}"
    )


_AI_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["title", "detail", "severity"],
        "properties": {
            "title": {"type": "string"}, "detail": {"type": "string"},
            "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
        }}}},
}


class AIReviewError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"AI review failed ({status}): {message}")
        self.status = status


def ai_checks(facts, req, rules, api_key: str | None = None, model: str = DEFAULT_MODEL,
              opener=urllib.request.urlopen) -> list[CheckItem]:
    """Streamed Responses call; returns advisory items. Raises AIReviewError."""
    key = api_key or os.environ.get("LOVABLE_API_KEY")
    if not key:
        raise AIReviewError(401, "LOVABLE_API_KEY is not set")
    body = {
        "model": model, "stream": True, "store": False,
        "reasoning": {"effort": "low"},
        "input": _ai_prompt(facts, req, rules),
        "text": {"format": {"type": "json_schema", "name": "review", "strict": True, "schema": _AI_SCHEMA}},
    }
    r = urllib.request.Request(GATEWAY_URL, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json", "Lovable-API-Key": key,
        "Authorization": f"Bearer {key}", "X-Lovable-AIG-SDK": "fetch",
    })
    out = []
    try:
        with opener(r) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                ev = json.loads(line[5:].strip() or "{}")
                if ev.get("type") == "response.output_text.delta":
                    out.append(ev.get("delta", ""))
                elif ev.get("type") in ("response.failed", "error"):
                    raise AIReviewError(500, json.dumps(ev)[:300])
    except urllib.error.HTTPError as e:  # 402/403/429 etc: surface, never retry here
        try:
            msg = json.loads(e.read()).get("message") or e.reason
        except Exception:
            msg = e.reason
        raise AIReviewError(e.code, str(msg)) from None
    text = "".join(out).strip()
    if not text:
        raise AIReviewError(200, "model returned no review (possible refusal)")
    data = json.loads(text)
    return [CheckItem(f"AI{i + 1}", it["title"], "warn", it["detail"], it["severity"], "ai")
            for i, it in enumerate(data.get("items", []))]


def review(dxf_path, requirements: dict[str, Any], use_ai: bool = False, **ai_kw) -> list[CheckItem]:
    facts = extract_facts(dxf_path)
    items = rule_checks(facts, requirements)
    if use_ai:
        try:
            items += ai_checks(facts, requirements, items, **ai_kw)
        except AIReviewError as e:
            items.append(CheckItem("AI0", "AI review unavailable", "warn", str(e), "minor", "ai"))
    return items


def to_markdown(items: list[CheckItem]) -> str:
    mark = {"pass": "[x]", "fail": "[ ]", "warn": "[!]"}
    rows = [f"- {mark[i.status]} **{i.id}** {i.title} — _{i.severity}_"
            + (f" — {i.detail}" if i.detail else "") + (" (AI)" if i.source == "ai" else "")
            for i in items]
    fails = sum(i.status == "fail" for i in items)
    return f"# Drawing review checklist\n\n{fails} failing of {len(items)} checks\n\n" + "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    use_ai = "--ai" in a
    a = [x for x in a if x != "--ai"]
    if len(a) != 2:
        print(__doc__)
        return 2
    items = review(a[0], json.loads(Path(a[1]).read_text()), use_ai=use_ai)
    print(to_markdown(items))
    return 1 if any(i.status == "fail" for i in items) else 0


if __name__ == "__main__":
    raise SystemExit(main())
