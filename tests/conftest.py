"""
Pytest configuration and isolated MongoDB test fixtures.
Automated tests operate against an isolated 'intellitrack_test' database,
strictly preventing any deletion or mutation of development data.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.connection import get_database, check_connection
from database.indexes import create_all_indexes
from database.validators import apply_collection_validators
from config import config

TEST_DB_NAME = config.TEST_DATABASE


@pytest.fixture(scope="session")
def is_mongo_available():
    """Verify that MongoDB is running locally before executing integration tests."""
    available, msg = check_connection()
    return available


@pytest.fixture(scope="function")
def test_db(is_mongo_available):
    """
    Provides an isolated test database with indexes and validators applied.
    Cleans all collections before and after each test function.
    """
    if not is_mongo_available:
        pytest.skip("MongoDB server is not reachable; skipping integration test.")

    db = get_database(TEST_DB_NAME)

    # Clean before test
    db[config.COLLECTION_STUDENTS].delete_many({})
    db[config.COLLECTION_SUBJECTS].delete_many({})
    db[config.COLLECTION_ASSESSMENTS].delete_many({})
    db[config.COLLECTION_ATTENDANCE].delete_many({})

    # Apply indexes and validators
    apply_collection_validators(db)
    create_all_indexes(db)

    yield db

    # Clean after test
    db[config.COLLECTION_STUDENTS].delete_many({})
    db[config.COLLECTION_SUBJECTS].delete_many({})
    db[config.COLLECTION_ASSESSMENTS].delete_many({})
    db[config.COLLECTION_ATTENDANCE].delete_many({})
