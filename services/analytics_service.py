"""
Academic Analytics Service for IntelliTrack.
Implements 12 genuine, production-grade MongoDB aggregation pipelines using PyMongo.
All calculations operate dynamically on live collection data.
"""

import logging
from typing import Optional, List, Dict, Any
from pymongo.database import Database
from database.connection import get_database
from config import config

logger = logging.getLogger("intellitrack.services.analytics")


class AnalyticsService:

    # -------------------------------------------------------------------------
    # PIPELINE 1: Average Marks Percentage by Subject
    # Operators: $project, $divide, $multiply, $group, $avg, $sum, $lookup, $unwind, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_average_marks_by_subject(db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Calculates average marks percentage and total assessments conducted per subject.
        Joins with the subjects collection to fetch human-readable course titles.
        """
        database = db if db is not None else get_database()
        pipeline = [
            {
                "$project": {
                    "subject_code": 1,
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$subject_code",
                    "avg_percentage": {"$avg": "$marks_pct"},
                    "assessment_count": {"$sum": 1}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_SUBJECTS,
                    "localField": "_id",
                    "foreignField": "subject_code",
                    "as": "subject_info"
                }
            },
            {
                "$unwind": {
                    "path": "$subject_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "subject_code": "$_id",
                    "subject_name": {"$ifNull": ["$subject_info.subject_name", "$_id"]},
                    "avg_percentage": {"$round": ["$avg_percentage", 2]},
                    "assessment_count": 1
                }
            },
            {"$sort": {"avg_percentage": -1}}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 2: Average Performance by Academic Class
    # Operators: $lookup, $unwind, $project, $group, $addToSet, $size, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_average_performance_by_class(db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Calculates overall average score percentage, total assessments, and active student
        count partitioned across each enrolled academic class.
        """
        database = db if db is not None else get_database()
        pipeline = [
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "student_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$project": {
                    "class_name": "$student.class_name",
                    "student_id": "$student.student_id",
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$class_name",
                    "avg_percentage": {"$avg": "$marks_pct"},
                    "total_assessments": {"$sum": 1},
                    "students": {"$addToSet": "$student_id"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "class_name": "$_id",
                    "avg_percentage": {"$round": ["$avg_percentage", 2]},
                    "total_assessments": 1,
                    "student_count": {"$size": "$students"}
                }
            },
            {"$sort": {"avg_percentage": -1}}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 3: Top Students Based on Overall Mean Academic Performance
    # Operators: $project, $group, $lookup, $unwind, $round, $sort, $limit
    # -------------------------------------------------------------------------
    @staticmethod
    def get_top_students(limit: int = 10, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Returns top students ranked by their mean assessment percentage score across all subjects.
        """
        database = db if db is not None else get_database()
        pipeline = [
            {
                "$project": {
                    "student_id": 1,
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$student_id",
                    "overall_average": {"$avg": "$marks_pct"},
                    "assessment_count": {"$sum": 1}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$project": {
                    "_id": 0,
                    "student_id": "$_id",
                    "name": "$student.name",
                    "class_name": "$student.class_name",
                    "email": "$student.email",
                    "overall_average": {"$round": ["$overall_average", 2]},
                    "assessment_count": 1
                }
            },
            {"$sort": {"overall_average": -1, "assessment_count": -1}},
            {"$limit": limit}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 4: Pass Rate by Subject
    # Operators: $project, $cond, $group, $sum, $lookup, $unwind, $subtract, $divide, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_pass_rate_by_subject(
        pass_threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculates total attempts, passed exams, failed attempts, and pass rate % per subject.
        Uses configurable pass mark percentage (default from config).
        """
        database = db if db is not None else get_database()
        threshold = pass_threshold if pass_threshold is not None else config.PASS_MARKS_PERCENTAGE

        pipeline = [
            {
                "$project": {
                    "subject_code": 1,
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$project": {
                    "subject_code": 1,
                    "marks_pct": 1,
                    "is_pass": {
                        "$cond": [{"$gte": ["$marks_pct", threshold]}, 1, 0]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$subject_code",
                    "total_assessments": {"$sum": 1},
                    "passed_count": {"$sum": "$is_pass"},
                    "avg_percentage": {"$avg": "$marks_pct"}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_SUBJECTS,
                    "localField": "_id",
                    "foreignField": "subject_code",
                    "as": "subject_info"
                }
            },
            {
                "$unwind": {
                    "path": "$subject_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "subject_code": "$_id",
                    "subject_name": {"$ifNull": ["$subject_info.subject_name", "$_id"]},
                    "total_assessments": 1,
                    "passed_count": 1,
                    "failed_count": {"$subtract": ["$total_assessments", "$passed_count"]},
                    "pass_rate": {
                        "$round": [
                            {
                                "$multiply": [
                                    {"$divide": ["$passed_count", "$total_assessments"]},
                                    100
                                ]
                            },
                            2
                        ]
                    },
                    "avg_percentage": {"$round": ["$avg_percentage", 2]}
                }
            },
            {"$sort": {"pass_rate": -1}}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 5: Assessment Count and Average Marks by Subject and Assessment Type
    # Operators: $project, $group (compound key), $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_assessment_count_and_avg_by_subject(db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Breakdown of assessment count and average performance grouped by both
        subject and assessment type (e.g. Midterm, Quiz, Final Exam, Lab).
        """
        database = db if db is not None else get_database()
        pipeline = [
            {
                "$project": {
                    "subject_code": 1,
                    "assessment_type": 1,
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "subject_code": "$subject_code",
                        "assessment_type": "$assessment_type"
                    },
                    "count": {"$sum": 1},
                    "avg_percentage": {"$avg": "$marks_pct"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "subject_code": "$_id.subject_code",
                    "assessment_type": "$_id.assessment_type",
                    "count": 1,
                    "avg_percentage": {"$round": ["$avg_percentage", 2]}
                }
            },
            {"$sort": {"subject_code": 1, "assessment_type": 1}}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 6: Monthly Performance Trends
    # Operators: $project, $substrCP, $group, $avg, $sum, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_monthly_performance_trends(db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Aggregates chronological monthly academic metrics across the semester/year.
        Extracts YYYY-MM from assessment_date using $substrCP.
        """
        database = db if db is not None else get_database()
        pipeline = [
            {
                "$project": {
                    "month": {"$substrCP": ["$assessment_date", 0, 7]},
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$month",
                    "avg_percentage": {"$avg": "$marks_pct"},
                    "total_assessments": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "month": "$_id",
                    "avg_percentage": {"$round": ["$avg_percentage", 2]},
                    "total_assessments": 1
                }
            },
            {"$sort": {"month": 1}}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 7: Attendance Percentage Per Student (Applying Late Policy)
    # Operators: $project, $switch, $group, $lookup, $unwind, $multiply, $divide, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_attendance_percentage_per_student(
        late_weight: Optional[float] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Computes accurate student attendance rates applying the standardized Late weight
        (Present = 1.0, Late = late_weight (0.5), Absent = 0.0).
        """
        database = db if db is not None else get_database()
        weight = late_weight if late_weight is not None else config.LATE_ATTENDANCE_WEIGHT

        pipeline = [
            {
                "$project": {
                    "student_id": 1,
                    "status": 1,
                    "weighted_score": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$status", "Present"]}, "then": 1.0},
                                {"case": {"$eq": ["$status", "Late"]}, "then": weight}
                            ],
                            "default": 0.0
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$student_id",
                    "total_sessions": {"$sum": 1},
                    "weighted_sum": {"$sum": "$weighted_score"},
                    "present_count": {"$sum": {"$cond": [{"$eq": ["$status", "Present"]}, 1, 0]}},
                    "late_count": {"$sum": {"$cond": [{"$eq": ["$status", "Late"]}, 1, 0]}},
                    "absent_count": {"$sum": {"$cond": [{"$eq": ["$status", "Absent"]}, 1, 0]}}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {
                "$unwind": {
                    "path": "$student",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "student_id": "$_id",
                    "name": {"$ifNull": ["$student.name", "$_id"]},
                    "class_name": {"$ifNull": ["$student.class_name", "N/A"]},
                    "total_sessions": 1,
                    "present_count": 1,
                    "late_count": 1,
                    "absent_count": 1,
                    "attendance_percentage": {
                        "$round": [
                            {
                                "$multiply": [
                                    {"$divide": ["$weighted_sum", "$total_sessions"]},
                                    100
                                ]
                            },
                            2
                        ]
                    }
                }
            },
            {"$sort": {"attendance_percentage": -1}}
        ]
        return list(database[config.COLLECTION_ATTENDANCE].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 8: Attendance Distribution by Status
    # Operators: $group, $sum, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_attendance_distribution_by_status(db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Total breakdown of attendance records categorized into Present, Absent, and Late.
        """
        database = db if db is not None else get_database()
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "status": "$_id",
                    "count": 1
                }
            },
            {"$sort": {"count": -1}}
        ]
        return list(database[config.COLLECTION_ATTENDANCE].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 9: Students with Low Average Marks
    # Operators: $project, $group, $match, $lookup, $unwind, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_students_with_low_marks(
        threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Finds all students whose average assessment percentage falls below the specified threshold.
        """
        database = db if db is not None else get_database()
        cut_off = threshold if threshold is not None else config.LOW_PERFORMANCE_THRESHOLD

        pipeline = [
            {
                "$project": {
                    "student_id": 1,
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$student_id",
                    "overall_average": {"$avg": "$marks_pct"},
                    "assessment_count": {"$sum": 1}
                }
            },
            {
                "$match": {
                    "overall_average": {"$lt": cut_off}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$project": {
                    "_id": 0,
                    "student_id": "$_id",
                    "name": "$student.name",
                    "email": "$student.email",
                    "class_name": "$student.class_name",
                    "overall_average": {"$round": ["$overall_average", 2]},
                    "assessment_count": 1
                }
            },
            {"$sort": {"overall_average": 1}}
        ]
        return list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 10: Students with Low Attendance
    # Operators: $project, $switch, $group, $match, $lookup, $unwind, $round, $sort
    # -------------------------------------------------------------------------
    @staticmethod
    def get_students_with_low_attendance(
        threshold: Optional[float] = None,
        late_weight: Optional[float] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Finds all students whose weighted attendance percentage falls below the low attendance threshold.
        """
        database = db if db is not None else get_database()
        cut_off = threshold if threshold is not None else config.LOW_ATTENDANCE_THRESHOLD
        weight = late_weight if late_weight is not None else config.LATE_ATTENDANCE_WEIGHT

        pipeline = [
            {
                "$project": {
                    "student_id": 1,
                    "status": 1,
                    "weighted_score": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$status", "Present"]}, "then": 1.0},
                                {"case": {"$eq": ["$status", "Late"]}, "then": weight}
                            ],
                            "default": 0.0
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$student_id",
                    "total_sessions": {"$sum": 1},
                    "weighted_sum": {"$sum": "$weighted_score"},
                    "absent_count": {"$sum": {"$cond": [{"$eq": ["$status", "Absent"]}, 1, 0]}}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "total_sessions": 1,
                    "absent_count": 1,
                    "attendance_percentage": {
                        "$multiply": [
                            {"$divide": ["$weighted_sum", "$total_sessions"]},
                            100
                        ]
                    }
                }
            },
            {
                "$match": {
                    "attendance_percentage": {"$lt": cut_off}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$project": {
                    "_id": 0,
                    "student_id": "$_id",
                    "name": "$student.name",
                    "email": "$student.email",
                    "class_name": "$student.class_name",
                    "total_sessions": 1,
                    "absent_count": 1,
                    "attendance_percentage": {"$round": ["$attendance_percentage", 2]}
                }
            },
            {"$sort": {"attendance_percentage": 1}}
        ]
        return list(database[config.COLLECTION_ATTENDANCE].aggregate(pipeline))

    # -------------------------------------------------------------------------
    # PIPELINE 11: Declining Performance Across Chronological Assessments
    # Operators: $sort, $project, $group ($push), $match, $lookup, $unwind
    # -------------------------------------------------------------------------
    @staticmethod
    def get_declining_students(
        min_assessments: int = 3,
        decline_threshold: float = -5.0,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects students with a demonstrable downward trajectory across chronological assessments.
        Pushes sorted assessments into an array, computes recent vs baseline scores,
        and flags students with a delta <= decline_threshold.
        """
        database = db if db is not None else get_database()
        pipeline = [
            {"$sort": {"student_id": 1, "assessment_date": 1}},
            {
                "$project": {
                    "student_id": 1,
                    "assessment_date": 1,
                    "subject_code": 1,
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$student_id",
                    "assessment_history": {
                        "$push": {
                            "date": "$assessment_date",
                            "subject": "$subject_code",
                            "pct": "$marks_pct"
                        }
                    },
                    "total_count": {"$sum": 1}
                }
            },
            {
                "$match": {
                    "total_count": {"$gte": min_assessments}
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"}
        ]

        raw_results = list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))
        declining_list = []

        for item in raw_results:
            history = item["assessment_history"]
            # Divide chronological history into initial half and recent half
            split_idx = max(1, len(history) // 2)
            initial_scores = [h["pct"] for h in history[:split_idx]]
            recent_scores = [h["pct"] for h in history[split_idx:]]

            if not initial_scores or not recent_scores:
                continue

            initial_avg = sum(initial_scores) / len(initial_scores)
            recent_avg = sum(recent_scores) / len(recent_scores)
            delta = round(recent_avg - initial_avg, 2)

            if delta <= decline_threshold:
                declining_list.append({
                    "student_id": item["_id"],
                    "name": item["student"]["name"],
                    "class_name": item["student"]["class_name"],
                    "initial_average": round(initial_avg, 2),
                    "recent_average": round(recent_avg, 2),
                    "score_drop": round(abs(delta), 2),
                    "assessment_count": item["total_count"]
                })

        # Sort by biggest drop
        declining_list.sort(key=lambda x: x["score_drop"], reverse=True)
        return declining_list

    # -------------------------------------------------------------------------
    # PIPELINE 12: Class-Level Multidimensional Performance Comparison
    # Combines marks average, pass rate, and attendance rate across classes.
    # -------------------------------------------------------------------------
    @staticmethod
    def get_class_level_performance_comparison(
        pass_threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Multidimensional class comparison synthesizing assessment average, pass rate,
        and average attendance percentage.
        """
        database = db if db is not None else get_database()
        threshold = pass_threshold if pass_threshold is not None else config.PASS_MARKS_PERCENTAGE

        # Step A: Class Marks & Pass Rate via Aggregation
        marks_pipeline = [
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "student_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$project": {
                    "class_name": "$student.class_name",
                    "marks_pct": {
                        "$multiply": [
                            {"$divide": ["$marks", "$max_marks"]},
                            100
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$class_name",
                    "avg_marks": {"$avg": "$marks_pct"},
                    "total_assessments": {"$sum": 1},
                    "passed": {
                        "$sum": {
                            "$cond": [{"$gte": ["$marks_pct", threshold]}, 1, 0]
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "class_name": "$_id",
                    "avg_marks": {"$round": ["$avg_marks", 2]},
                    "total_assessments": 1,
                    "pass_rate": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$passed", "$total_assessments"]}, 100]},
                            2
                        ]
                    }
                }
            }
        ]
        marks_data = {row["class_name"]: row for row in database[config.COLLECTION_ASSESSMENTS].aggregate(marks_pipeline)}

        # Step B: Class Attendance via Aggregation
        att_pipeline = [
            {
                "$lookup": {
                    "from": config.COLLECTION_STUDENTS,
                    "localField": "student_id",
                    "foreignField": "student_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$project": {
                    "class_name": "$student.class_name",
                    "weighted_score": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$status", "Present"]}, "then": 1.0},
                                {"case": {"$eq": ["$status", "Late"]}, "then": config.LATE_ATTENDANCE_WEIGHT}
                            ],
                            "default": 0.0
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$class_name",
                    "total_attendance": {"$sum": 1},
                    "weighted_sum": {"$sum": "$weighted_score"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "class_name": "$_id",
                    "avg_attendance": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$weighted_sum", "$total_attendance"]}, 100]},
                            2
                        ]
                    }
                }
            }
        ]
        att_data = {row["class_name"]: row["avg_attendance"] for row in database[config.COLLECTION_ATTENDANCE].aggregate(att_pipeline)}

        # Merge class summaries
        all_classes = sorted(list(set(list(marks_data.keys()) + list(att_data.keys()))))
        comparison = []
        for c in all_classes:
            m = marks_data.get(c, {})
            comparison.append({
                "class_name": c,
                "avg_marks": m.get("avg_marks", 0.0),
                "pass_rate": m.get("pass_rate", 0.0),
                "total_assessments": m.get("total_assessments", 0),
                "avg_attendance": att_data.get(c, 0.0)
            })
        return comparison

    # -------------------------------------------------------------------------
    # SYSTEM-WIDE KPIS & EXECUTIVE SUMMARY
    # -------------------------------------------------------------------------
    @staticmethod
    def get_system_kpis(
        pass_threshold: Optional[float] = None,
        low_perf_threshold: Optional[float] = None,
        low_att_threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        """
        Computes high-level KPIs for the home dashboard from live database collections.
        """
        database = db if db is not None else get_database()
        p_thresh = pass_threshold if pass_threshold is not None else config.PASS_MARKS_PERCENTAGE
        lp_thresh = low_perf_threshold if low_perf_threshold is not None else config.LOW_PERFORMANCE_THRESHOLD
        la_thresh = low_att_threshold if low_att_threshold is not None else config.LOW_ATTENDANCE_THRESHOLD

        total_students = database[config.COLLECTION_STUDENTS].count_documents({})
        total_subjects = database[config.COLLECTION_SUBJECTS].count_documents({})
        total_assessments = database[config.COLLECTION_ASSESSMENTS].count_documents({})
        total_attendance = database[config.COLLECTION_ATTENDANCE].count_documents({})

        # Overall average marks & pass rate
        overall_marks_avg = 0.0
        pass_rate = 0.0
        if total_assessments > 0:
            avg_pipe = [
                {
                    "$project": {
                        "pct": {"$multiply": [{"$divide": ["$marks", "$max_marks"]}, 100]}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "overall_avg": {"$avg": "$pct"},
                        "passed": {"$sum": {"$cond": [{"$gte": ["$pct", p_thresh]}, 1, 0]}}
                    }
                }
            ]
            res = list(database[config.COLLECTION_ASSESSMENTS].aggregate(avg_pipe))
            if res:
                overall_marks_avg = round(res[0].get("overall_avg", 0.0), 2)
                pass_rate = round((res[0].get("passed", 0) / total_assessments) * 100.0, 2)

        # Overall attendance percentage
        overall_attendance_pct = 0.0
        if total_attendance > 0:
            att_pipe = [
                {
                    "$project": {
                        "score": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$status", "Present"]}, "then": 1.0},
                                    {"case": {"$eq": ["$status", "Late"]}, "then": config.LATE_ATTENDANCE_WEIGHT}
                                ],
                                "default": 0.0
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "weighted": {"$sum": "$score"}
                    }
                }
            ]
            res = list(database[config.COLLECTION_ATTENDANCE].aggregate(att_pipe))
            if res and res[0]["total"] > 0:
                overall_attendance_pct = round((res[0]["weighted"] / res[0]["total"]) * 100.0, 2)

        # Count of students requiring academic support (at-risk)
        low_marks_students = AnalyticsService.get_students_with_low_marks(threshold=lp_thresh, db=database)
        low_att_students = AnalyticsService.get_students_with_low_attendance(threshold=la_thresh, db=database)
        declining_students = AnalyticsService.get_declining_students(db=database)

        at_risk_ids = set([s["student_id"] for s in low_marks_students] +
                          [s["student_id"] for s in low_att_students] +
                          [s["student_id"] for s in declining_students])

        return {
            "total_students": total_students,
            "total_subjects": total_subjects,
            "total_assessments": total_assessments,
            "total_attendance": total_attendance,
            "overall_marks_avg": overall_marks_avg,
            "overall_attendance_pct": overall_attendance_pct,
            "pass_rate": pass_rate,
            "at_risk_count": len(at_risk_ids),
        }
