"""
Attendance service layer.
Encapsulates attendance recording, duplicate prevention, referential verification,
and attendance queries.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from database.connection import get_database
from models.attendance import AttendanceCreateModel, AttendanceUpdateModel
from config import config

logger = logging.getLogger("intellitrack.services.attendance")


class AttendanceService:
    @staticmethod
    def create_attendance(
        data: Dict[str, Any],
        db: Optional[Database] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Record a single attendance document.
        Ensures student and subject exist, and prevents duplicate records for same student+subject+date.
        """
        database = db if db is not None else get_database()
        try:
            validated = AttendanceCreateModel(**data)
            att_dict = validated.model_dump()

            # Check student exists
            student = database[config.COLLECTION_STUDENTS].find_one({"student_id": validated.student_id})
            if not student:
                return False, f"Referential error: Student '{validated.student_id}' does not exist.", None

            # Check subject exists
            subject = database[config.COLLECTION_SUBJECTS].find_one({"subject_code": validated.subject_code})
            if not subject:
                return False, f"Referential error: Subject '{validated.subject_code}' does not exist.", None

            # Check duplicate entry manually before insert (application-level check)
            existing = database[config.COLLECTION_ATTENDANCE].find_one({
                "student_id": validated.student_id,
                "subject_code": validated.subject_code,
                "attendance_date": validated.attendance_date
            })
            if existing:
                return False, (
                    f"Duplicate error: Attendance record for student '{validated.student_id}' in "
                    f"subject '{validated.subject_code}' on '{validated.attendance_date}' already exists."
                ), None

            result = database[config.COLLECTION_ATTENDANCE].insert_one(att_dict)
            att_dict["_id"] = str(result.inserted_id)
            return True, "Attendance recorded successfully.", att_dict
        except DuplicateKeyError:
            return False, "Duplicate attendance entry: Record already exists for this date and subject.", None
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error during attendance recording: {err}")
            return False, "Database error occurred while recording attendance.", None
        except Exception as err:
            return False, f"Error: {str(err)}", None

    @staticmethod
    def list_attendance(
        student_id: str = "",
        subject_code: str = "",
        status: str = "",
        start_date: str = "",
        end_date: str = "",
        limit: int = 1500,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Query attendance records with optional filters.
        """
        database = db if db is not None else get_database()
        query: Dict[str, Any] = {}

        if student_id:
            query["student_id"] = student_id.strip().upper()
        if subject_code and subject_code != "All Subjects":
            query["subject_code"] = subject_code.strip().upper()
        if status and status != "All Statuses":
            query["status"] = status.strip()

        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        if date_query:
            query["attendance_date"] = date_query

        cursor = database[config.COLLECTION_ATTENDANCE].find(query).sort("attendance_date", -1).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    @staticmethod
    def update_attendance(
        student_id: str,
        subject_code: str,
        attendance_date: str,
        update_data: Dict[str, Any],
        db: Optional[Database] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update status or remarks of an attendance entry.
        """
        database = db if db is not None else get_database()
        stu_id = student_id.strip().upper()
        sub_code = subject_code.strip().upper()

        filter_query = {
            "student_id": stu_id,
            "subject_code": sub_code,
            "attendance_date": attendance_date
        }

        existing = database[config.COLLECTION_ATTENDANCE].find_one(filter_query)
        if not existing:
            return False, "Attendance record not found.", None

        try:
            validated = AttendanceUpdateModel(**update_data)
            update_fields = {k: v for k, v in validated.model_dump(exclude_unset=True).items() if v is not None}

            if not update_fields:
                return False, "No valid fields to update.", None

            database[config.COLLECTION_ATTENDANCE].update_one(filter_query, {"$set": update_fields})
            updated = database[config.COLLECTION_ATTENDANCE].find_one(filter_query)
            if updated and "_id" in updated:
                updated["_id"] = str(updated["_id"])
            return True, "Attendance updated successfully.", updated
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error updating attendance: {err}")
            return False, "Database error occurred while updating attendance.", None

    @staticmethod
    def delete_attendance(
        student_id: str,
        subject_code: str,
        attendance_date: str,
        db: Optional[Database] = None
    ) -> Tuple[bool, str]:
        """
        Delete an individual attendance record.
        """
        database = db if db is not None else get_database()
        stu_id = student_id.strip().upper()
        sub_code = subject_code.strip().upper()

        filter_query = {
            "student_id": stu_id,
            "subject_code": sub_code,
            "attendance_date": attendance_date
        }

        existing = database[config.COLLECTION_ATTENDANCE].find_one(filter_query)
        if not existing:
            return False, "Attendance record not found."

        try:
            database[config.COLLECTION_ATTENDANCE].delete_one(filter_query)
            return True, "Attendance record deleted successfully."
        except PyMongoError as err:
            logger.error(f"Database error deleting attendance: {err}")
            return False, "Database error occurred while deleting attendance."
