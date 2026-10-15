"""
Unit tests for domain validation layers (Pydantic models).
Tests required fields, data types, email formats, credit bounds,
marks limits, and attendance status enumerations.
"""

import pytest
from models.student import StudentCreateModel
from models.subject import SubjectCreateModel
from models.assessment import AssessmentCreateModel
from models.attendance import AttendanceCreateModel


def test_valid_student_model():
    """Verify that a properly formed student dictionary passes validation."""
    data = {
        "student_id": "STU9901",
        "name": "Arjun Das",
        "email": "arjun.das@example.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01",
        "skills": ["Python", "MongoDB"]
    }
    model = StudentCreateModel(**data)
    assert model.student_id == "STU9901"
    assert model.name == "Arjun Das"
    assert model.email == "arjun.das@example.edu"
    assert "Python" in model.skills


def test_student_missing_required_fields():
    """Verify that omitting required fields raises a validation error."""
    with pytest.raises(Exception):
        # Missing email and class_name
        StudentCreateModel(student_id="STU9902", name="Incomplete Student")


def test_student_invalid_email():
    """Verify that an invalid email string is rejected."""
    with pytest.raises(ValueError, match="Invalid email format"):
        StudentCreateModel(
            student_id="STU9903",
            name="Test User",
            email="not-a-valid-email",
            class_name="BTech-CSE-A",
            enrollment_date="2026-08-01"
        )


def test_subject_credit_limits():
    """Verify that credits must be between 1 and 10."""
    with pytest.raises(Exception):
        # 0 credits is invalid
        SubjectCreateModel(
            subject_code="CS999",
            subject_name="Zero Credit Subject",
            credits=0,
            class_name="BTech-CSE-A"
        )

    with pytest.raises(Exception):
        # 15 credits exceeds max of 10
        SubjectCreateModel(
            subject_code="CS999",
            subject_name="Excessive Credit Subject",
            credits=15,
            class_name="BTech-CSE-A"
        )


def test_assessment_marks_exceeding_max_marks():
    """Verify that marks obtained cannot exceed maximum marks."""
    with pytest.raises(ValueError, match="cannot exceed maximum marks"):
        AssessmentCreateModel(
            assessment_id="ASM9901",
            student_id="STU1001",
            subject_code="CS301",
            assessment_name="Midterm",
            assessment_type="Midterm",
            marks=55.0,
            max_marks=50.0,
            assessment_date="2026-09-10"
        )


def test_assessment_negative_marks():
    """Verify that negative marks are rejected."""
    with pytest.raises(Exception):
        AssessmentCreateModel(
            assessment_id="ASM9902",
            student_id="STU1001",
            subject_code="CS301",
            assessment_name="Quiz 1",
            assessment_type="Quiz",
            marks=-5.0,
            max_marks=25.0,
            assessment_date="2026-09-10"
        )


def test_assessment_percentage_property():
    """Verify percentage calculation across different maximum marks."""
    asm1 = AssessmentCreateModel(
        assessment_id="ASM9903",
        student_id="STU1001",
        subject_code="CS301",
        assessment_name="Quiz",
        assessment_type="Quiz",
        marks=18.0,
        max_marks=25.0,
        assessment_date="2026-09-10"
    )
    assert asm1.percentage == 72.0

    asm2 = AssessmentCreateModel(
        assessment_id="ASM9904",
        student_id="STU1001",
        subject_code="CS301",
        assessment_name="Final",
        assessment_type="Final Exam",
        marks=45.0,
        max_marks=50.0,
        assessment_date="2026-09-10"
    )
    assert asm2.percentage == 90.0


def test_invalid_attendance_status():
    """Verify that attendance status only accepts Present, Absent, or Late."""
    with pytest.raises(ValueError, match="is invalid. Allowed values: Present, Absent, Late"):
        AttendanceCreateModel(
            student_id="STU1001",
            subject_code="CS301",
            attendance_date="2026-09-10",
            status="Excused"
        )
