"""
Integration tests for Assessment CRUD and referential validation.
"""

import pytest
from services.assessment_service import AssessmentService
from services.student_service import StudentService
from services.subject_service import SubjectService
from config import config


@pytest.fixture
def setup_student_and_subject(test_db):
    """Seed one student and one subject in test_db."""
    StudentService.create_student({
        "student_id": "STU7001",
        "name": "Isha Saxena",
        "email": "isha@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01"
    }, db=test_db)

    SubjectService.create_subject({
        "subject_code": "CS701",
        "subject_name": "Distributed Systems",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    }, db=test_db)

    return "STU7001", "CS701"


def test_assessment_nonexistent_student(test_db, setup_student_and_subject):
    """Verify assessment fails if student does not exist."""
    _, sub_code = setup_student_and_subject
    payload = {
        "assessment_id": "ASM7001",
        "student_id": "STU_NONEXISTENT",
        "subject_code": sub_code,
        "assessment_name": "Quiz 1",
        "assessment_type": "Quiz",
        "marks": 20.0,
        "max_marks": 25.0,
        "assessment_date": "2026-09-10"
    }
    success, msg, _ = AssessmentService.create_assessment(payload, db=test_db)
    assert success is False
    assert "Referential error: Student" in msg


def test_assessment_nonexistent_subject(test_db, setup_student_and_subject):
    """Verify assessment fails if subject does not exist."""
    stu_id, _ = setup_student_and_subject
    payload = {
        "assessment_id": "ASM7002",
        "student_id": stu_id,
        "subject_code": "SUB_INVALID",
        "assessment_name": "Quiz 1",
        "assessment_type": "Quiz",
        "marks": 20.0,
        "max_marks": 25.0,
        "assessment_date": "2026-09-10"
    }
    success, msg, _ = AssessmentService.create_assessment(payload, db=test_db)
    assert success is False
    assert "Referential error: Subject" in msg


def test_create_and_update_assessment(test_db, setup_student_and_subject):
    """Verify successful assessment creation and percentage recalculation on update."""
    stu_id, sub_code = setup_student_and_subject
    payload = {
        "assessment_id": "ASM7003",
        "student_id": stu_id,
        "subject_code": sub_code,
        "assessment_name": "Midterm Exam",
        "assessment_type": "Midterm",
        "marks": 36.0,
        "max_marks": 40.0,
        "assessment_date": "2026-10-01"
    }
    success, _, created = AssessmentService.create_assessment(payload, db=test_db)
    assert success is True
    assert created["percentage"] == 90.0

    # Update marks to 20/40 (50%)
    success_up, _, updated = AssessmentService.update_assessment("ASM7003", {"marks": 20.0}, db=test_db)
    assert success_up is True
    assert updated["marks"] == 20.0
    assert updated["percentage"] == 50.0
