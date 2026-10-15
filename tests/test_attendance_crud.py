"""
Integration tests for Attendance CRUD and duplicate prevention.
"""

import pytest
from services.attendance_service import AttendanceService
from services.student_service import StudentService
from services.subject_service import SubjectService


@pytest.fixture
def setup_student_and_subject(test_db):
    StudentService.create_student({
        "student_id": "STU6001",
        "name": "Manish Sharma",
        "email": "manish@test.edu",
        "class_name": "BTech-CSE-A",
        "enrollment_date": "2026-08-01"
    }, db=test_db)

    SubjectService.create_subject({
        "subject_code": "CS601",
        "subject_name": "Software Engineering",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    }, db=test_db)

    return "STU6001", "CS601"


def test_attendance_creation_and_duplicate_prevention(test_db, setup_student_and_subject):
    """Test recording attendance and preventing duplicate entries on the same date."""
    stu_id, sub_code = setup_student_and_subject
    att_date = "2026-09-15"

    payload = {
        "student_id": stu_id,
        "subject_code": sub_code,
        "attendance_date": att_date,
        "status": "Present",
        "remarks": "On time"
    }

    # 1. First insert should succeed
    success1, _, created = AttendanceService.create_attendance(payload, db=test_db)
    assert success1 is True
    assert created["status"] == "Present"

    # 2. Duplicate insert for same student + subject + date must fail
    payload_dup = {
        "student_id": stu_id,
        "subject_code": sub_code,
        "attendance_date": att_date,
        "status": "Late"
    }
    success2, msg2, _ = AttendanceService.create_attendance(payload_dup, db=test_db)
    assert success2 is False
    assert "Duplicate" in msg2


def test_update_and_delete_attendance(test_db, setup_student_and_subject):
    """Test modifying attendance status and deleting entry."""
    stu_id, sub_code = setup_student_and_subject
    att_date = "2026-09-16"

    AttendanceService.create_attendance({
        "student_id": stu_id,
        "subject_code": sub_code,
        "attendance_date": att_date,
        "status": "Absent"
    }, db=test_db)

    # Update to Present
    success_up, _, updated = AttendanceService.update_attendance(stu_id, sub_code, att_date, {"status": "Present"}, db=test_db)
    assert success_up is True
    assert updated["status"] == "Present"

    # Delete
    success_del, _ = AttendanceService.delete_attendance(stu_id, sub_code, att_date, db=test_db)
    assert success_del is True
