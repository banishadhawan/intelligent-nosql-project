"""
Page B: Student Management
Provides full CRUD capabilities for student profiles with validation, search,
filtering, detailed profile drawer, and cascade deletion protection.
"""

import streamlit as st
import pandas as pd
from datetime import date
from services.student_service import StudentService
from services.assessment_service import AssessmentService
from services.attendance_service import AttendanceService
from database.connection import get_database


def render_students_page():
    st.markdown("## 👨‍🎓 Student Profile Management")
    st.markdown("Register, search, update, and manage student demographic records and enrolled cohorts.")

    db = get_database()
    classes = ["All Classes"] + StudentService.get_classes_list(db=db)

    tab_list, tab_add, tab_edit, tab_delete = st.tabs([
        "📋 Student Directory",
        "➕ Register New Student",
        "✏️ Edit Student Info",
        "🗑️ Delete Student"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: DIRECTORY & SEARCH
    # -------------------------------------------------------------------------
    with tab_list:
        st.subheader("Student Directory")
        c1, c2 = st.columns([3, 1])
        with c1:
            search_query = st.text_input("🔍 Search by Student ID, Name, or Email", placeholder="e.g. STU1001 or Sharma")
        with c2:
            selected_class = st.selectbox("Filter by Class", options=classes)

        students = StudentService.list_students(search=search_query, class_filter=selected_class, db=db)

        if not students:
            st.info("No matching students found in the database.")
        else:
            st.caption(f"Showing {len(students)} student record(s).")
            display_data = []
            for s in students:
                skills_str = ", ".join(s.get("skills", [])) if isinstance(s.get("skills"), list) else str(s.get("skills", ""))
                display_data.append({
                    "Student ID": s.get("student_id"),
                    "Full Name": s.get("name"),
                    "Email": s.get("email"),
                    "Class": s.get("class_name"),
                    "Enrollment Date": s.get("enrollment_date"),
                    "Skills": skills_str
                })
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Detailed Profile Viewer
            st.markdown("---")
            st.subheader("🔎 View Detailed Student Dossier")
            student_ids = [s["student_id"] for s in students]
            selected_stu_id = st.selectbox("Select a student to inspect dossier:", options=student_ids)

            if selected_stu_id:
                stu_doc = StudentService.get_student_by_id(selected_stu_id, db=db)
                if stu_doc:
                    col_info, col_history = st.columns([1, 2])
                    with col_info:
                        st.markdown(f"### {stu_doc.get('name')}")
                        st.markdown(f"**Student ID:** `{stu_doc.get('student_id')}`")
                        st.markdown(f"**Email:** {stu_doc.get('email')}")
                        st.markdown(f"**Class:** {stu_doc.get('class_name')}")
                        st.markdown(f"**Enrolled:** {stu_doc.get('enrollment_date')}")
                        st.markdown(f"**Skills:** {', '.join(stu_doc.get('skills', []))}")

                    with col_history:
                        st.markdown("#### Academic Record Summary")
                        assessments = AssessmentService.list_assessments(student_id=selected_stu_id, limit=10, db=db)
                        if assessments:
                            df_a = pd.DataFrame(assessments)[["assessment_id", "subject_code", "assessment_name", "marks", "max_marks", "percentage", "assessment_date"]]
                            df_a.rename(columns={
                                "assessment_id": "ID",
                                "subject_code": "Subject",
                                "assessment_name": "Title",
                                "marks": "Marks",
                                "max_marks": "Max",
                                "percentage": "Score (%)",
                                "assessment_date": "Date"
                            }, inplace=True)
                            st.dataframe(df_a, use_container_width=True, hide_index=True)
                        else:
                            st.info("No assessments logged for this student.")

    # -------------------------------------------------------------------------
    # TAB 2: REGISTER STUDENT (CREATE)
    # -------------------------------------------------------------------------
    with tab_add:
        st.subheader("Register a New Student")
        with st.form("create_student_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_id = st.text_input("Student ID *", placeholder="e.g. STU1151").strip().upper()
                new_name = st.text_input("Full Name *", placeholder="e.g. Rohan Verma").strip()
                new_email = st.text_input("Email Address *", placeholder="e.g. rohan.verma@example.com").strip().lower()

            with col_b:
                new_class = st.text_input("Class / Section *", placeholder="e.g. BTech-CSE-A").strip()
                new_date = st.date_input("Enrollment Date *", value=date.today())
                new_skills = st.text_input("Skills (comma-separated)", placeholder="e.g. Python, SQL, MongoDB").strip()

            submitted = st.form_submit_button("Register Student", type="primary")

            if submitted:
                if not new_id or not new_name or not new_email or not new_class:
                    st.error("Please fill in all mandatory fields (*).")
                else:
                    payload = {
                        "student_id": new_id,
                        "name": new_name,
                        "email": new_email,
                        "class_name": new_class,
                        "enrollment_date": str(new_date),
                        "skills": [s.strip() for s in new_skills.split(",") if s.strip()]
                    }
                    success, msg, _ = StudentService.create_student(payload, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 3: EDIT STUDENT (UPDATE)
    # -------------------------------------------------------------------------
    with tab_edit:
        st.subheader("Modify Student Information")
        all_students = StudentService.list_students(limit=1000, db=db)
        if not all_students:
            st.warning("No students available to edit.")
        else:
            student_map = {f"{s['student_id']} - {s['name']} ({s['class_name']})": s for s in all_students}
            selected_label = st.selectbox("Select student to modify:", options=list(student_map.keys()))
            student_to_edit = student_map[selected_label]

            with st.form("edit_student_form"):
                st.info(f"Modifying Student ID: `{student_to_edit['student_id']}` (Immutable)")
                c1, c2 = st.columns(2)
                with c1:
                    edit_name = st.text_input("Full Name", value=student_to_edit.get("name", ""))
                    edit_email = st.text_input("Email Address", value=student_to_edit.get("email", ""))
                with c2:
                    edit_class = st.text_input("Class / Section", value=student_to_edit.get("class_name", ""))
                    current_skills = ", ".join(student_to_edit.get("skills", []))
                    edit_skills = st.text_input("Skills (comma-separated)", value=current_skills)

                update_btn = st.form_submit_button("Save Changes", type="primary")

                if update_btn:
                    update_payload = {
                        "name": edit_name,
                        "email": edit_email,
                        "class_name": edit_class,
                        "skills": [s.strip() for s in edit_skills.split(",") if s.strip()]
                    }
                    success, msg, _ = StudentService.update_student(student_to_edit["student_id"], update_payload, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 4: DELETE STUDENT (DELETE with cascade policy)
    # -------------------------------------------------------------------------
    with tab_delete:
        st.subheader("Delete Student Record")
        all_students = StudentService.list_students(limit=1000, db=db)
        if not all_students:
            st.warning("No students to delete.")
        else:
            del_map = {f"{s['student_id']} - {s['name']} ({s['class_name']})": s for s in all_students}
            selected_del_label = st.selectbox("Select student to remove:", options=list(del_map.keys()), key="del_select")
            target_student = del_map[selected_del_label]
            target_id = target_student["student_id"]

            # Count dependencies
            asm_cnt = db["assessments"].count_documents({"student_id": target_id})
            att_cnt = db["attendance"].count_documents({"student_id": target_id})

            st.warning(
                f"⚠️ **Attention**: You have selected **{target_student['name']} ({target_id})**.\n\n"
                f"This student currently has **{asm_cnt} assessment records** and **{att_cnt} attendance entries** in the database."
            )

            cascade_opt = st.checkbox("Cascade delete: cleanly remove all associated assessments and attendance logs to avoid orphan records", value=True)
            confirm_check = st.checkbox(f"I confirm that I want to permanently delete student {target_id}.", value=False)

            if st.button("Permanently Delete Student", type="primary", disabled=not confirm_check):
                success, msg = StudentService.delete_student(target_id, cascade=cascade_opt, db=db)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
