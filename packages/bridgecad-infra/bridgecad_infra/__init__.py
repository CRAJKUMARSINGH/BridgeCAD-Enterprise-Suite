"""bridgecad_infra — Infrastructure layer (M8): DB, cache, auth, logging."""
from .db           import get_session, create_all_tables, engine
from .repositories import ProjectRepo, BridgeRepo, HistoryRepo
from .cache        import LRUCache, get_qa_cache, get_boq_cache
from .auth         import ApiKey, verify_api_key, require_role, generate_api_key
from .logging_setup import configure as configure_logging, get_logger

__version__ = "0.1.0-rc1"
__all__ = [
    "get_session", "create_all_tables", "engine",
    "ProjectRepo", "BridgeRepo", "HistoryRepo",
    "LRUCache", "get_qa_cache", "get_boq_cache",
    "ApiKey", "verify_api_key", "require_role", "generate_api_key",
    "configure_logging", "get_logger",
]
