# IntelliTrack — MongoDB Database Architecture & Schema Design

## 1. Architectural Overview & Design Philosophy

**IntelliTrack** is designed around MongoDB as its primary, native document database. Rather than attempting to force a relational schema onto NoSQL or inappropriately embedding unbounded arrays inside student documents, IntelliTrack follows standard enterprise document-oriented design patterns.

### Key Architectural Tenets:
1. **Separation of High-Velocity and Static Domains**:
   - Students and Subjects represent relatively static entity profiles.
   - Assessments and Attendance represent high-velocity, event-driven transactional datasets that scale continuously across academic semesters.
2. **Prevention of Document Bloat (16MB BSON Limit)**:
   - Embedding thousands of attendance logs or hundreds of assessment submissions directly into a single student document would lead to document bloat, frequent document relocations, and index thrashing.
   - Storing `assessments` and `attendance` as dedicated collections referencing `student_id` and `subject_code` enables unbounded horizontal scalability, efficient sharding, and rapid range-based aggregations.
3. **Application-Level & Engine-Level Dual Validation**:
   - Incoming payloads are validated synchronously at runtime using Python Pydantic models.
   - The MongoDB engine enforces collection-level `$jsonSchema` validators via `collMod` and collection creation, guaranteeing that no rogue client or script can corrupt database records.

---

## 2. Collections & Document Schemas

The database name is `intellitrack` (and `intellitrack_test` for isolated automated test runs).

### 2.1. `students` Collection
Stores demographic and enrollment profiles for registered students.

- **Sample Document**:
```json
{
  "_id": ObjectId("670f5e12..."),
  "student_id": "STU1001",
  "name": "Aarav Sharma",
  "email": "aarav.sharma1@campus.edu",
  "class_name": "BTech-CSE-A",
  "enrollment_date": "2026-08-01",
  "skills": ["Python", "MongoDB", "Data Structures", "Docker"]
}
```

- **Validation Rules (`$jsonSchema`)**:
  - `student_id`: String, required, unique index. Pattern: `^[A-Z0-9_-]+$`.
  - `name`: String, required, min length 2, max length 100.
  - `email`: String, required, regex email pattern.
  - `class_name`: String, required.
  - `enrollment_date`: String / Date (ISO YYYY-MM-DD), required.
  - `skills`: Array of strings.

---

### 2.2. `subjects` Collection
Represents the university curriculum courses, academic credit weightings, and class allocations.

- **Sample Document**:
```json
{
  "_id": ObjectId("670f5e15..."),
  "subject_code": "CS301",
  "subject_name": "Intelligent NoSQL Databases",
  "description": "Document databases, aggregation pipelines, schema modeling, and PyMongo analytics.",
  "credits": 4,
  "class_name": "BTech-CSE-A"
}
```

- **Validation Rules (`$jsonSchema`)**:
  - `subject_code`: String, required, unique index (e.g. `CS301`).
  - `subject_name`: String, required, min length 2, max length 100.
  - `description`: String.
  - `credits`: Integer / Number, required, minimum 1, maximum 10.
  - `class_name`: String, required.

---

### 2.3. `assessments` Collection
Records student marks across examinations, quizzes, lab practicals, assignments, and projects.

- **Sample Document**:
```json
{
  "_id": ObjectId("670f5e1a..."),
  "assessment_id": "ASM1001",
  "student_id": "STU1001",
  "subject_code": "CS301",
  "assessment_name": "Midterm Examination - CS301",
  "assessment_type": "Midterm",
  "marks": 42.0,
  "max_marks": 50.0,
  "percentage": 84.0,
  "assessment_date": "2026-10-04",
  "remarks": "Academic standing: High"
}
```

- **Validation Rules (`$jsonSchema`)**:
  - `assessment_id`: String, required, unique index.
  - `student_id`: String, required (foreign reference to `students.student_id`).
  - `subject_code`: String, required (foreign reference to `subjects.subject_code`).
  - `assessment_name`: String, required.
  - `assessment_type`: String, required (`Quiz`, `Midterm`, `Final Exam`, `Assignment`, `Project`, `Lab`).
  - `marks`: Number, required, minimum 0. Must not exceed `max_marks`.
  - `max_marks`: Number, required, strictly greater than 0.
  - `assessment_date`: String / Date (ISO YYYY-MM-DD), required.

---

### 2.4. `attendance` Collection
Tracks daily or session-level attendance logs per student per subject.

- **Sample Document**:
```json
{
  "_id": ObjectId("670f5e20..."),
  "student_id": "STU1001",
  "subject_code": "CS301",
  "attendance_date": "2026-08-18",
  "status": "Present",
  "remarks": ""
}
```

