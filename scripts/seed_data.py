"""
Seed Data Generator for IntelliTrack.
Generates an original, reproducible, and academically realistic fictional dataset:
- ~150 Students across 4 academic departments
- 8 Core Subjects
- ~750 Assessment records (mix of high, average, at-risk, and declining trajectories)
- ~3,300 Attendance records (with Present, Late, and Absent distributions)
Uses a fixed random seed (42) for deterministic reproducibility.
"""

import sys
import os
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.connection import get_database
from database.indexes import create_all_indexes
from database.validators import apply_collection_validators
from config import config

FIRST_NAMES = [
    "Aarav", "Diya", "Rohan", "Ananya", "Vikram", "Sneha", "Rahul", "Priya",
    "Aditya", "Ishita", "Arjun", "Kavya", "Siddharth", "Meera", "Kabir", "Neha",
    "Ayush", "Tanvi", "Dev", "Riya", "Karan", "Shreya", "Varun", "Pooja",
    "Manish", "Swati", "Nikhil", "Simran", "Gaurav", "Nandini", "Yash", "Bhavna",
    "Amit", "Divya", "Rajesh", "Aishwarya", "Deepak", "Ritu", "Harsh", "Sakshi",
    "Pranav", "Anjali", "Tarun", "Komal", "Mayank", "Preeti", "Suresh", "Sunita",
    "Sameer", "Geeta", "Akash", "Monika", "Alok", "Rashmi", "Sanjay", "Anu"
]

LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Iyer", "Malhotra", "Nair", "Mehta", "Sen",
    "Gupta", "Reddy", "Chopra", "Joshi", "Bose", "Kulkarni", "Das", "Menon",
    "Singhania", "Bhatia", "Deshmukh", "Kapoor", "Chatterjee", "Mishra", "Pandey",
    "Saxena", "Agarwal", "Bhardwaj", "Trivedi", "Banerjee", "Chauhan", "Rao"
]

SKILLS_POOL = [
    "Python", "MongoDB", "SQL", "Streamlit", "Pandas", "Plotly", "Machine Learning",
    "Data Structures", "Web Development", "Git", "Docker", "FastAPI", "React", "Cloud Computing"
]

CLASSES = [
    "BTech-CSE-A",
    "BTech-CSE-B",
    "BTech-AI-A",
    "BTech-DS-A"
]

SUBJECTS_CONFIG = [
    {
        "subject_code": "CS301",
        "subject_name": "Intelligent NoSQL Databases",
        "description": "Document databases, aggregation pipelines, schema modeling, and PyMongo analytics.",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    },
    {
        "subject_code": "CS302",
        "subject_name": "Data Structures & Algorithms",
        "description": "Advanced trees, graphs, dynamic programming, and complexity analysis.",
        "credits": 4,
        "class_name": "BTech-CSE-A"
    },
    {
        "subject_code": "CS303",
        "subject_name": "Modern Web Application Engineering",
        "description": "Full-stack architectures, RESTful APIs, state management, and modern frontends.",
        "credits": 3,
        "class_name": "BTech-CSE-B"
    },
    {
        "subject_code": "CS304",
        "subject_name": "Operating Systems & Concurrency",
        "description": "Process scheduling, thread synchronization, memory management, and virtualization.",
        "credits": 4,
        "class_name": "BTech-CSE-B"
    },
    {
        "subject_code": "AI301",
        "subject_name": "Machine Learning Foundations",
        "description": "Supervised, unsupervised algorithms, model evaluation, and regression models.",
        "credits": 4,
        "class_name": "BTech-AI-A"
    },
    {
        "subject_code": "AI302",
        "subject_name": "Natural Language Processing",
        "description": "Text vectorization, tokenization, transformer architectures, and sentiment analysis.",
        "credits": 3,
        "class_name": "BTech-AI-A"
    },
    {
        "subject_code": "DS301",
        "subject_name": "Big Data Engineering & Analytics",
        "description": "Distributed data processing, Spark fundamentals, and ETL pipeline design.",
        "credits": 4,
        "class_name": "BTech-DS-A"
    },
    {
        "subject_code": "DS302",
        "subject_name": "Applied Data Visualization & Storytelling",
        "description": "Interactive visual dashboards, exploratory data analysis, and Plotly graphics.",
        "credits": 3,
        "class_name": "BTech-DS-A"
    }
]

ASSESSMENT_TEMPLATES = [
    {"name": "Diagnostic Quiz", "type": "Quiz", "max_marks": 25, "day_offset": 15},
    {"name": "Lab Practical Assignment", "type": "Lab", "max_marks": 30, "day_offset": 30},
    {"name": "Midterm Examination", "type": "Midterm", "max_marks": 50, "day_offset": 50},
    {"name": "Mini Project Presentation", "type": "Project", "max_marks": 40, "day_offset": 70},
    {"name": "Comprehensive Final Exam", "type": "Final Exam", "max_marks": 100, "day_offset": 90}
]


