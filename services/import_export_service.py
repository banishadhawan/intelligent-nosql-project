"""
Import and Export Service for IntelliTrack.
Provides row-level validated CSV import and data export for students, assessments, and attendance.
"""

import io
import csv
import logging
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd
from pymongo.database import Database
from database.connection import get_database
from models.student import StudentCreateModel
from models.assessment import AssessmentCreateModel
from models.attendance import AttendanceCreateModel
from config import config

logger = logging.getLogger("intellitrack.services.import_export")


class ImportExportService:

    # -------------------------------------------------------------------------
    # CSV IMPORT: STUDENTS
    # -------------------------------------------------------------------------
    @staticmethod
    def import_students_csv(
        csv_file_or_content,
        skip_duplicates: bool = True,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        """
        Validates and imports students from CSV.
        Returns a detailed row-by-row error log and count of successfully inserted documents.
        """
        database = db if db is not None else get_database()
        if isinstance(csv_file_or_content, bytes):
            stream = io.StringIO(csv_file_or_content.decode("utf-8-sig"))
        elif isinstance(csv_file_or_content, str):
            stream = io.StringIO(csv_file_or_content)
        else:
            stream = io.StringIO(csv_file_or_content.getvalue().decode("utf-8-sig"))

        reader = csv.DictReader(stream)
        valid_records = []
        errors = []
        row_number = 1

        existing_ids = set(database[config.COLLECTION_STUDENTS].distinct("student_id"))
        existing_emails = set(database[config.COLLECTION_STUDENTS].distinct("email"))
        batch_ids = set()
        batch_emails = set()

        for row in reader:
            row_number += 1
            row_errors = []

            # Clean and normalize input row
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}

            stu_id = cleaned.get("student_id", "").upper()
            email = cleaned.get("email", "").lower()

            # Duplicate checks
            if stu_id in existing_ids:
                if skip_duplicates:
                    continue
                row_errors.append(f"Student ID '{stu_id}' already exists in database.")
            if stu_id in batch_ids:
                row_errors.append(f"Duplicate student ID '{stu_id}' in CSV file.")

            if email in existing_emails:
                if skip_duplicates:
                    continue
                row_errors.append(f"Email '{email}' is already in use by another student.")
            if email in batch_emails:
                row_errors.append(f"Duplicate email '{email}' in CSV file.")

            # Model validation
            try:
                model = StudentCreateModel(
                    student_id=stu_id,
                    name=cleaned.get("name", ""),
                    email=email,
                    class_name=cleaned.get("class_name", ""),
                    enrollment_date=cleaned.get("enrollment_date", ""),
                    skills=cleaned.get("skills", "")
                )
                valid_dict = model.model_dump()
            except Exception as err:
                row_errors.append(str(err))

            if row_errors:
                errors.append({"row": row_number, "data": cleaned, "errors": row_errors})
            else:
                batch_ids.add(stu_id)
                batch_emails.add(email)
                valid_records.append(valid_dict)

        # Insert valid records
        inserted_count = 0
        if valid_records:
            res = database[config.COLLECTION_STUDENTS].insert_many(valid_records)
            inserted_count = len(res.inserted_ids)

        return {
            "total_rows_processed": row_number - 1,
            "valid_records_count": len(valid_records),
            "inserted_count": inserted_count,
            "error_count": len(errors),
            "errors": errors
        }

    # -------------------------------------------------------------------------
    # CSV IMPORT: ASSESSMENTS
    # -------------------------------------------------------------------------
    @staticmethod
    def import_assessments_csv(
        csv_file_or_content,
        skip_duplicates: bool = True,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        """
        Validates and imports assessments from CSV.
        Checks foreign key presence for student_id and subject_code.
        """
        database = db if db is not None else get_database()
        if isinstance(csv_file_or_content, bytes):
            stream = io.StringIO(csv_file_or_content.decode("utf-8-sig"))
        elif isinstance(csv_file_or_content, str):
            stream = io.StringIO(csv_file_or_content)
        else:
            stream = io.StringIO(csv_file_or_content.getvalue().decode("utf-8-sig"))

        reader = csv.DictReader(stream)
        valid_records = []
        errors = []
        row_number = 1

        existing_students = set(database[config.COLLECTION_STUDENTS].distinct("student_id"))
        existing_subjects = set(database[config.COLLECTION_SUBJECTS].distinct("subject_code"))
        existing_asm_ids = set(database[config.COLLECTION_ASSESSMENTS].distinct("assessment_id"))
        batch_ids = set()

        for row in reader:
            row_number += 1
            row_errors = []
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}

            asm_id = cleaned.get("assessment_id", "").upper()
            stu_id = cleaned.get("student_id", "").upper()
            sub_code = cleaned.get("subject_code", "").upper()

            if asm_id in existing_asm_ids:
                if skip_duplicates:
                    continue
                row_errors.append(f"Assessment ID '{asm_id}' already exists.")
            if asm_id in batch_ids:
                row_errors.append(f"Duplicate Assessment ID '{asm_id}' in file.")

            if stu_id not in existing_students:
                row_errors.append(f"Referenced Student '{stu_id}' does not exist.")

            if sub_code not in existing_subjects:
                row_errors.append(f"Referenced Subject '{sub_code}' does not exist.")

            try:
                marks_val = float(cleaned.get("marks", 0))
                max_marks_val = float(cleaned.get("max_marks", 100))
                model = AssessmentCreateModel(
                    assessment_id=asm_id,
                    student_id=stu_id,
                    subject_code=sub_code,
                    assessment_name=cleaned.get("assessment_name", ""),
                    assessment_type=cleaned.get("assessment_type", "Quiz"),
                    marks=marks_val,
                    max_marks=max_marks_val,
                    assessment_date=cleaned.get("assessment_date", ""),
                    remarks=cleaned.get("remarks", "")
                )
                valid_dict = model.model_dump()
                valid_dict["percentage"] = round((marks_val / max_marks_val) * 100.0, 2)
            except Exception as err:
                row_errors.append(str(err))

            if row_errors:
                errors.append({"row": row_number, "data": cleaned, "errors": row_errors})
            else:
                batch_ids.add(asm_id)
                valid_records.append(valid_dict)

        inserted_count = 0
        if valid_records:
            res = database[config.COLLECTION_ASSESSMENTS].insert_many(valid_records)
            inserted_count = len(res.inserted_ids)

        return {
            "total_rows_processed": row_number - 1,
            "valid_records_count": len(valid_records),
            "inserted_count": inserted_count,
            "error_count": len(errors),
            "errors": errors
        }

    # -------------------------------------------------------------------------
    # CSV IMPORT: ATTENDANCE
    # -------------------------------------------------------------------------
    @staticmethod
    def import_attendance_csv(
        csv_file_or_content,
        skip_duplicates: bool = True,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        """
        Validates and imports attendance records from CSV.
        Prevents duplicate records for identical student + subject + date.
        """
        database = db if db is not None else get_database()
        if isinstance(csv_file_or_content, bytes):
            stream = io.StringIO(csv_file_or_content.decode("utf-8-sig"))
        elif isinstance(csv_file_or_content, str):
            stream = io.StringIO(csv_file_or_content)
        else:
            stream = io.StringIO(csv_file_or_content.getvalue().decode("utf-8-sig"))

        reader = csv.DictReader(stream)
        valid_records = []
        errors = []
        row_number = 1

        existing_students = set(database[config.COLLECTION_STUDENTS].distinct("student_id"))
        existing_subjects = set(database[config.COLLECTION_SUBJECTS].distinct("subject_code"))
        batch_keys = set()

        for row in reader:
            row_number += 1
            row_errors = []
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}

            stu_id = cleaned.get("student_id", "").upper()
            sub_code = cleaned.get("subject_code", "").upper()
            att_date = cleaned.get("attendance_date", "")

            if stu_id not in existing_students:
                row_errors.append(f"Student '{stu_id}' does not exist.")

            if sub_code not in existing_subjects:
                row_errors.append(f"Subject '{sub_code}' does not exist.")

            key = (stu_id, sub_code, att_date)
            if key in batch_keys:
                row_errors.append(f"Duplicate attendance entry for {stu_id} on {att_date} in CSV.")

            # Check database for existing record
            if database[config.COLLECTION_ATTENDANCE].find_one({"student_id": stu_id, "subject_code": sub_code, "attendance_date": att_date}):
                if skip_duplicates:
                    continue
                row_errors.append(f"Attendance for {stu_id} on {att_date} in {sub_code} already exists in DB.")

            try:
                model = AttendanceCreateModel(
                    student_id=stu_id,
                    subject_code=sub_code,
                    attendance_date=att_date,
                    status=cleaned.get("status", "Present"),
                    remarks=cleaned.get("remarks", "")
                )
                valid_dict = model.model_dump()
            except Exception as err:
                row_errors.append(str(err))

            if row_errors:
                errors.append({"row": row_number, "data": cleaned, "errors": row_errors})
            else:
                batch_keys.add(key)
                valid_records.append(valid_dict)

        inserted_count = 0
        if valid_records:
            res = database[config.COLLECTION_ATTENDANCE].insert_many(valid_records)
            inserted_count = len(res.inserted_ids)

        return {
            "total_rows_processed": row_number - 1,
            "valid_records_count": len(valid_records),
            "inserted_count": inserted_count,
            "error_count": len(errors),
            "errors": errors
        }

    # -------------------------------------------------------------------------
    # CSV EXPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def export_collection_to_csv(collection_name: str, db: Optional[Database] = None) -> str:
        """
        Exports all documents from a given collection to CSV string.
        Excludes raw MongoDB ObjectId `_id` to ensure clean export.
        """
        database = db if db is not None else get_database()
        cursor = database[collection_name].find({}, {"_id": 0})
        docs = list(cursor)
        if not docs:
            return ""

        # Flatten array fields like skills if present
        for d in docs:
            if "skills" in d and isinstance(d["skills"], list):
                d["skills"] = ", ".join(d["skills"])

        df = pd.DataFrame(docs)
        return df.to_csv(index=False)
