"""
Page E: Attendance Management
Provides complete CRUD capabilities for attendance tracking:
- Status categorization: Present, Late, Absent
- Application of standardized Late credit policy (0.5 weight)
- Duplicate entry prevention per student + subject + date
- Multi-dimensional query filters and audit tools
"""

import streamlit as st
import pandas as pd
from datetime import date
from services.attendance_service import AttendanceService
from services.subject_service import SubjectService
from models.attendance import ATTENDANCE_STATUSES
from database.connection import get_database
from config import config


def render_attendance_page(late_weight: float):
    st.markdown("## ⏱️ Attendance Tracking & Auditing")
    st.markdown(
        f"Record and audit student lecture presence. Late entries are awarded **{late_weight * 100}% credit** "
        f"({late_weight} session weight) under academic policy."
    )

    db = get_database()
    subjects = ["All Subjects"] + [s["subject_code"] for s in SubjectService.list_subjects(limit=100, db=db)]
    statuses = ["All Statuses"] + list(ATTENDANCE_STATUSES)

    tab_list, tab_add, tab_edit, tab_delete = st.tabs([
        "📋 Attendance Log & Audit",
        "➕ Mark Attendance",
        "✏️ Modify Entry",
        "🗑️ Delete Entry"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: HISTORY & AUDIT
    # -------------------------------------------------------------------------
    with tab_list:
        st.subheader("Attendance Records")
        c1, c2, c3 = st.columns(3)
        with c1:
            filter_student = st.text_input("Filter by Student ID", placeholder="e.g. STU1001", key="att_filter_stu").strip()
        with c2:
            filter_subject = st.selectbox("Filter by Subject", options=subjects, key="att_filter_sub")
        with c3:
            filter_status = st.selectbox("Filter by Status", options=statuses, key="att_filter_stat")

        records = AttendanceService.list_attendance(
            student_id=filter_student,
            subject_code=filter_subject,
            status=filter_status,
            limit=1000,
            db=db
        )

        if not records:
            st.info("No attendance records found matching the query filters.")
        else:
            # Metrics on filtered subset
            total_cnt = len(records)
            present_cnt = sum(1 for r in records if r.get("status") == "Present")
            late_cnt = sum(1 for r in records if r.get("status") == "Late")
            absent_cnt = sum(1 for r in records if r.get("status") == "Absent")
            weighted_score = (present_cnt * 1.0) + (late_cnt * late_weight)
            subset_pct = round((weighted_score / total_cnt) * 100.0, 2) if total_cnt > 0 else 0.0

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Filtered Sessions", total_cnt)
            m2.metric("Present", present_cnt)
            m3.metric("Late", late_cnt)
            m4.metric("Absent", absent_cnt)
            m5.metric("Weighted Rate", f"{subset_pct}%")

            st.write("")
            display_rows = []
            for r in records:
                display_rows.append({
                    "Student ID": r.get("student_id"),
                    "Subject": r.get("subject_code"),
                    "Date": r.get("attendance_date"),
                    "Status": r.get("status"),
                    "Remarks": r.get("remarks", "")
                })
            df = pd.DataFrame(display_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 2: MARK ATTENDANCE (CREATE)
    # -------------------------------------------------------------------------
    with tab_add:
        st.subheader("Mark Student Attendance")
        all_subjects = SubjectService.list_subjects(limit=100, db=db)
        sub_opts = [s["subject_code"] for s in all_subjects]

        with st.form("mark_attendance_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                stu_id = st.text_input("Student ID *", placeholder="e.g. STU1001").strip().upper()
                sub_code = st.selectbox("Subject Code *", options=sub_opts if sub_opts else ["None"])
            with c2:
                att_date = st.date_input("Attendance Date *", value=date.today())
                status = st.selectbox("Status *", options=ATTENDANCE_STATUSES)

            remarks = st.text_input("Remarks (Optional)", placeholder="e.g. Medical leave slip submitted").strip()
            submit_btn = st.form_submit_button("Record Attendance", type="primary")

            if submit_btn:
                if not stu_id or not sub_code:
                    st.error("Please provide both Student ID and Subject Code.")
                else:
                    payload = {
                        "student_id": stu_id,
                        "subject_code": sub_code,
                        "attendance_date": str(att_date),
                        "status": status,
                        "remarks": remarks
                    }
                    success, msg, _ = AttendanceService.create_attendance(payload, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 3: MODIFY ENTRY (UPDATE)
    # -------------------------------------------------------------------------
    with tab_edit:
        st.subheader("Modify Attendance Record")
        c1, c2, c3 = st.columns(3)
        with c1:
            u_stu = st.text_input("Student ID", placeholder="e.g. STU1001", key="u_att_stu").strip().upper()
        with c2:
            u_sub = st.selectbox("Subject Code", options=[s["subject_code"] for s in SubjectService.list_subjects(limit=100, db=db)], key="u_att_sub")
        with c3:
            u_date = st.date_input("Attendance Date", value=date.today(), key="u_att_date")

        if u_stu and u_sub:
            filter_q = {"student_id": u_stu, "subject_code": u_sub, "attendance_date": str(u_date)}
            existing = db[config.COLLECTION_ATTENDANCE].find_one(filter_q)
            if not existing:
                st.warning(f"No attendance entry found for Student `{u_stu}` in `{u_sub}` on `{u_date}`.")
            else:
                st.info(f"Existing Status: **{existing.get('status')}** | Remarks: '{existing.get('remarks', '')}'")
                with st.form("update_att_form"):
                    new_stat = st.selectbox("New Status", options=ATTENDANCE_STATUSES, index=ATTENDANCE_STATUSES.index(existing.get("status", "Present")))
                    new_rem = st.text_input("New Remarks", value=existing.get("remarks", ""))
                    save_att = st.form_submit_button("Update Status", type="primary")

                    if save_att:
                        up_payload = {"status": new_stat, "remarks": new_rem}
                        success, msg, _ = AttendanceService.update_attendance(u_stu, u_sub, str(u_date), up_payload, db=db)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 4: DELETE ENTRY
    # -------------------------------------------------------------------------
    with tab_delete:
        st.subheader("Delete Incorrect Attendance Entry")
        c1, c2, c3 = st.columns(3)
        with c1:
            d_stu = st.text_input("Student ID", placeholder="e.g. STU1001", key="d_att_stu").strip().upper()
        with c2:
            d_sub = st.selectbox("Subject Code", options=[s["subject_code"] for s in SubjectService.list_subjects(limit=100, db=db)], key="d_att_sub")
        with c3:
            d_date = st.date_input("Attendance Date", value=date.today(), key="d_att_date")

        if d_stu and d_sub:
            filter_q = {"student_id": d_stu, "subject_code": d_sub, "attendance_date": str(d_date)}
            existing = db[config.COLLECTION_ATTENDANCE].find_one(filter_q)
            if not existing:
                st.warning(f"No attendance entry found for Student `{d_stu}` in `{d_sub}` on `{d_date}`.")
            else:
                st.warning(f"Record found: **{existing.get('status')}** on {d_date} for student {d_stu}.")
                confirm_del = st.checkbox("I confirm that I want to delete this specific attendance log.", value=False)
                if st.button("Delete Attendance Record", type="primary", disabled=not confirm_del):
                    success, msg = AttendanceService.delete_attendance(d_stu, d_sub, str(d_date), db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
