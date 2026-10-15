# IntelliTrack — MongoDB Aggregation Pipeline Reference & Explanations

This document provides a comprehensive technical reference for the 12 production-grade MongoDB aggregation pipelines implemented in `services/analytics_service.py` using PyMongo's `collection.aggregate()`.

---

## Pipeline 1: Average Marks Percentage by Subject

### Purpose & Academic Utility
Computes the mean score achieved by students in each subject normalized to a percentage scale, accounting for differing maximum marks across quizzes, midterms, and final exams.

### MongoDB Stages & Operators
1. **`$project`**:
   - Operators: `$divide`, `$multiply`
   - Dynamically calculates the normalized percentage:
     `marks_pct = (marks / max_marks) * 100`
2. **`$group`**:
   - Operators: `$avg`, `$sum`
   - Groups by `_id: "$subject_code"`.
   - Computes `avg_percentage: {"$avg": "$marks_pct"}` and `assessment_count: {"$sum": 1}`.
3. **`$lookup`**:
   - Left outer joins with the `subjects` collection matching `_id` against `subject_code` to enrich the record with course details.
4. **`$unwind`**:
   - Flattens the array returned by `$lookup` (`preserveNullAndEmptyArrays: True`).
5. **`$project`**:
   - Formats fields and rounds `avg_percentage` to 2 decimal places using `$round`.
6. **`$sort`**:
   - Orders descending by `avg_percentage` (`{"avg_percentage": -1}`).

### Sample Output
```json
{
  "subject_code": "CS301",
  "subject_name": "Intelligent NoSQL Databases",
  "avg_percentage": 68.42,
  "assessment_count": 185
}
```

---

## Pipeline 2: Average Performance by Academic Class

### Purpose & Academic Utility
Evaluates inter-class cohort performance to identify sections excelling or falling behind across academic departments.

### MongoDB Stages & Operators
1. **`$lookup`**:
   - Joins `assessments` with `students` on `student_id` to obtain the student's assigned `class_name`.
2. **`$unwind`**:
   - Extracts student profile details.
3. **`$project`**:
   - Normalizes marks percentage (`(marks / max_marks) * 100`).
4. **`$group`**:
   - Grouping key: `_id: "$class_name"`.
   - Accumulators:
     - `avg_percentage: {"$avg": "$marks_pct"}`
     - `total_assessments: {"$sum": 1}`
     - `students: {"$addToSet": "$student_id"}` (collects unique active student IDs)
5. **`$project`**:
   - Computes `student_count: {"$size": "$students"}` and rounds percentage.
6. **`$sort`**:
   - Sorted descending by class average.

### Sample Output
```json
{
  "class_name": "BTech-CSE-A",
  "avg_percentage": 71.18,
  "total_assessments": 375,
  "student_count": 38
}
```

---

## Pipeline 3: Top Students Based on Mean Academic Percentage

### Purpose & Academic Utility
Identifies high-achieving candidates for the Dean’s List or academic merit honors based on their cumulative average across all assessments.

### MongoDB Stages & Operators
1. **`$project`**: Normalizes marks to percentage.
2. **`$group`**: Groups by `_id: "$student_id"`, computing overall mean score and total assessment count.
3. **`$lookup`**: Joins with `students` collection to retrieve full name, class, and email.
4. **`$unwind`**: Flattens student details.
5. **`$project`**: Structures output with rounded mean score.
6. **`$sort`**: Orders by `{"overall_average": -1, "assessment_count": -1}`.
7. **`$limit`**: Returns top $N$ candidates (default: 10).

### Sample Output
```json
{
  "student_id": "STU1012",
  "name": "Diya Patel",
  "class_name": "BTech-AI-A",
  "email": "diya.patel12@campus.edu",
  "overall_average": 94.65,
  "assessment_count": 10
}
```

---

## Pipeline 4: Pass Rate by Subject

### Purpose & Academic Utility
Determines the percentage of students passing each subject based on a configurable threshold (e.g. $\ge 40\%$), helping curriculum directors detect bottleneck courses.

### MongoDB Stages & Operators
1. **`$project`**: Computes `marks_pct`.
2. **`$project`**:
   - Operator: `$cond`
   - Flags each assessment attempt: `is_pass: {"$cond": [{"$gte": ["$marks_pct", threshold]}, 1, 0]}`.
3. **`$group`**:
   - Computes `total_assessments: {"$sum": 1}` and `passed_count: {"$sum": "$is_pass"}`.
4. **`$lookup` & `$unwind`**: Enriches course titles from `subjects`.
5. **`$project`**:
   - Operator: `$subtract`, `$divide`, `$multiply`, `$round`
   - Computes `failed_count = total_assessments - passed_count`.
   - Computes `pass_rate = round((passed_count / total_assessments) * 100, 2)`.
6. **`$sort`**: Descending by pass rate.

### Sample Output
```json
{
  "subject_code": "CS301",
  "subject_name": "Intelligent NoSQL Databases",
  "total_assessments": 185,
  "passed_count": 168,
  "failed_count": 17,
  "pass_rate": 90.81,
  "avg_percentage": 68.42
}
```

---

## Pipeline 5: Assessment Count & Average Marks by Subject & Type

### Purpose & Academic Utility
Provides a multidimensional breakdown of grades partitioned by both subject and examination category (Quiz, Lab, Midterm, Project, Final Exam).

### MongoDB Stages & Operators
1. **`$project`**: Normalizes marks percentage.
2. **`$group`**:
   - Compound Grouping Key:
     ```json
     "_id": {
       "subject_code": "$subject_code",
       "assessment_type": "$assessment_type"
     }
     ```
   - Accumulates `count` and `avg_percentage`.
