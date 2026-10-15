"""
Student service layer.
Encapsulates CRUD operations, search, filtering, and safe deletion cascades for students.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from database.connection import get_database
from models.student import StudentCreateModel, StudentUpdateModel
from config import config

logger = logging.getLogger("intellitrack.services.student")


class StudentService:
    @staticmethod
    def create_student(data: Dict[str, Any], db: Optional[Database] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and insert a new student document.
        """
        database = db if db is not None else get_database()
        try:
            # Pydantic validation
            validated_model = StudentCreateModel(**data)
            student_dict = validated_model.model_dump()

            # Insert into MongoDB
            result = database[config.COLLECTION_STUDENTS].insert_one(student_dict)
            student_dict["_id"] = str(result.inserted_id)
            return True, f"Student {validated_model.student_id} registered successfully.", student_dict
        except DuplicateKeyError as err:
            if "student_id" in str(err):
                return False, f"Student ID '{data.get('student_id')}' already exists.", None
            if "email" in str(err):
                return False, f"Email '{data.get('email')}' is already registered to another student.", None
            return False, "Duplicate record detected.", None
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error during student creation: {err}")
            return False, "Database error occurred while saving student.", None
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            return False, f"Error: {str(err)}", None

    @staticmethod
    def get_student_by_id(student_id: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single student by student_id.
        """
        database = db if db is not None else get_database()
        clean_id = student_id.strip().upper()
        doc = database[config.COLLECTION_STUDENTS].find_one({"student_id": clean_id})
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @staticmethod
    def list_students(
        search: str = "",
        class_filter: str = "",
        limit: int = 1000,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and filter students by name, ID, or class.
        """
        database = db if db is not None else get_database()
        query: Dict[str, Any] = {}

        if search:
            search_regex = {"$regex": search.strip(), "$options": "i"}
            query["$or"] = [
                {"student_id": search_regex},
                {"name": search_regex},
                {"email": search_regex}
            ]

        if class_filter and class_filter != "All Classes":
            query["class_name"] = class_filter.strip()

        cursor = database[config.COLLECTION_STUDENTS].find(query).sort("student_id", 1).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    @staticmethod
    def update_student(
        student_id: str,
        update_data: Dict[str, Any],
        db: Optional[Database] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and update an existing student document.
        """
        database = db if db is not None else get_database()
        clean_id = student_id.strip().upper()
        existing = database[config.COLLECTION_STUDENTS].find_one({"student_id": clean_id})
        if not existing:
            return False, f"Student '{clean_id}' does not exist.", None

        try:
            # Validate partial update
            validated = StudentUpdateModel(**update_data)
            update_fields = {k: v for k, v in validated.model_dump(exclude_unset=True).items() if v is not None}

            if not update_fields:
                return False, "No valid fields to update.", None

            database[config.COLLECTION_STUDENTS].update_one(
                {"student_id": clean_id},
                {"$set": update_fields}
            )
            updated = database[config.COLLECTION_STUDENTS].find_one({"student_id": clean_id})
            if updated and "_id" in updated:
                updated["_id"] = str(updated["_id"])
            return True, f"Student '{clean_id}' updated successfully.", updated
        except DuplicateKeyError as err:
            if "email" in str(err):
                return False, f"Email '{update_data.get('email')}' is already used by another student.", None
            return False, "Duplicate value violates unique index.", None
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error updating student: {err}")
            return False, "Database error occurred while updating student.", None

    @staticmethod
    def delete_student(
        student_id: str,
        cascade: bool = True,
        db: Optional[Database] = None
    ) -> Tuple[bool, str]:
        """
        Delete student and handle related assessments and attendance.
        If cascade=True, cleanly removes all related assessments and attendance records.
        If cascade=False, blocks deletion if related records exist.
        """
        database = db if db is not None else get_database()
        clean_id = student_id.strip().upper()

        existing = database[config.COLLECTION_STUDENTS].find_one({"student_id": clean_id})
        if not existing:
            return False, f"Student '{clean_id}' not found."

        # Count related records
        asm_count = database[config.COLLECTION_ASSESSMENTS].count_documents({"student_id": clean_id})
        att_count = database[config.COLLECTION_ATTENDANCE].count_documents({"student_id": clean_id})

        if not cascade and (asm_count > 0 or att_count > 0):
            return False, f"Cannot delete: Student has {asm_count} assessment(s) and {att_count} attendance record(s). Enable cascade deletion to proceed."

        try:
            # Cascade deletion
            if cascade:
                database[config.COLLECTION_ASSESSMENTS].delete_many({"student_id": clean_id})
                database[config.COLLECTION_ATTENDANCE].delete_many({"student_id": clean_id})

            database[config.COLLECTION_STUDENTS].delete_one({"student_id": clean_id})
            return True, f"Deleted student '{clean_id}' along with {asm_count} assessments and {att_count} attendance records."
        except PyMongoError as err:
            logger.error(f"Error during student deletion: {err}")
            return False, "Database error occurred while deleting student."

    @staticmethod
    def get_classes_list(db: Optional[Database] = None) -> List[str]:
        """
        Returns distinct class names.
        """
        database = db if db is not None else get_database()
        classes = database[config.COLLECTION_STUDENTS].distinct("class_name")
        return sorted([c for c in classes if c])
