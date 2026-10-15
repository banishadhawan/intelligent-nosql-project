"""
Page D: Assessment and Marks Management
Provides complete CRUD capabilities for academic assessments:
- Referential validation against active students and subjects
- Nonnegative marks and max_marks boundaries
- Automated percentage calculation
- Update and delete workflows
"""

import streamlit as st
import pandas as pd
from datetime import date
from services.assessment_service import AssessmentService
from services.student_service import StudentService
from services.subject_service import SubjectService
from models.assessment import ASSESSMENT_TYPES
from database.connection import get_database


def render_assessments_page():
    st.markdown("## 📝 Assessment & Marks Management")
    st.markdown("Log examinations, quizzes, assignments, compute scores, and manage student grades.")

    db = get_database()
    subjects = ["All Subjects"] + [s["subject_code"] for s in SubjectService.list_subjects(limit=100, db=db)]
    types = ["All Types"] + list(ASSESSMENT_TYPES)

    tab_list, tab_add, tab_edit, tab_delete = st.tabs([
        "📋 Assessment Log",
        "➕ Log New Assessment",
        "✏️ Edit Marks & Details",
        "🗑️ Delete Assessment"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: LIST & SEARCH
    # -------------------------------------------------------------------------
    with tab_list:
        st.subheader("Assessment Submissions")
        c1, c2, c3 = st.columns(3)
        with c1:
            filter_student = st.text_input("Filter by Student ID", placeholder="e.g. STU1001").strip()
        with c2:
            filter_subject = st.selectbox("Filter by Subject", options=subjects)
        with c3:
            filter_type = st.selectbox("Filter by Type", options=types)

        records = AssessmentService.list_assessments(
            student_id=filter_student,
            subject_code=filter_subject,
            assessment_type=filter_type,
            limit=500,
            db=db
        )

        if not records:
            st.info("No assessment records found matching the filters.")
        else:
            st.caption(f"Displaying {len(records)} assessment record(s).")
            display_rows = []
            for r in records:
                display_rows.append({
                    "Assessment ID": r.get("assessment_id"),
                    "Student ID": r.get("student_id"),
                    "Subject": r.get("subject_code"),
                    "Assessment Name": r.get("assessment_name"),
                    "Type": r.get("assessment_type"),
                    "Marks": r.get("marks"),
                    "Max Marks": r.get("max_marks"),
                    "Score (%)": r.get("percentage"),
                    "Date": r.get("assessment_date"),
                    "Remarks": r.get("remarks", "")
                })
            df = pd.DataFrame(display_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 2: CREATE ASSESSMENT
    # -------------------------------------------------------------------------
    with tab_add:
        st.subheader("Record New Assessment")
        all_subjects = SubjectService.list_subjects(limit=100, db=db)
        subject_options = [s["subject_code"] for s in all_subjects]

        with st.form("create_assessment_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_asm_id = st.text_input("Assessment ID *", placeholder="e.g. ASM2001").strip().upper()
                new_student_id = st.text_input("Student ID *", placeholder="e.g. STU1001").strip().upper()
                new_subject_code = st.selectbox("Subject Code *", options=subject_options if subject_options else ["None"])
                new_name = st.text_input("Assessment Name *", placeholder="e.g. Midterm Examination").strip()

            with c2:
                new_type = st.selectbox("Assessment Type *", options=ASSESSMENT_TYPES)
                new_marks = st.number_input("Marks Obtained *", min_value=0.0, max_value=500.0, value=20.0, step=0.5)
                new_max = st.number_input("Maximum Achievable Marks *", min_value=1.0, max_value=500.0, value=25.0, step=1.0)
                new_date = st.date_input("Assessment Date *", value=date.today())
                new_remarks = st.text_input("Remarks", placeholder="e.g. Good theoretical understanding").strip()

            calc_pct = round((new_marks / new_max) * 100.0, 2) if new_max > 0 else 0.0
            st.caption(f"Calculated Score: **{calc_pct}%**")

            submit_asm = st.form_submit_button("Record Assessment", type="primary")

            if submit_asm:
                if not new_asm_id or not new_student_id or not new_name:
                    st.error("Please fill in all mandatory fields (*).")
                elif new_marks > new_max:
                    st.error(f"Marks obtained ({new_marks}) cannot exceed maximum marks ({new_max}).")
                else:
                    payload = {
                        "assessment_id": new_asm_id,
                        "student_id": new_student_id,
                        "subject_code": new_subject_code,
                        "assessment_name": new_name,
                        "assessment_type": new_type,
                        "marks": float(new_marks),
                        "max_marks": float(new_max),
                        "assessment_date": str(new_date),
                        "remarks": new_remarks
                    }
                    success, msg, _ = AssessmentService.create_assessment(payload, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 3: EDIT ASSESSMENT (UPDATE)
    # -------------------------------------------------------------------------
    with tab_edit:
        st.subheader("Edit Assessment Record")
        search_edit_id = st.text_input("Enter Assessment ID to edit:", placeholder="e.g. ASM1001").strip().upper()

        if search_edit_id:
            asm_to_edit = AssessmentService.get_assessment_by_id(search_edit_id, db=db)
            if not asm_to_edit:
                st.warning(f"Assessment '{search_edit_id}' not found.")
            else:
                st.info(f"Editing Assessment `{search_edit_id}` for Student `{asm_to_edit['student_id']}` in `{asm_to_edit['subject_code']}`")
                with st.form("edit_asm_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        edit_name = st.text_input("Assessment Name", value=asm_to_edit.get("assessment_name", ""))
                        edit_type = st.selectbox(
                            "Assessment Type",
                            options=ASSESSMENT_TYPES,
                            index=ASSESSMENT_TYPES.index(asm_to_edit.get("assessment_type", "Quiz")) if asm_to_edit.get("assessment_type") in ASSESSMENT_TYPES else 0
                        )
                    with c2:
                        edit_marks = st.number_input("Marks Obtained", min_value=0.0, max_value=500.0, value=float(asm_to_edit.get("marks", 0.0)), step=0.5)
                        edit_max = st.number_input("Maximum Marks", min_value=1.0, max_value=500.0, value=float(asm_to_edit.get("max_marks", 100.0)), step=1.0)
                        edit_remarks = st.text_input("Remarks", value=asm_to_edit.get("remarks", ""))

                    updated_pct = round((edit_marks / edit_max) * 100.0, 2) if edit_max > 0 else 0.0
                    st.caption(f"Updated Score: **{updated_pct}%**")

                    save_asm = st.form_submit_button("Update Assessment", type="primary")

                    if save_asm:
                        if edit_marks > edit_max:
                            st.error(f"Marks obtained ({edit_marks}) cannot exceed maximum marks ({edit_max}).")
                        else:
                            up_payload = {
                                "assessment_name": edit_name,
                                "assessment_type": edit_type,
                                "marks": float(edit_marks),
                                "max_marks": float(edit_max),
                                "remarks": edit_remarks
                            }
                            success, msg, _ = AssessmentService.update_assessment(search_edit_id, up_payload, db=db)
                            if success:
                                st.success(f"✅ {msg}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 4: DELETE ASSESSMENT
    # -------------------------------------------------------------------------
    with tab_delete:
        st.subheader("Delete Assessment")
        del_asm_id = st.text_input("Enter Assessment ID to delete:", placeholder="e.g. ASM1001", key="del_asm_input").strip().upper()

        if del_asm_id:
            asm_rec = AssessmentService.get_assessment_by_id(del_asm_id, db=db)
            if not asm_rec:
                st.warning(f"Assessment '{del_asm_id}' not found.")
            else:
                st.warning(
                    f"Selected: **{asm_rec.get('assessment_name')}** for Student **{asm_rec.get('student_id')}** "
                    f"in Subject **{asm_rec.get('subject_code')}** (Score: {asm_rec.get('percentage')}%)."
                )
                confirm_del = st.checkbox(f"I confirm that I want to delete assessment {del_asm_id}.", value=False)
                if st.button("Delete Assessment Record", type="primary", disabled=not confirm_del):
                    success, msg = AssessmentService.delete_assessment(del_asm_id, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