def seed_database(
    student_count: int = 150,
    reset: bool = False,
    demo: bool = False,
    seed_value: int = 42,
    db_name: str = None
):
    """
    Seeds the MongoDB database with reproducible fictional academic records.
    """
    random.seed(seed_value)
    db = get_database(db_name)

    print(f"=== IntelliTrack Data Seeder ===")
    print(f"Target Database: {db.name}")

    if demo:
        student_count = 30
        print("[Demo Mode] Generating smaller dataset (30 students).")
    else:
        print(f"[Full Mode] Generating standard dataset ({student_count} students).")

    if reset:
        print("Clearing existing collections as requested (--reset)...")
        db[config.COLLECTION_STUDENTS].delete_many({})
        db[config.COLLECTION_SUBJECTS].delete_many({})
        db[config.COLLECTION_ASSESSMENTS].delete_many({})
        db[config.COLLECTION_ATTENDANCE].delete_many({})
        print("Collections cleared.")

    # 1. Apply Schema Validators & Create Indexes
    print("Applying schema validators and creating MongoDB indexes...")
    apply_collection_validators(db)
    create_all_indexes(db)

    # 2. Seed Subjects
    print(f"Seeding {len(SUBJECTS_CONFIG)} subjects...")
    for sub in SUBJECTS_CONFIG:
        db[config.COLLECTION_SUBJECTS].update_one(
            {"subject_code": sub["subject_code"]},
            {"$set": sub},
            upsert=True
        )

    # Map classes to subjects for realistic course enrollment
    class_subject_map = {}
    for sub in SUBJECTS_CONFIG:
        c = sub["class_name"]
        class_subject_map.setdefault(c, []).append(sub["subject_code"])

    # 3. Seed Students
    print(f"Generating {student_count} students...")
    student_docs = []
    student_profiles = {}  # student_id -> profile category: 'high', 'average', 'at_risk', 'declining'

    # Stratify profiles
    # 20% High, 55% Average, 15% At-Risk, 10% Declining Trajectory
    high_count = int(student_count * 0.20)
    at_risk_count = int(student_count * 0.15)
    declining_count = int(student_count * 0.10)
    avg_count = student_count - high_count - at_risk_count - declining_count

    profile_categories = (
        ["high"] * high_count +
        ["average"] * avg_count +
        ["at_risk"] * at_risk_count +
        ["declining"] * declining_count
    )
    random.shuffle(profile_categories)

    start_date = datetime(2026, 8, 1)

    for i in range(1, student_count + 1):
        stu_id = f"STU{1000 + i}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}{i}@campus.edu"
        assigned_class = CLASSES[(i - 1) % len(CLASSES)]
        enrollment_date = (start_date + timedelta(days=random.randint(0, 10))).strftime("%Y-%m-%d")
        skills = random.sample(SKILLS_POOL, k=random.randint(2, 5))

        profile_cat = profile_categories[i - 1]
        student_profiles[stu_id] = profile_cat

        doc = {
            "student_id": stu_id,
            "name": full_name,
            "email": email,
            "class_name": assigned_class,
            "enrollment_date": enrollment_date,
            "skills": skills
        }
        student_docs.append(doc)
        db[config.COLLECTION_STUDENTS].update_one(
            {"student_id": stu_id},
            {"$set": doc},
            upsert=True
        )

    print(f"Students successfully seeded ({len(student_docs)} total).")

    # 4. Seed Assessments
    print("Generating assessment records...")
    assessment_docs = []
    asm_counter = 1000
    semester_start = datetime(2026, 8, 15)

    for stu in student_docs:
        stu_id = stu["student_id"]
        stu_class = stu["class_name"]
        profile = student_profiles[stu_id]
        enrolled_subjects = class_subject_map.get(stu_class, [])

        for sub_code in enrolled_subjects:
            for tmpl_idx, tmpl in enumerate(ASSESSMENT_TEMPLATES):
                asm_counter += 1
                asm_id = f"ASM{asm_counter}"
                asm_date = (semester_start + timedelta(days=tmpl["day_offset"] + random.randint(-2, 2))).strftime("%Y-%m-%d")
                max_marks = tmpl["max_marks"]

                # Generate marks according to academic profile
                if profile == "high":
                    pct = random.uniform(80.0, 98.0)
                elif profile == "average":
                    pct = random.uniform(55.0, 78.0)
                elif profile == "at_risk":
                    pct = random.uniform(25.0, 48.0)
                elif profile == "declining":
                    # Chronological decline: starts strong (80-88%), then drops to (30-45%)
                    progress_ratio = tmpl_idx / (len(ASSESSMENT_TEMPLATES) - 1)
                    pct = 85.0 - (progress_ratio * 45.0) + random.uniform(-4, 4)
                    pct = max(20.0, min(95.0, pct))
                else:
                    pct = random.uniform(50.0, 80.0)

                raw_marks = round((pct / 100.0) * max_marks, 1)
                raw_marks = min(raw_marks, float(max_marks))

                doc = {
                    "assessment_id": asm_id,
                    "student_id": stu_id,
                    "subject_code": sub_code,
                    "assessment_name": f"{tmpl['name']} - {sub_code}",
                    "assessment_type": tmpl["type"],
                    "marks": raw_marks,
                    "max_marks": max_marks,
                    "assessment_date": asm_date,
                    "percentage": round((raw_marks / max_marks) * 100.0, 2),
                    "remarks": f"Academic standing: {profile.replace('_', ' ').title()}"
                }
                assessment_docs.append(doc)

    print(f"Inserting {len(assessment_docs)} assessment records into MongoDB...")
    # Safe upsert / insert
    for a in assessment_docs:
        db[config.COLLECTION_ASSESSMENTS].update_one(
            {"assessment_id": a["assessment_id"]},
            {"$set": a},
            upsert=True
        )
    print(f"Assessments successfully seeded.")

    # 5. Seed Attendance
    print("Generating attendance records (sampling across 22 lecture dates per course)...")
    attendance_docs = []
    # 22 lecture dates across August to November 2026
    lecture_dates = []
    curr_date = datetime(2026, 8, 18)
    while len(lecture_dates) < 22:
        if curr_date.weekday() < 5:  # Monday to Friday
            lecture_dates.append(curr_date.strftime("%Y-%m-%d"))
        curr_date += timedelta(days=random.choice([2, 3, 4]))

    for stu in student_docs:
        stu_id = stu["student_id"]
        stu_class = stu["class_name"]
        profile = student_profiles[stu_id]
        enrolled_subjects = class_subject_map.get(stu_class, [])

        for sub_code in enrolled_subjects:
            for d in lecture_dates:
                # Determine status distribution based on profile
                if profile == "high":
                    status = random.choices(["Present", "Late", "Absent"], weights=[92, 6, 2])[0]
                elif profile == "average":
                    status = random.choices(["Present", "Late", "Absent"], weights=[80, 12, 8])[0]
                elif profile == "at_risk":
                    status = random.choices(["Present", "Late", "Absent"], weights=[55, 15, 30])[0]
                elif profile == "declining":
                    # Attendance also drops over time for declining profile
                    status = random.choices(["Present", "Late", "Absent"], weights=[65, 15, 20])[0]
                else:
                    status = random.choices(["Present", "Late", "Absent"], weights=[80, 10, 10])[0]

                doc = {
                    "student_id": stu_id,
                    "subject_code": sub_code,
                    "attendance_date": d,
                    "status": status,
                    "remarks": ""
                }
                attendance_docs.append(doc)

    print(f"Inserting {len(attendance_docs)} attendance records into MongoDB...")
    # Bulk insert for speed
    # Delete existing attendance for these students first if not reset
    if not reset:
        db[config.COLLECTION_ATTENDANCE].delete_many({
            "student_id": {"$in": [s["student_id"] for s in student_docs]}
        })
    db[config.COLLECTION_ATTENDANCE].insert_many(attendance_docs)
    print(f"Attendance successfully seeded ({len(attendance_docs)} records).")

    print("\n=== Dataset Seeding Complete ===")
    print(f"Registered Students: {db[config.COLLECTION_STUDENTS].count_documents({})}")
    print(f"Enrolled Subjects:   {db[config.COLLECTION_SUBJECTS].count_documents({})}")
    print(f"Assessments Logged:  {db[config.COLLECTION_ASSESSMENTS].count_documents({})}")
    print(f"Attendance Recorded: {db[config.COLLECTION_ATTENDANCE].count_documents({})}")
    print("Ready for live analytics execution!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IntelliTrack Reproducible Fictional Academic Dataset Generator")
    parser.add_argument("--reset", action="store_true", help="Reset and clear existing project collections before seeding")
    parser.add_argument("--demo", action="store_true", help="Generate smaller demo dataset (30 students)")
    parser.add_argument("--students", type=int, default=150, help="Number of students to generate (default: 150)")
    parser.add_argument("--seed", type=int, default=42, help="Random generator seed for exact reproducibility (default: 42)")

    args = parser.parse_args()

    if args.reset:
        confirm = input("Are you sure you want to delete all existing data in IntelliTrack? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Reset aborted by user.")
            sys.exit(0)

    seed_database(student_count=args.students, reset=args.reset, demo=args.demo, seed_value=args.seed)
