"""
Centralized MongoDB connection management using PyMongo.
Provides safe client instantiation, database access, and health checks.
"""

import logging
from typing import Optional, Tuple
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import config

logger = logging.getLogger("intellitrack.database")

_mongo_client: Optional[MongoClient] = None


def get_client(uri: Optional[str] = None) -> MongoClient:
    """
    Get or create a singleton MongoClient instance.
    """
    global _mongo_client
    target_uri = uri or config.MONGODB_URI
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(
                target_uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=5000,
            )
        except Exception as e:
            logger.error(f"Failed to initialize MongoClient: {e}")
            raise
    return _mongo_client


def get_database(db_name: Optional[str] = None, uri: Optional[str] = None) -> Database:
    """
    Return the specified database or default from config.
    """
    client = get_client(uri)
    target_db_name = db_name or config.MONGODB_DATABASE
    return client[target_db_name]


def check_connection(uri: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify connectivity to MongoDB.
    Returns (True, "Connected successfully") or (False, error_message).
    """
    try:
        client = get_client(uri)
        # The ping command is cheap and does not require auth on admin in local setups
        client.admin.command("ping")
        server_info = client.server_info()
        version = server_info.get("version", "unknown")
        return True, f"MongoDB connection active (v{version})"
    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        logger.warning(f"MongoDB connection failed: {err}")
        return False, "Could not connect to MongoDB server. Please ensure the MongoDB service is running."
    except Exception as err:
        logger.error(f"Unexpected MongoDB error: {err}")
        return False, f"Database error: {str(err)}"


def close_connection() -> None:
    """Close active client connection."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        logger.info("MongoDB connection closed.")
