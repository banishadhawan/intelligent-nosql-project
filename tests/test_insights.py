"""
Integration tests for Intelligent Learning Insights and rule-based recommendation logic.
"""

import pytest
from services.insights_service import InsightsService
from services.student_service import StudentService
from services.subject_service import SubjectService
from services.assessment_service import AssessmentService
from services.attendance_service import AttendanceService
from scripts.seed_data import seed_database


def test_at_risk_detection_with_known_records(test_db):
    """Verify that at-risk students are flagged with transparent empirical justifications."""
    StudentService.create_student({
        "student_id": "STU_RISK",
        "name": "Underperforming Student",
        "email": "risk@test.edu",
        "class_name": "Class-A",
        "enrollment_date": "2026-08-01"
    }, db=test_db)

    SubjectService.create_subject({
        "subject_code": "CS101",
        "subject_name": "Intro to Computing",
        "credits": 4,
        "class_name": "Class-A"
    }, db=test_db)

    # 1. Low marks: 15 / 50 = 30.0% (< 50% threshold)
    AssessmentService.create_assessment({
        "assessment_id": "ASM_R1",
        "student_id": "STU_RISK",
        "subject_code": "CS101",
        "assessment_name": "Quiz",
        "assessment_type": "Quiz",
        "marks": 15.0,
        "max_marks": 50.0,
        "assessment_date": "2026-09-01"
    }, db=test_db)

    # 2. Low attendance: 2 Absent out of 2 = 0.0% (< 75% threshold)
    AttendanceService.create_attendance({
        "student_id": "STU_RISK",
        "subject_code": "CS101",
        "attendance_date": "2026-09-01",
        "status": "Absent"
    }, db=test_db)
    AttendanceService.create_attendance({
        "student_id": "STU_RISK",
        "subject_code": "CS101",
        "attendance_date": "2026-09-02",
        "status": "Absent"
    }, db=test_db)

    at_risk = InsightsService.get_at_risk_students(low_perf_threshold=50.0, low_att_threshold=75.0, db=test_db)
    assert len(at_risk) == 1
    flagged = at_risk[0]
    assert flagged["student_id"] == "STU_RISK"
    assert flagged["risk_tier"] == "Critical Risk"

    # Verify transparent evidence in reasons list
    assert any("Low Academic Performance" in r for r in flagged["reasons"])
    assert any("Low Class Attendance" in r for r in flagged["reasons"])


def test_performance_trend_detection(test_db):
    """
    Test chronological trend analysis:
    - Declining student with >= 3 assessments has trend detected
    - Student with < 3 assessments reports insufficient data
    """
    StudentService.create_student({
        "student_id": "STU_TREND",
        "name": "Declining Student",
        "email": "trend@test.edu",
        "class_name": "Class-A",
        "enrollment_date": "2026-08-01"
    }, db=test_db)

    SubjectService.create_subject({
        "subject_code": "CS102",
        "subject_name": "Software Engineering",
        "credits": 4,
        "class_name": "Class-A"
    }, db=test_db)

    # 1. Assessment 1 on Sep 1: 90% (45/50)
    AssessmentService.create_assessment({
        "assessment_id": "ASM_T1", "student_id": "STU_TREND", "subject_code": "CS102",
        "assessment_name": "Quiz 1", "assessment_type": "Quiz",
        "marks": 45.0, "max_marks": 50.0, "assessment_date": "2026-09-01"
    }, db=test_db)

    # Check diagnostic with 1 assessment -> insufficient data for trend
    d1 = InsightsService.get_student_diagnostic("STU_TREND", db=test_db)
    assert "Baseline" in d1["trend_status"]

    # 2. Add Assessment 2 (Sep 15: 80%) and Assessment 3 (Oct 1: 40%) and Assessment 4 (Oct 15: 35%)
    # Initial: (90 + 80) / 2 = 85.0%
    # Recent: (40 + 35) / 2 = 37.5% -> drop of -47.5%
    AssessmentService.create_assessment({
        "assessment_id": "ASM_T2", "student_id": "STU_TREND", "subject_code": "CS102",
        "assessment_name": "Quiz 2", "assessment_type": "Quiz",
        "marks": 40.0, "max_marks": 50.0, "assessment_date": "2026-09-15"
    }, db=test_db)
    AssessmentService.create_assessment({
        "assessment_id": "ASM_T3", "student_id": "STU_TREND", "subject_code": "CS102",
        "assessment_name": "Midterm", "assessment_type": "Midterm",
        "marks": 20.0, "max_marks": 50.0, "assessment_date": "2026-10-01"
    }, db=test_db)
    AssessmentService.create_assessment({
        "assessment_id": "ASM_T4", "student_id": "STU_TREND", "subject_code": "CS102",
        "assessment_name": "Quiz 3", "assessment_type": "Quiz",
        "marks": 17.5, "max_marks": 50.0, "assessment_date": "2026-10-15"
    }, db=test_db)

    d2 = InsightsService.get_student_diagnostic("STU_TREND", db=test_db)
    assert "Declining" in d2["trend_status"]
    assert d2["trend_delta"] < -20.0

    # Ensure actionable intervention recommendation was generated
    categories = [r["category"] for r in d2["recommendations"]]
    assert "Performance Trend Intervention" in categories


def test_seed_script_idempotency(test_db):
    """
    Test that running the seed_database function multiple times without reset
    does not create duplicate student IDs or violate uniqueness constraints.
    """
    # Run 1 in demo mode on test_db
    seed_database(student_count=10, reset=False, demo=True, db_name=test_db.name)
    count1_students = test_db["students"].count_documents({})
    count1_subjects = test_db["subjects"].count_documents({})

    assert count1_students == 30  # Demo mode generates 30
    assert count1_subjects == 8

    # Run 2 in demo mode without reset (should update/upsert cleanly)
    seed_database(student_count=10, reset=False, demo=True, db_name=test_db.name)
    count2_students = test_db["students"].count_documents({})
    count2_subjects = test_db["subjects"].count_documents({})

    assert count2_students == 30
    assert count2_subjects == 8
