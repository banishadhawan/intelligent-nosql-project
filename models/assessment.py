"""
Assessment data models and validation schemas.
"""

from typing import Optional, Literal
from datetime import date, datetime
import re
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

ASSESSMENT_TYPES = ("Quiz", "Midterm", "Final Exam", "Assignment", "Project", "Lab")


class AssessmentBase(BaseModel):
    student_id: str = Field(..., min_length=2, max_length=20)
    subject_code: str = Field(..., min_length=2, max_length=20)
    assessment_name: str = Field(..., min_length=2, max_length=100)
    assessment_type: str = Field(..., description="Assessment category")
    marks: float = Field(..., ge=0.0, description="Marks obtained")
    max_marks: float = Field(..., gt=0.0, description="Maximum marks")
    assessment_date: str = Field(..., description="Date of assessment in YYYY-MM-DD format")
    remarks: Optional[str] = Field(default="", description="Optional feedback or notes")

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

    @field_validator("assessment_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Assessment name must have at least 2 characters.")
        return clean

    @field_validator("assessment_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().title()
        # Normalization
        type_map = {t.lower(): t for t in ASSESSMENT_TYPES}
        if clean.lower() in type_map:
            return type_map[clean.lower()]
        return clean

    @field_validator("assessment_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if isinstance(v, (date, datetime)):
            return v.strftime("%Y-%m-%d")
        clean = str(v).strip()
        try:
            parsed = datetime.strptime(clean, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Assessment date '{v}' must be in YYYY-MM-DD format.")

    @model_validator(mode="after")
    def validate_marks_within_maximum(self):
        if self.marks > self.max_marks:
            raise ValueError(f"Marks obtained ({self.marks}) cannot exceed maximum marks ({self.max_marks}).")
        return self

    @property
    def percentage(self) -> float:
        if self.max_marks > 0:
            return round((self.marks / self.max_marks) * 100.0, 2)
        return 0.0


class AssessmentCreateModel(AssessmentBase):
    assessment_id: str = Field(..., min_length=3, max_length=30, description="Unique assessment ID")

    @field_validator("assessment_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9_-]+$", clean):
            raise ValueError("Assessment ID must contain only alphanumeric characters, dashes, or underscores.")
        return clean


class AssessmentUpdateModel(BaseModel):
    assessment_name: Optional[str] = None
    assessment_type: Optional[str] = None
    marks: Optional[float] = Field(None, ge=0.0)
    max_marks: Optional[float] = Field(None, gt=0.0)
    assessment_date: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator("assessment_date")
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

    @model_validator(mode="after")
    def check_marks_consistency(self):
        if self.marks is not None and self.max_marks is not None:
            if self.marks > self.max_marks:
                raise ValueError(f"Marks obtained ({self.marks}) cannot exceed maximum marks ({self.max_marks}).")
        return self


class AssessmentModel(AssessmentCreateModel):
    model_config = ConfigDict(extra="ignore")
