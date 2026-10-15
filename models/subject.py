"""
Subject data models and validation schemas.
"""

from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SubjectBase(BaseModel):
    subject_name: str = Field(..., min_length=2, max_length=100, description="Full subject name")
    description: str = Field(default="", description="Subject description and topics covered")
    credits: int = Field(..., ge=1, le=10, description="Credit hours (1-10)")
    class_name: str = Field(..., min_length=2, max_length=50, description="Class or section name")

    @field_validator("subject_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Subject name must have at least 2 characters.")
        return clean

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Class name cannot be empty.")
        return clean


class SubjectCreateModel(SubjectBase):
    subject_code: str = Field(..., min_length=2, max_length=20, description="Unique subject code (e.g., CS301)")

    @field_validator("subject_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9_-]+$", clean):
            raise ValueError("Subject code must contain only alphanumeric characters, dashes, or underscores.")
        return clean


class SubjectUpdateModel(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=10)
    class_name: Optional[str] = Field(None, min_length=2, max_length=50)

    @field_validator("subject_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if len(clean) < 2:
                raise ValueError("Subject name must have at least 2 characters.")
            return clean
        return None


class SubjectModel(SubjectCreateModel):
    model_config = ConfigDict(extra="ignore")
