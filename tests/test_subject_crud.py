"""
Integration tests for Subject CRUD operations on isolated MongoDB test database.
"""

import pytest
from services.subject_service import SubjectService
from config import config


def test_create_and_get_subject(test_db):
    """Test successful subject insertion and lookup."""
    payload = {
        "subject_code": "CS901",
        "subject_name": "Cloud Native Architecture",
        "description": "Microservices, containers, and Kubernetes",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    }
    success, msg, created = SubjectService.create_subject(payload, db=test_db)
    assert success is True
    assert created["subject_code"] == "CS901"

    retrieved = SubjectService.get_subject_by_code("CS901", db=test_db)
    assert retrieved is not None
    assert retrieved["subject_name"] == "Cloud Native Architecture"
    assert retrieved["credits"] == 4


def test_duplicate_subject_code_prevention(test_db):
    """Test unique constraint on subject_code."""
    payload = {
        "subject_code": "CS902",
        "subject_name": "Original Subject",
        "credits": 3,
        "class_name": "BTech-CSE-A"
    }
    SubjectService.create_subject(payload, db=test_db)

    # Duplicate code
    payload_dup = {
        "subject_code": "CS902",
        "subject_name": "Duplicate Subject",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    }
    success, msg, _ = SubjectService.create_subject(payload_dup, db=test_db)
    assert success is False
    assert "already exists" in msg


def test_safe_subject_deletion_prevention(test_db):
    """Test that subjects referenced by assessments cannot be deleted unless forced."""
    SubjectService.create_subject({
        "subject_code": "CS903",
        "subject_name": "Database Systems",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    }, db=test_db)

    # Insert dependent assessment
    test_db[config.COLLECTION_ASSESSMENTS].insert_one({
        "assessment_id": "ASM9031",
        "student_id": "STU1001",
        "subject_code": "CS903",
        "assessment_name": "Midterm Exam",
        "assessment_type": "Midterm",
        "marks": 20,
        "max_marks": 25,
        "assessment_date": "2026-09-10"
    })

    # Default deletion should be blocked
    success, msg = SubjectService.delete_subject("CS903", cascade=False, db=test_db)
    assert success is False
    assert "Cannot delete subject" in msg

    # Forced cascade deletion succeeds
    success_casc, _ = SubjectService.delete_subject("CS903", cascade=True, db=test_db)
    assert success_casc is True
    assert test_db[config.COLLECTION_SUBJECTS].find_one({"subject_code": "CS903"}) is None
