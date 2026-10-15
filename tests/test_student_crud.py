"""
Integration tests for Student CRUD operations on isolated MongoDB test database.
"""

import pytest
from services.student_service import StudentService
from config import config


def test_create_and_get_student(test_db):
    """Test successful student insertion and retrieval."""
    payload = {
        "student_id": "STU8001",
        "name": "Kavya Nair",
        "email": "kavya.nair@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01",
        "skills": ["Python", "SQL"]
    }
    success, msg, created = StudentService.create_student(payload, db=test_db)
    assert success is True
    assert created["student_id"] == "STU8001"

    # Read back
    retrieved = StudentService.get_student_by_id("STU8001", db=test_db)
    assert retrieved is not None
    assert retrieved["name"] == "Kavya Nair"
    assert retrieved["email"] == "kavya.nair@test.edu"


def test_duplicate_student_id_prevention(test_db):
    """Test that duplicate student_id is rejected by unique index."""
    payload = {
        "student_id": "STU8002",
        "name": "Original Student",
        "email": "original@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01"
    }
    success1, _, _ = StudentService.create_student(payload, db=test_db)
    assert success1 is True

    # Duplicate ID with different email
    payload_dup = {
        "student_id": "STU8002",
        "name": "Duplicate Student",
        "email": "dup@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01"
    }
    success2, msg2, _ = StudentService.create_student(payload_dup, db=test_db)
    assert success2 is False
    assert "already exists" in msg2


def test_update_student(test_db):
    """Test updating student details."""
    payload = {
        "student_id": "STU8003",
        "name": "Vikas Rao",
        "email": "vikas@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01"
    }
    StudentService.create_student(payload, db=test_db)

    # Update class and name
    update_data = {
        "name": "Vikas K. Rao",
        "class_name": "BTech-CSE-B"
    }
    success, msg, updated = StudentService.update_student("STU8003", update_data, db=test_db)
    assert success is True
    assert updated["name"] == "Vikas K. Rao"
    assert updated["class_name"] == "BTech-CSE-B"


def test_delete_student_cascade(test_db):
    """Test safe cascade deletion of student and their related records."""
    # 1. Create student
    StudentService.create_student({
        "student_id": "STU8004",
        "name": "Tarun Kapoor",
        "email": "tarun@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01"
    }, db=test_db)

    # 2. Insert dummy assessment and attendance for this student
    test_db[config.COLLECTION_ASSESSMENTS].insert_one({
        "assessment_id": "ASM8001",
        "student_id": "STU8004",
        "subject_code": "CS301",
        "assessment_name": "Quiz 1",
        "assessment_type": "Quiz",
        "marks": 20,
        "max_marks": 25,
        "assessment_date": "2026-09-01"
    })
    test_db[config.COLLECTION_ATTENDANCE].insert_one({
        "student_id": "STU8004",
        "subject_code": "CS301",
        "attendance_date": "2026-09-01",
        "status": "Present"
    })

    # Test non-cascade rejection
    success_no_casc, msg_no = StudentService.delete_student("STU8004", cascade=False, db=test_db)
    assert success_no_casc is False
    assert "Cannot delete" in msg_no

    # Test cascade deletion
    success_casc, msg_casc = StudentService.delete_student("STU8004", cascade=True, db=test_db)
    assert success_casc is True
    assert test_db[config.COLLECTION_STUDENTS].find_one({"student_id": "STU8004"}) is None
    assert test_db[config.COLLECTION_ASSESSMENTS].find_one({"student_id": "STU8004"}) is None
    assert test_db[config.COLLECTION_ATTENDANCE].find_one({"student_id": "STU8004"}) is None
