"""
Assessment service layer.
Encapsulates assessment CRUD, referential integrity checks against students and subjects,
and percentage calculation.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError
from database.connection import get_database
from models.assessment import AssessmentCreateModel, AssessmentUpdateModel
from config import config

logger = logging.getLogger("intellitrack.services.assessment")


class AssessmentService:
    @staticmethod
    def create_assessment(
        data: Dict[str, Any],
        db: Optional[Database] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and insert an assessment record.
        Enforces foreign-key referential integrity to students and subjects.
        """
        database = db if db is not None else get_database()
        try:
            validated = AssessmentCreateModel(**data)
            asm_dict = validated.model_dump()

            # Referential integrity: check student exists
            student = database[config.COLLECTION_STUDENTS].find_one({"student_id": validated.student_id})
            if not student:
                return False, f"Referential error: Student '{validated.student_id}' does not exist.", None

            # Referential integrity: check subject exists
            subject = database[config.COLLECTION_SUBJECTS].find_one({"subject_code": validated.subject_code})
            if not subject:
                return False, f"Referential error: Subject '{validated.subject_code}' does not exist.", None

            # Compute percentage
            asm_dict["percentage"] = round((validated.marks / validated.max_marks) * 100.0, 2)

            result = database[config.COLLECTION_ASSESSMENTS].insert_one(asm_dict)
            asm_dict["_id"] = str(result.inserted_id)
            return True, f"Assessment '{validated.assessment_id}' created successfully.", asm_dict
        except DuplicateKeyError:
            return False, f"Assessment ID '{data.get('assessment_id')}' already exists.", None
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error during assessment creation: {err}")
            return False, "Database error occurred while saving assessment.", None
        except Exception as err:
            return False, f"Error: {str(err)}", None

    @staticmethod
    def get_assessment_by_id(assessment_id: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve an assessment by its ID.
        """
        database = db if db is not None else get_database()
        clean_id = assessment_id.strip().upper()
        doc = database[config.COLLECTION_ASSESSMENTS].find_one({"assessment_id": clean_id})
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @staticmethod
    def list_assessments(
        student_id: str = "",
        subject_code: str = "",
        assessment_type: str = "",
        limit: int = 1000,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        List assessments with filters for student, subject, and type.
        """
        database = db if db is not None else get_database()
        query: Dict[str, Any] = {}

        if student_id:
            query["student_id"] = student_id.strip().upper()
        if subject_code and subject_code != "All Subjects":
            query["subject_code"] = subject_code.strip().upper()
        if assessment_type and assessment_type != "All Types":
            query["assessment_type"] = assessment_type.strip()

        cursor = database[config.COLLECTION_ASSESSMENTS].find(query).sort("assessment_date", -1).limit(limit)
        results = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        return results

    @staticmethod
    def update_assessment(
        assessment_id: str,
        update_data: Dict[str, Any],
        db: Optional[Database] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update an existing assessment and recalculate percentage if marks changed.
        """
        database = db if db is not None else get_database()
        clean_id = assessment_id.strip().upper()

        existing = database[config.COLLECTION_ASSESSMENTS].find_one({"assessment_id": clean_id})
        if not existing:
            return False, f"Assessment '{clean_id}' does not exist.", None

        try:
            validated = AssessmentUpdateModel(**update_data)
            update_fields = {k: v for k, v in validated.model_dump(exclude_unset=True).items() if v is not None}

            if not update_fields:
                return False, "No valid fields to update.", None

            # Calculate new percentage if marks or max_marks updated
            new_marks = update_fields.get("marks", existing.get("marks"))
            new_max = update_fields.get("max_marks", existing.get("max_marks"))
            if new_marks is not None and new_max is not None:
                if new_marks > new_max:
                    return False, f"Marks ({new_marks}) cannot exceed maximum marks ({new_max}).", None
                update_fields["percentage"] = round((new_marks / new_max) * 100.0, 2)

            database[config.COLLECTION_ASSESSMENTS].update_one(
                {"assessment_id": clean_id},
                {"$set": update_fields}
            )
            updated = database[config.COLLECTION_ASSESSMENTS].find_one({"assessment_id": clean_id})
            if updated and "_id" in updated:
                updated["_id"] = str(updated["_id"])
            return True, f"Assessment '{clean_id}' updated successfully.", updated
        except ValueError as err:
            return False, f"Validation error: {str(err)}", None
        except PyMongoError as err:
            logger.error(f"Database error updating assessment: {err}")
            return False, "Database error occurred while updating assessment.", None

    @staticmethod
    def delete_assessment(assessment_id: str, db: Optional[Database] = None) -> Tuple[bool, str]:
        """
        Delete an assessment record by ID.
        """
        database = db if db is not None else get_database()
        clean_id = assessment_id.strip().upper()

        existing = database[config.COLLECTION_ASSESSMENTS].find_one({"assessment_id": clean_id})
        if not existing:
            return False, f"Assessment '{clean_id}' not found."

        try:
            database[config.COLLECTION_ASSESSMENTS].delete_one({"assessment_id": clean_id})
            return True, f"Assessment '{clean_id}' deleted successfully."
        except PyMongoError as err:
            logger.error(f"Database error deleting assessment: {err}")
            return False, "Database error occurred while deleting assessment."
