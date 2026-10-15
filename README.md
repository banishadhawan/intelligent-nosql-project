# IntelliTrack — Intelligent Student Performance & Learning Analytics System

An advanced, production-grade individual academic project built using **MongoDB, PyMongo, Streamlit, Pandas, and Plotly**.

---

## 📌 Table of Contents
1. [Project Overview & Title](#project-overview)
2. [Problem Statement & Existing Limitations](#problem-statement)
3. [Objectives & Proposed Solution](#objectives--proposed-solution)
4. [Scope and System Limitations](#scope-and-limitations)
5. [System Requirements](#system-requirements)
6. [Technology Stack](#technology-stack)
7. [System Architecture](#system-architecture)
8. [Database Schema & Collection Design](#database-schema)
9. [Index Architecture & Optimization](#indexes)
10. [Step-by-Step Windows Installation & Execution Guide](#installation-guide)
11. [Dataset Generation & Idempotency](#dataset-generation)
12. [CRUD Operations Specification](#crud-operations)
13. [Dual-Layer Validation Strategy](#validation-strategy)
14. [MongoDB Aggregation Pipelines (12 Genuine Pipelines)](#aggregation-pipelines)
15. [Intelligent Learning Insights & Explainable Diagnostics](#intelligent-insights)
16. [Automated Testing Suite (Pytest)](#testing)
17. [Demonstration Checklist for College Viva](#demonstration-checklist)
18. [Capturing Real Application Screenshots](#screenshots)
19. [Future Roadmap & Enhancements](#future-enhancements)

---

## 1. Project Overview <a name="project-overview"></a>
**IntelliTrack** is an enterprise-grade academic analytics platform designed to empower educators, academic advisors, and institutional leaders. By leveraging MongoDB's document model and high-performance server-side aggregation pipelines, the system processes longitudinal assessment scores, subject credit weights, and session-by-session attendance logs. IntelliTrack transforms raw academic data into actionable pedagogical interventions, identifies at-risk cohorts with transparent empirical evidence, and tracks student progress across semesters.

---

## 2. Problem Statement & Existing Limitations <a name="problem-statement"></a>
Traditional university academic management systems exhibit critical deficiencies:
1. **Static Data Repositories**: Most existing systems function merely as passive digital registers for storing marks without performing intelligent trend or cohort analysis.
2. **Relational Rigidity**: Conventional relational databases struggle to adapt when curriculum structures, assessment types, and elective skill sets evolve across university departments.
3. **Late-Stage Interventions**: Student learning difficulties are frequently identified only after semester final exams have concluded, when remediation is no longer possible.
4. **Black-Box AI Fallacies**: Modern AI systems frequently produce unexplainable predictions or require costly external APIs, making them unsuitable for transparent academic grading and institutional audits.

---

## 3. Objectives & Proposed Solution <a name="objectives--proposed-solution"></a>
### Objectives:
- Implement a **pure MongoDB + PyMongo** backend adhering to enterprise NoSQL standards.
- Deliver full Create, Read, Update, and Delete (**CRUD**) capabilities across students, subjects, assessments, and attendance.
- Execute **12 genuine MongoDB aggregation pipelines** calculating marks averages, subject pass rates, chronological trends, and attendance percentages.
- Deliver **deterministic, explainable intelligence** diagnosing at-risk learners with empirical evidence.
- Maintain a clear separation of concerns (UI, Business Services, Models, Validation, Database).

### Proposed Solution:
IntelliTrack introduces a centralized, reactive Streamlit dashboard powered by an optimized PyMongo query layer. All dashboard indicators, charts, and alerts operate on live MongoDB records, automatically updating when records are inserted, modified, or deleted.

---

## 4. Scope and System Limitations <a name="scope-and-limitations"></a>
- **Scope**: Covers comprehensive undergraduate and postgraduate cohorts across student registration, course allocations, multifaceted assessments (Quizzes, Midterms, Practicals, Final Exams), and lecture attendance.
- **Limitations**:
  - Currently operates in single-institution mode (multi-tenant university branching can be added in future versions).
  - Deletions are coordinated via safe application-level cascading rather than distributed replica-set ACID transactions.

---

## 5. System Requirements <a name="system-requirements"></a>
### Functional Requirements:
- Multi-factor At-Risk student screening based on marks, attendance, and decline trajectory.
- Referential integrity enforcement preventing orphan records.
- Row-level validated CSV import and clean CSV export.
- Idempotent synthetic dataset generation reproducing 150 students, 8 subjects, 1,500 assessments, and 6,600 attendance logs.

### Non-Functional Requirements:
- Sub-second execution for all aggregation pipelines on typical college cohorts.
- Resilient error handling without exposing database credentials or raw stack traces.
- Clean, responsive user experience compatible with standard laptop screens.

---

## 6. Technology Stack <a name="technology-stack"></a>
- **Programming Language**: Python 3.11+
- **Primary Database**: MongoDB Community Server 8.x / MongoDB Atlas
- **Database Driver**: PyMongo 4.x (Synchronous native client)
- **User Interface**: Streamlit 1.30+
- **Data Manipulation**: Pandas 2.x
- **Data Visualization**: Plotly Express & Plotly Graph Objects
- **Validation**: Pydantic v2 (Application Layer) & MongoDB `$jsonSchema` (Engine Layer)
- **Configuration**: python-dotenv
- **Testing Framework**: Pytest 7.x+

---

## 7. System Architecture <a name="system-architecture"></a>
The project follows a clean architectural layout:

```
c:\Users\banis\mongodb project\
├── app.py                      # Streamlit application entrypoint & routing
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Project dependencies
├── .env.example                # Environment variables template
├── .env                        # Local active environment configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Primary system documentation
├── database/
│   ├── __init__.py
│   ├── connection.py           # Singleton MongoClient & connection health check
│   ├── indexes.py              # Unique & compound index specifications
│   └── validators.py           # MongoDB $jsonSchema collection validation
├── models/
│   ├── __init__.py
│   ├── student.py              # Student Pydantic models
│   ├── subject.py              # Subject Pydantic models
│   ├── assessment.py           # Assessment Pydantic models & percentage logic
│   └── attendance.py           # Attendance Pydantic models & status enum
├── services/
│   ├── __init__.py
│   ├── student_service.py      # Student CRUD & cascade deletion logic
│   ├── subject_service.py      # Subject CRUD & referential protection
│   ├── assessment_service.py   # Assessment CRUD & foreign-key validation
│   ├── attendance_service.py   # Attendance CRUD & duplicate prevention
│   ├── analytics_service.py    # 12 Genuine MongoDB aggregation pipelines
│   ├── insights_service.py     # Rules-based diagnostics & recommendations
│   └── import_export_service.py# Two-pass CSV validation import & export
├── pages/
│   ├── __init__.py
│   ├── dashboard.py            # Page A: Home Dashboard
│   ├── students.py             # Page B: Student Profile Management
│   ├── subjects.py             # Page C: Subject Management
│   ├── assessments.py          # Page D: Assessment & Marks Management
│   ├── attendance.py           # Page E: Attendance Tracking
│   ├── analytics.py            # Page F: Academic Analytics & Aggregations
│   ├── insights.py             # Page G: Intelligent Learning Insights
│   └── data_management.py      # Page H: CSV Import/Export & Seeder UI
├── scripts/
│   ├── __init__.py
│   └── seed_data.py            # Reproducible synthetic dataset generator
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures & isolated test_db
│   ├── test_validation.py      # Domain model unit tests
│   ├── test_student_crud.py    # Student CRUD integration tests
│   ├── test_subject_crud.py    # Subject CRUD integration tests
│   ├── test_assessment_crud.py # Assessment CRUD integration tests
│   ├── test_attendance_crud.py # Attendance CRUD integration tests
│   ├── test_analytics.py       # Aggregation pipeline tests on known dataset
│   └── test_insights.py        # Diagnostic & idempotency tests
└── docs/
    ├── database_design.md      # Detailed database architecture documentation
    ├── aggregation_explanations.md # Complete technical aggregation guide
    └── viva_questions.md       # 28 Project viva questions & answers
```

---

## 8. Database Schema & Collection Design <a name="database-schema"></a>
The database `intellitrack` contains four collections:

1. **`students`**: Demographic records (`student_id`, `name`, `email`, `class_name`, `enrollment_date`, `skills`).
2. **`subjects`**: Course catalog (`subject_code`, `subject_name`, `credits`, `class_name`, `description`).
3. **`assessments`**: Submissions (`assessment_id`, `student_id`, `subject_code`, `assessment_name`, `assessment_type`, `marks`, `max_marks`, `percentage`, `assessment_date`, `remarks`).
4. **`attendance`**: Daily lecture logs (`student_id`, `subject_code`, `attendance_date`, `status`, `remarks`).

Detailed schemas are documented in [docs/database_design.md](file:///c:/Users/banis/mongodb%20project/docs/database_design.md).

---

## 9. Index Architecture & Optimization <a name="indexes"></a>
Indexes are automatically created upon application startup and seeding:
- **`students`**: Unique index on `student_id`, unique index on `email`, index on `class_name`.
- **`subjects`**: Unique index on `subject_code`, index on `class_name`.
- **`assessments`**: Unique index on `assessment_id`, compound index on `(student_id, subject_code)`, index on `assessment_date`.
- **`attendance`**: **Unique compound index on `(student_id, subject_code, attendance_date)`** to guarantee zero duplicate logs for the same student on the same date.

---

## 10. Step-by-Step Windows Installation & Execution Guide <a name="installation-guide"></a>

### Prerequisites:
- Windows 10/11
- Python 3.11 installed (`python --version`)
- MongoDB Community Server installed and running as a Windows Service

### Step 1: Ensure MongoDB is Running
Open PowerShell or Command Prompt:
```powershell
Get-Service -Name "*mongo*"
# If stopped, start it:
net start MongoDB
```

### Step 2: Navigate to Project Directory & Activate Virtual Environment
```powershell
cd "c:\Users\banis\mongodb project"
# If venv is not yet created:
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Settings
Ensure `.env` exists in the project root:
```ini
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=intellitrack
PASS_MARKS_PERCENTAGE=40
LOW_PERFORMANCE_THRESHOLD=50
LOW_ATTENDANCE_THRESHOLD=75
LATE_ATTENDANCE_WEIGHT=0.5
```

### Step 5: Seed Database with Reproducible Dataset
```powershell
python scripts/seed_data.py --students 150
```

### Step 6: Launch the Streamlit Application
```powershell
streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

---

## 11. Dataset Generation & Idempotency <a name="dataset-generation"></a>
The dataset generator (`scripts/seed_data.py`) creates an original, reproducible academic dataset using a fixed random seed (`42`):
- **150 Students** across 4 classes (`BTech-CSE-A`, `BTech-CSE-B`, `BTech-AI-A`, `BTech-DS-A`).
- **8 Core Subjects** with varying credit weightings (3–4 credits).
- **1,500 Assessments** with varied maximum marks (20, 25, 40, 50, 100 marks).
- **6,600 Attendance records** spanning August–November 2026.
- Stratified performance distribution:
  - 20% High Performers (80–98% scores)
  - 55% Average Performers (55–78% scores)
  - 15% At-Risk Students (25–48% scores)
  - 10% Declining Trajectory Cohort (scores start high at 85% and decline to 35% across exams)

### Safe Reruns:
Running `python scripts/seed_data.py` is **idempotent** (uses upserts on unique keys). To completely wipe and rebuild:
```powershell
python scripts/seed_data.py --reset --students 150
```
Or for a rapid demo:
```powershell
python scripts/seed_data.py --demo
```

---

## 12. CRUD Operations Specification <a name="crud-operations"></a>
| Entity | Create | Read | Update | Delete Policy |
|---|---|---|---|---|
| **Student** | Form with ID, name, email, class, skills | Search by ID/name, filter by class, inspect dossier | Edit name, class, email, skills with validation | Cascade delete cleans related assessments & attendance to prevent orphan records |
| **Subject** | Form with code, name, credits (1-10), class | Catalog table with assessment count metrics | Edit title, credits, syllabus description | Deletion blocked if referenced by assessments unless force cascade confirmed |
| **Assessment** | Form with marks & max_marks validation | Multi-filter by student, subject, assessment type | Recalculates percentage on marks update | Confirmation dialog before deletion |
| **Attendance** | Marks Present, Late, or Absent | Filters by student, subject, status, and dates | Update status or notes | Delete incorrect entry with confirmation |

---

## 13. Dual-Layer Validation Strategy <a name="validation-strategy"></a>
1. **Application-Level Validation (Pydantic v2)**:
   - Validates regex student ID (`^[A-Z0-9_-]+$`) and email formats.
   - Enforces $0 \le \text{marks} \le \text{max\_marks}$.
   - Restricts attendance status to `Present`, `Absent`, or `Late`.
   - Validates subject credits ($1 \le \text{credits} \le 10$).
2. **Database-Level Validation (MongoDB `$jsonSchema`)**:
   - Registered directly on collections.
   - Prevents unvalidated BSON insertions by any external script or client.

---

## 14. MongoDB Aggregation Pipelines <a name="aggregation-pipelines"></a>
IntelliTrack implements 12 genuine aggregation pipelines in `services/analytics_service.py`:
1. `get_average_marks_by_subject`: Normalizes percentages and groups by course title.
2. `get_average_performance_by_class`: Groups by cohort section with student count.
3. `get_top_students`: Computes overall mean percentages and ranks the top 10 students.
4. `get_pass_rate_by_subject`: Evaluates pass/fail counts using `$cond` based on configurable thresholds.
5. `get_assessment_count_and_avg_by_subject`: Grouping on composite keys `(subject_code, assessment_type)`.
6. `get_monthly_performance_trends`: Extracts calendar months via `$substrCP` to track semester progression.
7. `get_attendance_percentage_per_student`: Calculates weighted attendance rates using `$switch`.
8. `get_attendance_distribution_by_status`: Campus-wide breakdown of Present, Late, and Absent logs.
9. `get_students_with_low_marks`: Filters students whose overall score falls below warning thresholds.
10. `get_students_with_low_attendance`: Identifies students at risk of attendance shortages.
11. `get_declining_students`: Pushes chronological assessment histories using `$push` to calculate trajectory deltas.
12. `get_class_level_performance_comparison`: Combines academic averages, pass rates, and attendance into a single multidimensional comparison.

Full details in [docs/aggregation_explanations.md](file:///c:/Users/banis/mongodb%20project/docs/aggregation_explanations.md).

---

## 15. Intelligent Learning Insights & Explainable Diagnostics <a name="intelligent-insights"></a>
- **Zero Third-Party AI Fees**: Operates deterministically on live MongoDB records.
- **Transparent Empirical Evidence**: Never flags a student without identifying the underlying evidence (e.g., *"Attendance is 62.5% across 24 lectures; scores in CS301 dropped from 82% to 41%"*).
- **Personalized Recommendations**: Generates actionable guidance for students (remedial tutorials, attendance warnings, or advanced competitive tasks).
- **Classroom Bottleneck Detection**: Identifies courses with lowest class averages for curriculum review.

---

## 16. Automated Testing Suite (Pytest) <a name="testing"></a>
All 25 automated unit and integration tests execute against an isolated `intellitrack_test` database:
```powershell
.\venv\Scripts\pytest -v
```
**Test Coverage Includes:**
- Pydantic model validation (valid fields, missing fields, invalid emails, negative marks, marks > max_marks, credit bounds, status enums).
- Student CRUD, duplicate ID rejection, duplicate email rejection, and cascade deletion.
- Subject CRUD, uniqueness, and referential protection against unsafe deletion.
- Assessment CRUD, foreign key checks (rejects nonexistent student or subject), and percentage calculations.
- Attendance CRUD and unique compound constraint preventing duplicate dates.
- Aggregation pipelines on controlled datasets with differing maximum marks.
- Empty collection handling (safe defaults, zero division prevention).
- At-risk detection, chronological trend detection, and seeder idempotency.

---

## 17. Demonstration Checklist for College Viva <a name="demonstration-checklist"></a>
1. **Show MongoDB Running**: Show MongoDB service in Windows Services or run `Get-Service -Name "*mongo*"`.
2. **Execute Pytest**: Run `pytest -v` to show all 25 tests passing in seconds.
3. **Launch Streamlit**: Run `streamlit run app.py` and open `http://localhost:8501`.
4. **Demonstrate Home Dashboard**: Show live KPI metric cards (150 students, 8 subjects, 1,500 assessments, 6,600 attendance logs) and Plotly charts.
5. **Demonstrate CRUD Operations**:
   - Register a new student on the Student Management page.
   - Show the new student appearing in the directory.
   - Modify the student's skills or name.
   - Delete the student and observe the cascade deletion of related records.
6. **Demonstrate Referential Integrity**: Attempt to log an assessment for a nonexistent student ID; show the descriptive error message.
7. **Demonstrate Configurable Thresholds**: Adjust the Passing Marks slider in the sidebar from 40% to 55%; watch the pass rate charts and at-risk metrics update dynamically.
8. **Demonstrate Intelligent Insights**: Open the Individual Student Diagnostic tab and inspect a student's chronological score progression and tailored recommendations.
9. **Demonstrate CSV Import/Export**: Export the `assessments` collection to CSV and download it.

---

## 18. Capturing Real Application Screenshots <a name="screenshots"></a>
To add screenshots to your submission document or college report:
1. Start the application: `streamlit run app.py`.
2. Open `http://localhost:8501` in your browser.
3. Use the Windows Snipping Tool (`Win + Shift + S`) to capture:
   - *Screenshot 1*: Executive Academic Dashboard with KPI cards and Plotly charts.
   - *Screenshot 2*: Student Management Directory and detailed student dossier.
   - *Screenshot 3*: Assessment and Marks logging form with automated percentage calculation.
   - *Screenshot 4*: Academic Analytics pass rate and monthly trend graphs.
   - *Screenshot 5*: Intelligent Learning Insights showing At-Risk student triage and empirical evidence.
4. Save the images into a `docs/screenshots/` folder.

---

## 19. Future Roadmap & Enhancements <a name="future-enhancements"></a>
- **Role-Based Access Control (RBAC)**: Distinct login views for students, faculty, and university administrators.
- **MongoDB Change Streams**: Real-time push notifications using `collection.watch()` when attendance falls below threshold.
- **Automated Report Generation**: One-click downloadable PDF transcripts and academic warning notices.
