"""bridgecad_infra — Infrastructure layer (M8): DB, cache, auth, logging."""
from .auth import ApiKey, generate_api_key, require_role, verify_api_key
from .cache import LRUCache, get_boq_cache, get_qa_cache
from .db import create_all_tables, engine, get_session
from .logging_setup import configure as configure_logging
from .logging_setup import get_logger
from .repositories import BridgeRepo, HistoryRepo, ProjectRepo

__version__ = "0.1.0-rc1"
__all__ = [
    "get_session", "create_all_tables", "engine",
    "ProjectRepo", "BridgeRepo", "HistoryRepo",
    "LRUCache", "get_qa_cache", "get_boq_cache",
    "ApiKey", "verify_api_key", "require_role", "generate_api_key",
    "configure_logging", "get_logger",
]
