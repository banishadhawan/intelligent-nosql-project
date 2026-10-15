"""
Subject service layer.
Encapsulates CRUD operations, search, and safe deletion checks for academic subjects.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from database.connection import get_database
from models.subject import SubjectCreateModel, SubjectUpdateModel
from config import config

logger = logging.getLogger("intellitrack.services.subject")


class SubjectService:
    @staticmethod
    def create_subject(data: Dict[str, Any], db: Optional[Database] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and insert a new subject document.
        """
        database = db if db is not None else get_database()
        try:
            validated = SubjectCreateModel(**data)
            subject_dict = validated.model_dump()

            result = database[config.COLLECTION_SUBJECTS].insert_one(subject_dict)
            subject_dict["_id"] = str(result.inserted_id)
            return True, f"Subject {validated.subject_code} registered successfully.", subject_dict
        except DuplicateKeyError:
            return False, f"Subject code '{data.get('subject_code')}' already exists.", None
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error during subject creation: {err}")
            return False, "Database error occurred while saving subject.", None
        except Exception as err:
            return False, f"Error: {str(err)}", None

    @staticmethod
    def get_subject_by_code(subject_code: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a subject by subject_code.
        """
        database = db if db is not None else get_database()
        clean_code = subject_code.strip().upper()
        doc = database[config.COLLECTION_SUBJECTS].find_one({"subject_code": clean_code})
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @staticmethod
    def list_subjects(
        search: str = "",
        class_filter: str = "",
        limit: int = 100,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        List subjects with optional search and class filter.
        """
        database = db if db is not None else get_database()
        query: Dict[str, Any] = {}

        if search:
            regex = {"$regex": search.strip(), "$options": "i"}
            query["$or"] = [
                {"subject_code": regex},
                {"subject_name": regex},
                {"description": regex}
            ]

        if class_filter and class_filter != "All Classes":
            query["class_name"] = class_filter.strip()

        cursor = database[config.COLLECTION_SUBJECTS].find(query).sort("subject_code", 1).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    @staticmethod
    def update_subject(
        subject_code: str,
        update_data: Dict[str, Any],
        db: Optional[Database] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update an existing subject.
        """
        database = db if db is not None else get_database()
        clean_code = subject_code.strip().upper()

        existing = database[config.COLLECTION_SUBJECTS].find_one({"subject_code": clean_code})
        if not existing:
            return False, f"Subject '{clean_code}' does not exist.", None

        try:
            validated = SubjectUpdateModel(**update_data)
            update_fields = {k: v for k, v in validated.model_dump(exclude_unset=True).items() if v is not None}

            if not update_fields:
                return False, "No valid fields to update.", None

            database[config.COLLECTION_SUBJECTS].update_one(
                {"subject_code": clean_code},
                {"$set": update_fields}
            )
            updated = database[config.COLLECTION_SUBJECTS].find_one({"subject_code": clean_code})
            if updated and "_id" in updated:
                updated["_id"] = str(updated["_id"])
            return True, f"Subject '{clean_code}' updated successfully.", updated
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error updating subject: {err}")
            return False, "Database error occurred while updating subject.", None

    @staticmethod
    def delete_subject(
        subject_code: str,
        cascade: bool = False,
        db: Optional[Database] = None
    ) -> Tuple[bool, str]:
        """
        Delete a subject.
        Safe policy: Prevents deletion if referenced by existing assessments or attendance,
        unless cascade=True is explicitly specified.
        """
        database = db if db is not None else get_database()
        clean_code = subject_code.strip().upper()

        existing = database[config.COLLECTION_SUBJECTS].find_one({"subject_code": clean_code})
        if not existing:
            return False, f"Subject '{clean_code}' not found."

        asm_count = database[config.COLLECTION_ASSESSMENTS].count_documents({"subject_code": clean_code})
        att_count = database[config.COLLECTION_ATTENDANCE].count_documents({"subject_code": clean_code})

        if not cascade and (asm_count > 0 or att_count > 0):
            return False, (
                f"Cannot delete subject '{clean_code}': referenced by {asm_count} assessment(s) "
                f"and {att_count} attendance record(s). Deletion prevented to preserve data integrity."
            )

        try:
            if cascade:
                database[config.COLLECTION_ASSESSMENTS].delete_many({"subject_code": clean_code})
                database[config.COLLECTION_ATTENDANCE].delete_many({"subject_code": clean_code})

            database[config.COLLECTION_SUBJECTS].delete_one({"subject_code": clean_code})
            return True, f"Deleted subject '{clean_code}' (cascaded {asm_count} assessments, {att_count} attendance records)."
        except PyMongoError as err:
            logger.error(f"Database error deleting subject: {err}")
            return False, "Database error occurred while deleting subject."
