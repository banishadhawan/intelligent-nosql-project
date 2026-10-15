"""
Configuration module for IntelliTrack.
Loads environment variables and application-wide settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Config:
    """Application configuration parameters."""
    APP_NAME = "IntelliTrack"
    APP_SUBTITLE = "Intelligent Student Performance & Learning Analytics System"
    VERSION = "1.0.0"

    # MongoDB Settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "intellitrack")
    TEST_DATABASE = os.getenv("MONGODB_TEST_DATABASE", "intellitrack_test")

    # Academic & Analytics Thresholds
    PASS_MARKS_PERCENTAGE = float(os.getenv("PASS_MARKS_PERCENTAGE", 40.0))
    LOW_PERFORMANCE_THRESHOLD = float(os.getenv("LOW_PERFORMANCE_THRESHOLD", 50.0))
    LOW_ATTENDANCE_THRESHOLD = float(os.getenv("LOW_ATTENDANCE_THRESHOLD", 75.0))

    # Attendance Policy:
    # Present = 1.0
    # Late = 0.5 (configurable, standard academic half-credit)
    # Absent = 0.0
    LATE_ATTENDANCE_WEIGHT = float(os.getenv("LATE_ATTENDANCE_WEIGHT", 0.5))

    # Collections
    COLLECTION_STUDENTS = "students"
    COLLECTION_SUBJECTS = "subjects"
    COLLECTION_ASSESSMENTS = "assessments"
    COLLECTION_ATTENDANCE = "attendance"


config = Config()