3. **`$project`**: Flattens composite ID keys.
4. **`$sort`**: Ascending by subject code and assessment type.

### Sample Output
```json
{
  "subject_code": "CS301",
  "assessment_type": "Midterm",
  "count": 37,
  "avg_percentage": 65.40
}
```

---

## Pipeline 6: Monthly Longitudinal Performance Trends

### Purpose & Academic Utility
Tracks calendar-month grade fluctuations across the semester to evaluate whether mid-semester interventions yield measurable score improvements.

### MongoDB Stages & Operators
1. **`$project`**:
   - Operator: `$substrCP`
   - Extracts the `YYYY-MM` month substring from ISO date string `assessment_date`.
   - Normalizes `marks_pct`.
2. **`$group`**:
   - Groups by `_id: "$month"`.
   - Computes monthly mean score and assessment volume.
3. **`$project`**: Formats output document.
4. **`$sort`**: Chronological ordering (`{"month": 1}`).

### Sample Output
```json
{
  "month": "2026-09",
  "avg_percentage": 67.84,
  "total_assessments": 420
}
```

---

## Pipeline 7: Attendance Percentage Per Student (Applying Late Policy)

### Purpose & Academic Utility
Calculates mathematically rigorous individual student attendance rates, applying the university policy where `Late` is credited with 0.5 weight.

### MongoDB Stages & Operators
1. **`$project`**:
   - Operator: `$switch`
   - Evaluates session weight:
     ```json
     "weighted_score": {
       "$switch": {
         "branches": [
           {"case": {"$eq": ["$status", "Present"]}, "then": 1.0},
           {"case": {"$eq": ["$status", "Late"]}, "then": 0.5}
         ],
         "default": 0.0
       }
     }
     ```
2. **`$group`**:
   - Groups by `student_id`.
   - Computes `total_sessions`, `weighted_sum`, `present_count`, `late_count`, `absent_count`.
3. **`$lookup` & `$unwind`**: Joins with `students` to attach name and class.
4. **`$project`**:
   - Computes: `attendance_percentage = round((weighted_sum / total_sessions) * 100, 2)`.
5. **`$sort`**: Descending by attendance percentage.

### Sample Output
```json
{
  "student_id": "STU1001",
  "name": "Aarav Sharma",
  "class_name": "BTech-CSE-A",
  "total_sessions": 44,
  "present_count": 38,
  "late_count": 4,
  "absent_count": 2,
  "attendance_percentage": 90.91
}
```

---

## Pipeline 8: Attendance Distribution by Status

### Purpose & Academic Utility
Provides overall institutional presence ratios across campus for executive capacity planning.

### MongoDB Stages & Operators
1. **`$group`**: Groups by `_id: "$status"`, summing total logs.
2. **`$project`**: Formats clean keys (`status`, `count`).
3. **`$sort`**: Descending by occurrence count.

### Sample Output
```json
{ "status": "Present", "count": 5240 }
{ "status": "Late", "count": 780 }
{ "status": "Absent", "count": 580 }
```

---

## Pipeline 9: Students with Low Average Marks

### Purpose & Academic Utility
Filters all students whose overall assessment percentage falls below the remediation threshold (default: $< 50\%$).

### MongoDB Stages & Operators
1. **`$project`**: Normalizes `marks_pct`.
2. **`$group`**: Computes `overall_average` per student.
3. **`$match`**:
   - Filters: `{"overall_average": {"$lt": threshold}}`.
4. **`$lookup` & `$unwind`**: Enriches student details from `students`.
5. **`$project` & `$sort`**: Formats and sorts ascending (lowest scores first).

---

## Pipeline 10: Students with Low Attendance

### Purpose & Academic Utility
Identifies students at risk of attendance shortages before end-of-semester examination disqualification (default: $< 75\%$).

### MongoDB Stages & Operators
1. **`$project`**: Maps status to numeric weight using `$switch`.
2. **`$group`**: Accumulates total sessions and weighted sum per student.
3. **`$project`**: Calculates `attendance_percentage`.
4. **`$match`**: Filters: `{"attendance_percentage": {"$lt": threshold}}`.
5. **`$lookup` & `$unwind`**: Enriches student name and email.
6. **`$sort`**: Ascending by attendance percentage.

---

## Pipeline 11: Declining Performance Across Chronological Assessments

### Purpose & Academic Utility
Detects students who began the term with strong scores but have experienced a severe downward trajectory.

### MongoDB Stages & Operators
1. **`$sort`**: Orders assessments by `student_id: 1, assessment_date: 1`.
2. **`$project`**: Calculates normalized percentage.
3. **`$group`**:
   - Operator: `$push`
   - Pushes chronological test events into an ordered array:
     ```json
     "assessment_history": {
       "$push": { "date": "$assessment_date", "subject": "$subject_code", "pct": "$marks_pct" }
     }
     ```
   - Filters cohorts having at least 3 historical assessments (`$match: {"total_count": {"$gte": 3}}`).
4. **Application Logic**:
   - Computes baseline average (first half) vs recent average (second half).
   - If `delta <= -5.0%`, flags student with empirical `score_drop`.

---

## Pipeline 12: Class-Level Multidimensional Performance Comparison

### Purpose & Academic Utility
Synthesizes marks averages, pass rates, and attendance percentages into a single cohort comparison table.

### MongoDB Stages & Operators
1. **Part A (Marks Aggregation)**:
   - Groups assessments by class.
   - Computes mean marks and pass rate % using `$cond`.
2. **Part B (Attendance Aggregation)**:
   - Groups attendance logs by class.
   - Computes weighted attendance rate using `$switch`.
3. **Merge Stage**:
   - Combines both analytical datasets into an executive multidimensional summary.
