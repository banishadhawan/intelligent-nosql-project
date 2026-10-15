"""
Intelligent Learning Insights Service for IntelliTrack.
Implements explainable, evidence-backed, rules-based educational analytics:
- Multi-factor At-Risk Student Detection
- Chronological Performance Trend Analysis
- Subject-Specific Weakness Diagnosis
- Tailored Actionable Learning Recommendations
- Classroom Strengths and Vulnerabilities
"""

import logging
from typing import Optional, List, Dict, Any
from pymongo.database import Database
from database.connection import get_database
from services.analytics_service import AnalyticsService
from config import config

logger = logging.getLogger("intellitrack.services.insights")


class InsightsService:

    @staticmethod
    def get_at_risk_students(
        low_perf_threshold: Optional[float] = None,
        low_att_threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects and classifies students requiring academic support based on
        low marks, low attendance, and declining performance trajectories.
        Every flag provides transparent, empirical evidence.
        """
        database = db if db is not None else get_database()
        perf_thresh = low_perf_threshold if low_perf_threshold is not None else config.LOW_PERFORMANCE_THRESHOLD
        att_thresh = low_att_threshold if low_att_threshold is not None else config.LOW_ATTENDANCE_THRESHOLD

        # Fetch underlying aggregation datasets
        low_marks_data = {
            s["student_id"]: s for s in AnalyticsService.get_students_with_low_marks(threshold=perf_thresh, db=database)
        }
        low_att_data = {
            s["student_id"]: s for s in AnalyticsService.get_students_with_low_attendance(threshold=att_thresh, db=database)
        }
        declining_data = {
            s["student_id"]: s for s in AnalyticsService.get_declining_students(db=database)
        }

        # Unique union of all flagged students
        flagged_ids = set(list(low_marks_data.keys()) + list(low_att_data.keys()) + list(declining_data.keys()))

        at_risk_report = []
        for stu_id in flagged_ids:
            reasons = []
            risk_points = 0

            # 1. Check Marks
            marks_info = low_marks_data.get(stu_id)
            marks_avg = marks_info["overall_average"] if marks_info else None
            if marks_info:
                reasons.append(f"Low Academic Performance: Average score is {marks_avg}% (Below threshold {perf_thresh}%)")
                risk_points += 2
                if marks_avg < (perf_thresh - 15):
                    risk_points += 1

            # 2. Check Attendance
            att_info = low_att_data.get(stu_id)
            att_pct = att_info["attendance_percentage"] if att_info else None
            if att_info:
                reasons.append(f"Low Class Attendance: Attendance is {att_pct}% (Below required {att_thresh}%)")
                risk_points += 2
                if att_pct < (att_thresh - 15):
                    risk_points += 1

            # 3. Check Trajectory / Decline
            dec_info = declining_data.get(stu_id)
            score_drop = dec_info["score_drop"] if dec_info else None
            if dec_info:
                reasons.append(
                    f"Declining Academic Trajectory: Performance dropped by {score_drop}% "
                    f"(from {dec_info['initial_average']}% down to {dec_info['recent_average']}%)"
                )
                risk_points += 1

            # Determine Risk Tier
            if risk_points >= 4:
                tier = "Critical Risk"
                badge_color = "red"
            elif risk_points >= 2:
                tier = "Moderate Risk"
                badge_color = "orange"
            else:
                tier = "Early Warning"
                badge_color = "blue"

            # Get student basic profile
            any_source = marks_info or att_info or dec_info
            name = any_source.get("name", stu_id) if any_source else stu_id
            class_name = any_source.get("class_name", "N/A") if any_source else "N/A"

            at_risk_report.append({
                "student_id": stu_id,
                "name": name,
                "class_name": class_name,
                "risk_tier": tier,
                "badge_color": badge_color,
                "risk_points": risk_points,
                "reasons": reasons,
                "marks_avg": marks_avg,
                "attendance_pct": att_pct,
                "score_drop": score_drop
            })

        # Sort: highest risk points first, then lowest marks
        at_risk_report.sort(key=lambda x: (x["risk_points"], -(x["marks_avg"] or 100)), reverse=True)
        return at_risk_report

    @staticmethod
    def get_student_diagnostic(
        student_id: str,
        pass_threshold: Optional[float] = None,
        low_perf_threshold: Optional[float] = None,
        low_att_threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive diagnostic report for an individual student:
        - Subject strengths and weaknesses
        - Chronological trend analysis
        - Attendance audit
        - Explainable recommendations
        """
        database = db if db is not None else get_database()
        clean_id = student_id.strip().upper()
        p_thresh = pass_threshold if pass_threshold is not None else config.PASS_MARKS_PERCENTAGE
        lp_thresh = low_perf_threshold if low_perf_threshold is not None else config.LOW_PERFORMANCE_THRESHOLD
        la_thresh = low_att_threshold if low_att_threshold is not None else config.LOW_ATTENDANCE_THRESHOLD

        # 1. Fetch Student Profile
        student = database[config.COLLECTION_STUDENTS].find_one({"student_id": clean_id})
        if not student:
            return {"error": f"Student '{clean_id}' not found."}

        # 2. Subject Breakdown via Aggregation
        sub_pipeline = [
            {"$match": {"student_id": clean_id}},
            {
                "$project": {
                    "subject_code": 1,
                    "marks_pct": {
                        "$multiply": [{"$divide": ["$marks", "$max_marks"]}, 100]
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
            {"$unwind": {"path": "$subject_info", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "subject_code": "$_id",
                    "subject_name": {"$ifNull": ["$subject_info.subject_name", "$_id"]},
                    "avg_percentage": {"$round": ["$avg_percentage", 2]},
                    "assessment_count": 1
                }
            },
            {"$sort": {"avg_percentage": 1}}
        ]
        subject_breakdown = list(database[config.COLLECTION_ASSESSMENTS].aggregate(sub_pipeline))

        weak_subjects = []
        strong_subjects = []
        for s in subject_breakdown:
            if s["avg_percentage"] < lp_thresh:
                weak_subjects.append(s)
            elif s["avg_percentage"] >= 75.0:
                strong_subjects.append(s)

        # 3. Chronological Performance Trend
        assessments_cursor = database[config.COLLECTION_ASSESSMENTS].find({"student_id": clean_id}).sort("assessment_date", 1)
        chronological_assessments = []
        for a in assessments_cursor:
            pct = round((a["marks"] / a["max_marks"]) * 100.0, 2)
            chronological_assessments.append({
                "assessment_id": a["assessment_id"],
                "assessment_name": a["assessment_name"],
                "subject_code": a["subject_code"],
                "assessment_date": a["assessment_date"],
                "percentage": pct
            })

        trend_status = "Insufficient Data"
        trend_delta = 0.0
        if len(chronological_assessments) >= 3:
            mid = len(chronological_assessments) // 2
            initial_avg = sum([x["percentage"] for x in chronological_assessments[:mid]]) / mid
            recent_avg = sum([x["percentage"] for x in chronological_assessments[mid:]]) / (len(chronological_assessments) - mid)
            trend_delta = round(recent_avg - initial_avg, 2)
            if trend_delta <= -5.0:
                trend_status = f"Declining (Dropped by {abs(trend_delta)}%)"
            elif trend_delta >= 5.0:
                trend_status = f"Improving (Gained +{trend_delta}%)"
            else:
                trend_status = f"Stable (Delta: {trend_delta:+}%)"
        elif len(chronological_assessments) > 0:
            trend_status = "Baseline (1-2 Assessments Conducted)"

        # 4. Attendance Metrics
        att_pipeline = [
            {"$match": {"student_id": clean_id}},
            {
                "$project": {
                    "status": 1,
                    "weighted": {
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
                    "weighted_sum": {"$sum": "$weighted"},
                    "present": {"$sum": {"$cond": [{"$eq": ["$status", "Present"]}, 1, 0]}},
                    "late": {"$sum": {"$cond": [{"$eq": ["$status", "Late"]}, 1, 0]}},
                    "absent": {"$sum": {"$cond": [{"$eq": ["$status", "Absent"]}, 1, 0]}}
                }
            }
        ]
        att_res = list(database[config.COLLECTION_ATTENDANCE].aggregate(att_pipeline))
        attendance_stats = {
            "total": 0,
            "present": 0,
            "late": 0,
            "absent": 0,
            "percentage": 0.0
        }
        if att_res and att_res[0]["total"] > 0:
            t = att_res[0]["total"]
            w = att_res[0]["weighted_sum"]
            attendance_stats = {
                "total": t,
                "present": att_res[0]["present"],
                "late": att_res[0]["late"],
                "absent": att_res[0]["absent"],
                "percentage": round((w / t) * 100.0, 2)
            }

        # Overall student marks average
        student_overall_avg = 0.0
        if chronological_assessments:
            student_overall_avg = round(sum([x["percentage"] for x in chronological_assessments]) / len(chronological_assessments), 2)

        # 5. Generate Tailored Explainable Learning Recommendations
        recommendations = []

        # Attendance recommendations
        if attendance_stats["total"] > 0 and attendance_stats["percentage"] < la_thresh:
            diff = round(la_thresh - attendance_stats["percentage"], 1)
            recommendations.append({
                "category": "Attendance Alert",
                "severity": "High",
                "message": (
                    f"Current attendance is {attendance_stats['percentage']}% ({attendance_stats['absent']} absences), "
                    f"which is {diff}% below the required {la_thresh}% threshold. "
                    "Regular classroom presence is critical to avoid attendance shortage penalties."
                )
            })

        # Subject-specific recommendations
        for w in weak_subjects:
            gap = round(lp_thresh - w["avg_percentage"], 1)
            recommendations.append({
                "category": f"Subject Remediation: {w['subject_name']} ({w['subject_code']})",
                "severity": "High" if w["avg_percentage"] < p_thresh else "Medium",
                "message": (
                    f"Average score in {w['subject_name']} is currently {w['avg_percentage']}%, "
                    f"falling short of the target by {gap}%. Recommended actions: attend weekly tutorial sessions, "
                    "review textbook exercises, and schedule one-on-one doubt clearing with faculty."
                )
            })

        # Trajectory recommendation
        if "Declining" in trend_status:
            recommendations.append({
                "category": "Performance Trend Intervention",
                "severity": "Medium",
                "message": (
                    f"Chronological scores indicate a downward trend with a {abs(trend_delta)}% drop between recent "
                    "and earlier assessments. Immediate review of recent quizzes and exam solutions is advised."
                )
            })

        # Positive commendations
        for s in strong_subjects:
            recommendations.append({
                "category": f"Academic Commendation: {s['subject_name']}",
                "severity": "Positive",
                "message": (
                    f"Outstanding performance in {s['subject_name']} with an average of {s['avg_percentage']}%. "
                    "Encourage peer-tutoring participation or advanced competitive coding/projects."
                )
            })

        if not recommendations:
            recommendations.append({
                "category": "Consistent Performance",
                "severity": "Positive",
                "message": "Student is maintaining satisfactory academic progress and meeting attendance requirements."
            })

        return {
            "student_id": clean_id,
            "name": student.get("name"),
            "email": student.get("email"),
            "class_name": student.get("class_name"),
            "enrollment_date": student.get("enrollment_date"),
            "skills": student.get("skills", []),
            "overall_average": student_overall_avg,
            "attendance_stats": attendance_stats,
            "subject_breakdown": subject_breakdown,
            "weak_subjects": weak_subjects,
            "strong_subjects": strong_subjects,
            "trend_status": trend_status,
            "trend_delta": trend_delta,
            "chronological_assessments": chronological_assessments,
            "recommendations": recommendations
        }

    @staticmethod
    def get_classroom_insights(
        class_name: Optional[str] = None,
        pass_threshold: Optional[float] = None,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        """
        Class-level insights highlighting subjects with highest and lowest average marks,
        pass rates, and overall engagement indicators.
        """
        database = db if db is not None else get_database()
        threshold = pass_threshold if pass_threshold is not None else config.PASS_MARKS_PERCENTAGE

        match_stage = {}
        if class_name and class_name != "All Classes":
            match_stage["student.class_name"] = class_name.strip()

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
        ]
        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.extend([
            {
                "$project": {
                    "subject_code": 1,
                    "marks_pct": {
                        "$multiply": [{"$divide": ["$marks", "$max_marks"]}, 100]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$subject_code",
                    "avg_percentage": {"$avg": "$marks_pct"},
                    "total_assessments": {"$sum": 1},
                    "passed": {
                        "$sum": {"$cond": [{"$gte": ["$marks_pct", threshold]}, 1, 0]}
                    }
                }
            },
            {
                "$lookup": {
                    "from": config.COLLECTION_SUBJECTS,
                    "localField": "_id",
                    "foreignField": "subject_code",
                    "as": "sub"
                }
            },
            {"$unwind": {"path": "$sub", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "subject_code": "$_id",
                    "subject_name": {"$ifNull": ["$sub.subject_name", "$_id"]},
                    "avg_percentage": {"$round": ["$avg_percentage", 2]},
                    "total_assessments": 1,
                    "pass_rate": {
                        "$round": [
                            {"$multiply": [{"$divide": ["$passed", "$total_assessments"]}, 100]},
                            2
                        ]
                    }
                }
            },
            {"$sort": {"avg_percentage": 1}}
        ])

        subjects_analysis = list(database[config.COLLECTION_ASSESSMENTS].aggregate(pipeline))

        lowest_subjects = subjects_analysis[:3] if subjects_analysis else []
        highest_subjects = list(reversed(subjects_analysis[-3:])) if subjects_analysis else []

        return {
            "class_name": class_name or "All Classes",
            "subjects_analysis": subjects_analysis,
            "lowest_performing_subjects": lowest_subjects,
            "highest_performing_subjects": highest_subjects
        }
