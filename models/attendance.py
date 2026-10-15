"""
Attendance data models and validation schemas.
"""

from typing import Optional, Literal
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

ATTENDANCE_STATUSES = ("Present", "Absent", "Late")


class AttendanceBase(BaseModel):
    student_id: str = Field(..., min_length=2, max_length=20)
    subject_code: str = Field(..., min_length=2, max_length=20)
    attendance_date: str = Field(..., description="Date of attendance in YYYY-MM-DD format")
    status: str = Field(..., description="Status: Present, Absent, or Late")
    remarks: Optional[str] = Field(default="", description="Optional remarks")

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Student ID cannot be empty.")
        return clean

    @field_validator("subject_code")
    @classmethod
    def validate_subject_code(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Subject code cannot be empty.")
        return clean

    @field_validator("attendance_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if isinstance(v, (date, datetime)):
            return v.strftime("%Y-%m-%d")
        clean = str(v).strip()
        try:
            parsed = datetime.strptime(clean, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Attendance date '{v}' must be in YYYY-MM-DD format.")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().title()
        if clean not in ATTENDANCE_STATUSES:
            raise ValueError(f"Status '{v}' is invalid. Allowed values: {', '.join(ATTENDANCE_STATUSES)}")
        return clean


class AttendanceCreateModel(AttendanceBase):
    pass


class AttendanceUpdateModel(BaseModel):
    status: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().title()
            if clean not in ATTENDANCE_STATUSES:
                raise ValueError(f"Status '{v}' is invalid. Allowed values: {', '.join(ATTENDANCE_STATUSES)}")
            return clean
        return None


class AttendanceModel(AttendanceBase):
    model_config = ConfigDict(extra="ignore")
