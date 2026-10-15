"""
MongoDB Index Management for IntelliTrack.
Ensures unique constraints and performance-optimized indexes on all collections.
"""

import logging
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from config import config

logger = logging.getLogger("intellitrack.indexes")


def create_all_indexes(db: Database) -> dict:
    """
    Creates necessary unique and compound indexes for students, subjects,
    assessments, and attendance collections.
    Returns a dictionary of created index names per collection.
    """
    created_indexes = {}

    # 1. Students Collection Indexes
    # - Unique: student_id
    # - Unique: email
    # - Filter: class_name
    students_col = db[config.COLLECTION_STUDENTS]
    idx_stu_id = students_col.create_index([("student_id", ASCENDING)], unique=True, name="idx_unique_student_id")
    idx_stu_email = students_col.create_index([("email", ASCENDING)], unique=True, name="idx_unique_student_email")
    idx_stu_class = students_col.create_index([("class_name", ASCENDING)], name="idx_student_class")
    created_indexes["students"] = [idx_stu_id, idx_stu_email, idx_stu_class]

    # 2. Subjects Collection Indexes
    # - Unique: subject_code
    # - Filter: class_name
    subjects_col = db[config.COLLECTION_SUBJECTS]
    idx_sub_code = subjects_col.create_index([("subject_code", ASCENDING)], unique=True, name="idx_unique_subject_code")
    idx_sub_class = subjects_col.create_index([("class_name", ASCENDING)], name="idx_subject_class")
    created_indexes["subjects"] = [idx_sub_code, idx_sub_class]

    # 3. Assessments Collection Indexes
    # - Unique: assessment_id
    # - Compound: student_id + subject_code
    # - Filter: student_id, subject_code, assessment_date
    assessments_col = db[config.COLLECTION_ASSESSMENTS]
    idx_asm_id = assessments_col.create_index([("assessment_id", ASCENDING)], unique=True, name="idx_unique_assessment_id")
    idx_asm_student_subject = assessments_col.create_index(
        [("student_id", ASCENDING), ("subject_code", ASCENDING)],
        name="idx_asm_student_subject"
    )
    idx_asm_student = assessments_col.create_index([("student_id", ASCENDING)], name="idx_asm_student")
    idx_asm_subject = assessments_col.create_index([("subject_code", ASCENDING)], name="idx_asm_subject")
    idx_asm_date = assessments_col.create_index([("assessment_date", DESCENDING)], name="idx_asm_date")
    created_indexes["assessments"] = [idx_asm_id, idx_asm_student_subject, idx_asm_student, idx_asm_subject, idx_asm_date]

    # 4. Attendance Collection Indexes
    # - Unique Compound: student_id + subject_code + attendance_date (prevents duplicate attendance)
    # - Compound: student_id + attendance_date
    # - Filter: status, attendance_date
    attendance_col = db[config.COLLECTION_ATTENDANCE]
    idx_att_unique = attendance_col.create_index(
        [("student_id", ASCENDING), ("subject_code", ASCENDING), ("attendance_date", ASCENDING)],
        unique=True,
        name="idx_unique_student_subject_date"
    )
    idx_att_student = attendance_col.create_index(
        [("student_id", ASCENDING), ("attendance_date", DESCENDING)],
        name="idx_att_student_date"
    )
    idx_att_status = attendance_col.create_index([("status", ASCENDING)], name="idx_att_status")
    created_indexes["attendance"] = [idx_att_unique, idx_att_student, idx_att_status]

    logger.info("Successfully ensured all indexes across collections.")
    return created_indexes
