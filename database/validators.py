"""
MongoDB collection-level schema validation definitions and setup.
Applies JSON schema validators directly to MongoDB collections.
"""

import logging
from pymongo.database import Database
from pymongo.errors import OperationFailure
from config import config

logger = logging.getLogger("intellitrack.validators")

STUDENT_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["student_id", "name", "email", "class_name", "enrollment_date"],
        "properties": {
            "student_id": {
                "bsonType": "string",
                "description": "Unique student identifier (e.g., STU1001) - required"
            },
            "name": {
                "bsonType": "string",
                "description": "Full student name - required"
            },
            "email": {
                "bsonType": "string",
                "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                "description": "Valid email address - required"
            },
            "class_name": {
                "bsonType": "string",
                "description": "Enrolled class or section - required"
            },
            "enrollment_date": {
                "bsonType": ["date", "string"],
                "description": "Enrollment date - required"
            },
            "skills": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
                "description": "List of student technical skills or interests"
            }
        }
    }
}

SUBJECT_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["subject_code", "subject_name", "credits", "class_name"],
        "properties": {
            "subject_code": {
                "bsonType": "string",
                "description": "Unique subject code (e.g. CS301) - required"
            },
            "subject_name": {
                "bsonType": "string",
                "description": "Full subject course title - required"
            },
            "description": {
                "bsonType": "string",
                "description": "Subject description"
            },
            "credits": {
                "bsonType": ["int", "double", "long"],
                "minimum": 1,
                "maximum": 10,
                "description": "Subject credits (1-10) - required"
            },
            "class_name": {
                "bsonType": "string",
                "description": "Assigned class/section - required"
            }
        }
    }
}

ASSESSMENT_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["assessment_id", "student_id", "subject_code", "assessment_name", "assessment_type", "marks", "max_marks", "assessment_date"],
        "properties": {
            "assessment_id": {
                "bsonType": "string",
                "description": "Unique assessment identifier - required"
            },
            "student_id": {
                "bsonType": "string",
                "description": "Foreign key to student document - required"
            },
            "subject_code": {
                "bsonType": "string",
                "description": "Foreign key to subject document - required"
            },
            "assessment_name": {
                "bsonType": "string",
                "description": "Name of assessment or quiz - required"
            },
            "assessment_type": {
                "bsonType": "string",
                "enum": ["Quiz", "Midterm", "Final Exam", "Assignment", "Project", "Lab"],
                "description": "Category of assessment"
            },
            "marks": {
                "bsonType": ["int", "double", "long"],
                "minimum": 0,
                "description": "Marks obtained (>= 0)"
            },
            "max_marks": {
                "bsonType": ["int", "double", "long"],
                "minimum": 1,
                "description": "Maximum achievable marks (> 0)"
            },
            "assessment_date": {
                "bsonType": ["date", "string"],
                "description": "Date of assessment"
            },
            "remarks": {
                "bsonType": "string",
                "description": "Optional faculty notes or remarks"
            }
        }
    }
}

ATTENDANCE_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["student_id", "subject_code", "attendance_date", "status"],
        "properties": {
            "student_id": {
                "bsonType": "string",
                "description": "Foreign key to student document - required"
            },
            "subject_code": {
                "bsonType": "string",
                "description": "Subject code - required"
            },
            "attendance_date": {
                "bsonType": ["date", "string"],
                "description": "Date of attendance - required"
            },
            "status": {
                "bsonType": "string",
                "enum": ["Present", "Absent", "Late"],
                "description": "Attendance status - required"
            },
            "remarks": {
                "bsonType": "string",
                "description": "Optional note"
            }
        }
    }
}


def apply_collection_validators(db: Database) -> None:
    """
    Applies JSON Schema validation rules to all primary collections.
    Creates collections if they do not yet exist.
    """
    schemas = {
        config.COLLECTION_STUDENTS: STUDENT_SCHEMA,
        config.COLLECTION_SUBJECTS: SUBJECT_SCHEMA,
        config.COLLECTION_ASSESSMENTS: ASSESSMENT_SCHEMA,
        config.COLLECTION_ATTENDANCE: ATTENDANCE_SCHEMA,
    }

    existing_collections = db.list_collection_names()

    for col_name, schema in schemas.items():
        if col_name not in existing_collections:
            try:
                db.create_collection(col_name, validator=schema)
                logger.info(f"Created collection '{col_name}' with schema validator.")
            except OperationFailure as err:
                logger.warning(f"Could not create collection '{col_name}' with validator: {err}")
        else:
            try:
                db.command({
                    "collMod": col_name,
                    "validator": schema,
                    "validationLevel": "moderate"
                })
                logger.info(f"Updated schema validator on existing collection '{col_name}'.")
            except OperationFailure as err:
                logger.warning(f"Could not update schema validator on '{col_name}': {err}")
