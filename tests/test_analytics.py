"""
Integration tests for MongoDB aggregation pipelines on known, controlled datasets.
Validates percentage normalizations, varying max_marks calculations, and empty collection handling.
"""

import pytest
from services.analytics_service import AnalyticsService
from services.student_service import StudentService
from services.subject_service import SubjectService
from services.assessment_service import AssessmentService
from services.attendance_service import AttendanceService


def test_empty_collection_analytics(test_db):
    """Verify that aggregation pipelines handle empty collections gracefully."""
    kpis = AnalyticsService.get_system_kpis(db=test_db)
    assert kpis["total_students"] == 0
    assert kpis["total_assessments"] == 0
    assert kpis["overall_marks_avg"] == 0.0
    assert kpis["pass_rate"] == 0.0

    res_sub = AnalyticsService.get_average_marks_by_subject(db=test_db)
    assert res_sub == []

    res_top = AnalyticsService.get_top_students(db=test_db)
    assert res_top == []

    res_pass = AnalyticsService.get_pass_rate_by_subject(db=test_db)
    assert res_pass == []


def test_controlled_aggregation_results(test_db):
    """
    Validates mathematical precision of aggregation pipelines against a controlled dataset
    where assessment maximum marks differ (50 marks vs 20 marks).
    """
    # 1. Register 2 Students
    StudentService.create_student({
        "student_id": "STU1", "name": "Alice", "email": "alice@test.edu",
        "class_name": "Class-A", "enrollment_date": "2026-08-01"
    }, db=test_db)
    StudentService.create_student({
        "student_id": "STU2", "name": "Bob", "email": "bob@test.edu",
        "class_name": "Class-A", "enrollment_date": "2026-08-01"
    }, db=test_db)

    # 2. Register 2 Subjects
    SubjectService.create_subject({
        "subject_code": "SUB1", "subject_name": "Database Analytics",
        "credits": 4, "class_name": "Class-A"
    }, db=test_db)
    SubjectService.create_subject({
        "subject_code": "SUB2", "subject_name": "Algorithms",
        "credits": 4, "class_name": "Class-A"
    }, db=test_db)

    # 3. Create Assessments with varying max_marks:
    # Alice SUB1: 40/50 = 80.0%
    # Alice SUB2: 18/20 = 90.0%  (Alice overall mean: 85.0%)
    # Bob SUB1:   20/50 = 40.0%
    # Bob SUB2:   10/20 = 50.0%  (Bob overall mean: 45.0%)
    AssessmentService.create_assessment({
        "assessment_id": "ASM1", "student_id": "STU1", "subject_code": "SUB1",
        "assessment_name": "Midterm", "assessment_type": "Midterm",
        "marks": 40.0, "max_marks": 50.0, "assessment_date": "2026-09-01"
    }, db=test_db)
    AssessmentService.create_assessment({
        "assessment_id": "ASM2", "student_id": "STU1", "subject_code": "SUB2",
        "assessment_name": "Quiz", "assessment_type": "Quiz",
        "marks": 18.0, "max_marks": 20.0, "assessment_date": "2026-09-02"
    }, db=test_db)
    AssessmentService.create_assessment({
        "assessment_id": "ASM3", "student_id": "STU2", "subject_code": "SUB1",
        "assessment_name": "Midterm", "assessment_type": "Midterm",
        "marks": 20.0, "max_marks": 50.0, "assessment_date": "2026-09-01"
    }, db=test_db)
    AssessmentService.create_assessment({
        "assessment_id": "ASM4", "student_id": "STU2", "subject_code": "SUB2",
        "assessment_name": "Quiz", "assessment_type": "Quiz",
        "marks": 10.0, "max_marks": 20.0, "assessment_date": "2026-09-02"
    }, db=test_db)

    # Pipeline 3: Verify Top Students ranking
    top_students = AnalyticsService.get_top_students(limit=10, db=test_db)
    assert len(top_students) == 2
    assert top_students[0]["student_id"] == "STU1"
    assert top_students[0]["overall_average"] == 85.0
    assert top_students[1]["student_id"] == "STU2"
    assert top_students[1]["overall_average"] == 45.0

    # Pipeline 1: Verify Subject Averages
    # SUB1: (80 + 40) / 2 = 60.0%
    # SUB2: (90 + 50) / 2 = 70.0%
    sub_perf = {s["subject_code"]: s["avg_percentage"] for s in AnalyticsService.get_average_marks_by_subject(db=test_db)}
    assert sub_perf["SUB1"] == 60.0
    assert sub_perf["SUB2"] == 70.0

    # Pipeline 4: Verify Pass Rate with threshold=50%
    # SUB1 has 1 pass (80%) and 1 fail (40%) -> 50.0% pass rate
    # SUB2 has 2 passes (90%, 50%) -> 100.0% pass rate
    pass_rates = {s["subject_code"]: s["pass_rate"] for s in AnalyticsService.get_pass_rate_by_subject(pass_threshold=50.0, db=test_db)}
    assert pass_rates["SUB1"] == 50.0
    assert pass_rates["SUB2"] == 100.0

    # Pipeline 9: Low marks threshold = 50.0%
    # Bob (45.0%) must be flagged; Alice (85.0%) must not be flagged
    low_marks = AnalyticsService.get_students_with_low_marks(threshold=50.0, db=test_db)
    assert len(low_marks) == 1
    assert low_marks[0]["student_id"] == "STU2"
    assert low_marks[0]["overall_average"] == 45.0

    # Pipeline 7: Attendance with Late weight (0.5)
    # Alice: 1 Present, 1 Late -> (1.0 + 0.5) / 2 = 75.0%
    # Bob: 1 Absent, 1 Late -> (0.0 + 0.5) / 2 = 25.0%
    AttendanceService.create_attendance({"student_id": "STU1", "subject_code": "SUB1", "attendance_date": "2026-09-01", "status": "Present"}, db=test_db)
    AttendanceService.create_attendance({"student_id": "STU1", "subject_code": "SUB1", "attendance_date": "2026-09-02", "status": "Late"}, db=test_db)
    AttendanceService.create_attendance({"student_id": "STU2", "subject_code": "SUB1", "attendance_date": "2026-09-01", "status": "Absent"}, db=test_db)
    AttendanceService.create_attendance({"student_id": "STU2", "subject_code": "SUB1", "attendance_date": "2026-09-02", "status": "Late"}, db=test_db)

    att_pcts = {s["student_id"]: s["attendance_percentage"] for s in AnalyticsService.get_attendance_percentage_per_student(late_weight=0.5, db=test_db)}
    assert att_pcts["STU1"] == 75.0
    assert att_pcts["STU2"] == 25.0
