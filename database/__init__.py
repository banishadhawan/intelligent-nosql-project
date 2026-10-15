"""
Database layer for IntelliTrack.
Manages MongoDB connections, index creation, and collection validation.
"""

from .connection import get_database, get_client, check_connection
from .indexes import create_all_indexes
from .validators import apply_collection_validators

__all__ = [
    "get_database",
    "get_client",
    "check_connection",
    "create_all_indexes",
    "apply_collection_validators",
]
