"""bridgecad_qa — QA compliance engine (M6)."""
from .rules_engine import run_qa
from .compliance   import ComplianceScore, score
from .reports      import generate_html_report
__version__ = "0.1.0-rc1"
__all__ = ["run_qa", "ComplianceScore", "score", "generate_html_report"]
