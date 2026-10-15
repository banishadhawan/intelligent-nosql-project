"""
Domain data models and Pydantic validation schemas for IntelliTrack.
"""

from .student import StudentModel, StudentCreateModel, StudentUpdateModel
from .subject import SubjectModel, SubjectCreateModel, SubjectUpdateModel
from .assessment import AssessmentModel, AssessmentCreateModel, AssessmentUpdateModel
from .attendance import AttendanceModel, AttendanceCreateModel, AttendanceUpdateModel

__all__ = [
    "StudentModel",
    "StudentCreateModel",
    "StudentUpdateModel",
    "SubjectModel",
    "SubjectCreateModel",
    "SubjectUpdateModel",
    "AssessmentModel",
    "AssessmentCreateModel",
    "AssessmentUpdateModel",
    "AttendanceModel",
    "AttendanceCreateModel",
    "AttendanceUpdateModel",
]
