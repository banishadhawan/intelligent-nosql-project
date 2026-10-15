"""
Student data models and validation schemas.
"""

from typing import List, Optional
from datetime import date, datetime
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict


class StudentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of student")
    email: str = Field(..., description="Student email address")
    class_name: str = Field(..., min_length=2, max_length=50, description="Enrolled class or section")
    enrollment_date: str = Field(..., description="Enrollment date in YYYY-MM-DD format")
    skills: List[str] = Field(default_factory=list, description="List of technical skills or interests")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Student name must have at least 2 characters.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, clean):
            raise ValueError(f"Invalid email format: '{v}'")
        return clean

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Class name cannot be empty.")
        return clean

    @field_validator("enrollment_date")
    @classmethod
    def validate_enrollment_date(cls, v: str) -> str:
        if isinstance(v, (date, datetime)):
            return v.strftime("%Y-%m-%d")
        clean = str(v).strip()
        try:
            parsed = datetime.strptime(clean, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Enrollment date '{v}' must be in YYYY-MM-DD format.")

    @field_validator("skills", mode="before")
    @classmethod
    def validate_skills(cls, v) -> List[str]:
        if isinstance(v, str):
            # Split comma-separated string if provided
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        return []


class StudentCreateModel(StudentBase):
    student_id: str = Field(..., min_length=3, max_length=20, description="Unique student ID")

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9_-]+$", clean):
            raise ValueError("Student ID must contain only alphanumeric characters, dashes, or underscores.")
        return clean


class StudentUpdateModel(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = None
    class_name: Optional[str] = Field(None, min_length=2, max_length=50)
    enrollment_date: Optional[str] = None
    skills: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if len(clean) < 2:
                raise ValueError("Student name must have at least 2 characters.")
            return clean
        return None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().lower()
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_regex, clean):
                raise ValueError(f"Invalid email format: '{v}'")
            return clean
        return None

    @field_validator("enrollment_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if isinstance(v, (date, datetime)):
                return v.strftime("%Y-%m-%d")
            clean = str(v).strip()
            try:
                parsed = datetime.strptime(clean, "%Y-%m-%d")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Date '{v}' must be in YYYY-MM-DD format.")
        return None


class StudentModel(StudentCreateModel):
    model_config = ConfigDict(extra="ignore")
