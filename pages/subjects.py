"""
Page C: Subject Management
Provides complete CRUD capabilities for academic subjects with validation,
referential checks, credit limits, and safe deletion prevention.
"""

import streamlit as st
import pandas as pd
from services.subject_service import SubjectService
from services.student_service import StudentService
from database.connection import get_database


def render_subjects_page():
    st.markdown("## 📚 Academic Subject Management")
    st.markdown("Manage curriculum subjects, credit values, course descriptions, and class allocations.")

    db = get_database()
    classes = ["All Classes"] + StudentService.get_classes_list(db=db)

    tab_list, tab_add, tab_edit, tab_delete = st.tabs([
        "📖 Course Catalog",
        "➕ Add New Subject",
        "✏️ Edit Subject Details",
        "🗑️ Delete Subject"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: CATALOG & SEARCH
    # -------------------------------------------------------------------------
    with tab_list:
        st.subheader("Curriculum Course Catalog")
        c1, c2 = st.columns([3, 1])
        with c1:
            search_query = st.text_input("🔍 Search by Subject Code, Title, or Description", placeholder="e.g. CS301 or NoSQL")
        with c2:
            selected_class = st.selectbox("Filter by Class Allocation", options=classes, key="sub_class_filter")

        subjects = SubjectService.list_subjects(search=search_query, class_filter=selected_class, db=db)

        if not subjects:
            st.info("No subjects found matching the criteria.")
        else:
            st.caption(f"Showing {len(subjects)} registered subject(s).")
            display_data = []
            for s in subjects:
                # Count assessments associated with this subject
                asm_count = db["assessments"].count_documents({"subject_code": s.get("subject_code")})
                display_data.append({
                    "Subject Code": s.get("subject_code"),
                    "Subject Name": s.get("subject_name"),
                    "Credits": s.get("credits"),
                    "Assigned Class": s.get("class_name"),
                    "Assessments Conducted": asm_count,
                    "Description": s.get("description")
                })
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 2: ADD SUBJECT (CREATE)
    # -------------------------------------------------------------------------
    with tab_add:
        st.subheader("Add New Academic Subject")
        with st.form("create_subject_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_code = st.text_input("Subject Code *", placeholder="e.g. CS305").strip().upper()
                new_name = st.text_input("Subject Title *", placeholder="e.g. Distributed Cloud Computing").strip()
                new_credits = st.number_input("Credits (1 - 10) *", min_value=1, max_value=10, value=4, step=1)

            with col_b:
                new_class = st.text_input("Assigned Class / Department *", placeholder="e.g. BTech-CSE-A").strip()
                new_desc = st.text_area("Course Description", placeholder="Topics, prerequisites, syllabus summary...").strip()

            submitted = st.form_submit_button("Create Subject", type="primary")

            if submitted:
                if not new_code or not new_name or not new_class:
                    st.error("Please fill in all mandatory fields (*).")
                else:
                    payload = {
                        "subject_code": new_code,
                        "subject_name": new_name,
                        "credits": int(new_credits),
                        "class_name": new_class,
                        "description": new_desc
                    }
                    success, msg, _ = SubjectService.create_subject(payload, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 3: EDIT SUBJECT (UPDATE)
    # -------------------------------------------------------------------------
    with tab_edit:
        st.subheader("Modify Existing Subject")
        all_subjects = SubjectService.list_subjects(limit=100, db=db)
        if not all_subjects:
            st.warning("No subjects available to edit.")
        else:
            sub_map = {f"{s['subject_code']} - {s['subject_name']}": s for s in all_subjects}
            selected_label = st.selectbox("Select subject to edit:", options=list(sub_map.keys()))
            subject_to_edit = sub_map[selected_label]

            with st.form("edit_subject_form"):
                st.info(f"Modifying Subject Code: `{subject_to_edit['subject_code']}` (Immutable)")
                c1, c2 = st.columns(2)
                with c1:
                    edit_name = st.text_input("Subject Title", value=subject_to_edit.get("subject_name", ""))
                    edit_credits = st.number_input(
                        "Credits",
                        min_value=1,
                        max_value=10,
                        value=int(subject_to_edit.get("credits", 4)),
                        step=1
                    )
                with c2:
                    edit_class = st.text_input("Assigned Class", value=subject_to_edit.get("class_name", ""))
                    edit_desc = st.text_area("Description", value=subject_to_edit.get("description", ""))

                save_btn = st.form_submit_button("Update Subject", type="primary")

                if save_btn:
                    update_payload = {
                        "subject_name": edit_name,
                        "credits": int(edit_credits),
                        "class_name": edit_class,
                        "description": edit_desc
                    }
                    success, msg, _ = SubjectService.update_subject(subject_to_edit["subject_code"], update_payload, db=db)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # -------------------------------------------------------------------------
    # TAB 4: DELETE SUBJECT (DELETE with referential safety)
    # -------------------------------------------------------------------------
    with tab_delete:
        st.subheader("Delete Subject")
        all_subjects = SubjectService.list_subjects(limit=100, db=db)
        if not all_subjects:
            st.warning("No subjects available to delete.")
        else:
            del_map = {f"{s['subject_code']} - {s['subject_name']}": s for s in all_subjects}
            selected_del_label = st.selectbox("Select subject to remove:", options=list(del_map.keys()), key="sub_del_select")
            target_sub = del_map[selected_del_label]
            target_code = target_sub["subject_code"]

            asm_cnt = db["assessments"].count_documents({"subject_code": target_code})
            att_cnt = db["attendance"].count_documents({"subject_code": target_code})

            if asm_cnt > 0 or att_cnt > 0:
                st.warning(
                    f"⚠️ **Referential Warning**: Subject **{target_code}** is currently referenced by "
                    f"**{asm_cnt} assessment(s)** and **{att_cnt} attendance record(s)**.\n\n"
                    "By default, deleting this subject is blocked to preserve academic integrity. "
                    "If you choose cascade deletion, all associated assessments and attendance logs will be permanently deleted."
                )
                cascade_allowed = st.checkbox("Force cascade delete: permanently remove this subject and all its related assessments and attendance", value=False)
            else:
                st.info(f"Subject **{target_code}** has no active assessment or attendance dependencies.")
                cascade_allowed = False

            confirm_check = st.checkbox(f"I confirm that I want to delete subject {target_code}.", value=False)

            if st.button("Delete Subject", type="primary", disabled=not confirm_check):
                success, msg = SubjectService.delete_subject(target_code, cascade=cascade_allowed, db=db)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