- **Validation Rules (`$jsonSchema`)**:
  - `student_id`: String, required (foreign reference to `students.student_id`).
  - `subject_code`: String, required (foreign reference to `subjects.subject_code`).
  - `attendance_date`: String / Date (ISO YYYY-MM-DD), required.
  - `status`: String, required (`Present`, `Absent`, `Late`).
  - Unique compound constraint on `(student_id, subject_code, attendance_date)`.

---

## 3. Index Design & Optimization Strategy

Indexes are systematically applied to ensure $O(\log N)$ point lookups, enforce uniqueness, and optimize MongoDB aggregation pipelines (`$match`, `$sort`, `$group`).

| Collection | Index Name | Key Specification | Type / Constraints | Purpose |
|---|---|---|---|---|
| `students` | `idx_unique_student_id` | `{"student_id": 1}` | Unique | Primary student identifier lookup; prevents duplicate IDs |
| `students` | `idx_unique_student_email` | `{"email": 1}` | Unique | Enforces campus email uniqueness |
| `students` | `idx_student_class` | `{"class_name": 1}` | Standard B-Tree | Accelerated filtering by cohort/section |
| `subjects` | `idx_unique_subject_code` | `{"subject_code": 1}` | Unique | Primary course identifier lookup; prevents duplicate subject codes |
| `subjects` | `idx_subject_class` | `{"class_name": 1}` | Standard B-Tree | Optimizes class curriculum queries |
| `assessments` | `idx_unique_assessment_id` | `{"assessment_id": 1}` | Unique | Primary assessment submission identifier |
| `assessments` | `idx_asm_student_subject` | `{"student_id": 1, "subject_code": 1}` | Compound | Optimizes student subject-specific grade queries |
| `assessments` | `idx_asm_student` | `{"student_id": 1}` | Standard B-Tree | Optimizes student performance history lookups |
| `assessments` | `idx_asm_subject` | `{"subject_code": 1}` | Standard B-Tree | Optimizes course pass rate and average calculations |
| `assessments` | `idx_asm_date` | `{"assessment_date": -1}` | Descending | Optimizes chronological timeline queries & trend analytics |
| `attendance` | `idx_unique_student_subject_date` | `{"student_id": 1, "subject_code": 1, "attendance_date": 1}` | Unique Compound | **Crucial constraint**: Prevents duplicate attendance logging for the same student and subject on the same day |
| `attendance` | `idx_att_student_date` | `{"student_id": 1, "attendance_date": -1}` | Compound | Accelerates student attendance history extraction |
| `attendance` | `idx_att_status` | `{"status": 1}` | Standard B-Tree | Optimizes campus attendance status breakdown aggregations |

---

## 4. Referential Integrity & Cascade Deletion Policy

MongoDB is a document database without automatic SQL foreign key cascading. IntelliTrack implements an explicit, tested referential integrity strategy in the application service layer:

1. **Child Insertion Safety**:
   - Before inserting an assessment record, `AssessmentService.create_assessment()` verifies that both `student_id` exists in `students` and `subject_code` exists in `subjects`.
   - Before inserting an attendance log, `AttendanceService.create_attendance()` verifies that both `student_id` and `subject_code` exist.
2. **Student Cascade Deletion**:
   - `StudentService.delete_student(student_id, cascade=True)`:
     When a student is deleted with cascade enabled, all associated assessment records in `assessments` and all attendance logs in `attendance` matching `student_id` are cleanly deleted in a coordinated sequence, eliminating orphan records completely.
   - If `cascade=False`, the deletion is aborted with a protective error if related records exist.
3. **Subject Safe Deletion**:
   - `SubjectService.delete_subject(subject_code, cascade=False)`:
     By default, deleting a subject is strictly blocked if any assessment records or attendance logs reference `subject_code`.
     Forced deletion (`cascade=True`) cleanly sweeps associated dependent records.

---

## 5. Attendance Calculation & Late Policy

The system applies a uniform, explainable academic attendance scoring model:
- **`Present`**: 1.0 weight (Full credit)
- **`Late`**: 0.5 weight (Configurable half credit; acknowledges student presence while accounting for arrival tardiness)
- **`Absent`**: 0.0 weight (No credit)

The student's attendance percentage is calculated using the MongoDB aggregation pipeline operator `$switch`:
$$\text{Attendance \%} = \frac{\sum \text{Weighted Scores}}{\text{Total Registered Sessions}} \times 100$$
This ensures mathematically consistent figures across the Home Dashboard, Academic Analytics, and At-Risk screening modules.
