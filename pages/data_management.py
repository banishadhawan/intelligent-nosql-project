"""
Page H: Dataset Import, Export & System Management
Provides row-level validated CSV import, CSV export for collections/analytics,
and database seeding & reset tools.
"""

import streamlit as st
import pandas as pd
from services.import_export_service import ImportExportService
from scripts.seed_data import seed_database
from database.connection import get_database
from config import config


def render_data_management_page():
    st.markdown("## 💾 Dataset Management, Import & Export")
    st.markdown(
        "Manage raw collection data: perform strict row-level validated CSV imports, "
        "export reports to CSV, or trigger reproducible database reseeding."
    )

    db = get_database()

    tab_import, tab_export, tab_seed = st.tabs([
        "📥 CSV Batch Import",
        "📤 CSV Data Export",
        "🌱 Database Seeder & Reset"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: CSV IMPORT WITH ROW-LEVEL VALIDATION
    # -------------------------------------------------------------------------
    with tab_import:
        st.subheader("Validate & Import Records from CSV")
        st.markdown(
            "Every row is strictly validated against domain schemas and database referential integrity. "
            "Invalid rows are rejected with explicit line-item diagnostic messages."
        )

        import_type = st.radio(
            "Select Target Entity:",
            options=["Students", "Assessments", "Attendance"],
            horizontal=True
        )

        # Sample templates
        if import_type == "Students":
            sample_csv = "student_id,name,email,class_name,enrollment_date,skills\nSTU2001,Pooja Saxena,pooja.saxena@example.edu,BTech-CSE-A,2026-08-10,\"Python, MongoDB\"\n"
            field_notes = "Required columns: `student_id`, `name`, `email`, `class_name`, `enrollment_date`. Optional: `skills`."
        elif import_type == "Assessments":
            sample_csv = "assessment_id,student_id,subject_code,assessment_name,assessment_type,marks,max_marks,assessment_date,remarks\nASM9001,STU1001,CS301,Lab Exam 1,Lab,28,30,2026-09-15,Good execution\n"
            field_notes = "Required columns: `assessment_id`, `student_id`, `subject_code`, `assessment_name`, `assessment_type`, `marks`, `max_marks`, `assessment_date`."
        else:
            sample_csv = "student_id,subject_code,attendance_date,status,remarks\nSTU1001,CS301,2026-09-20,Present,On time\n"
            field_notes = "Required columns: `student_id`, `subject_code`, `attendance_date`, `status` (Present, Absent, Late)."

        st.caption(field_notes)
        st.download_button(
            label=f"⬇️ Download Sample {import_type} CSV Template",
            data=sample_csv,
            file_name=f"sample_{import_type.lower()}_template.csv",
            mime="text/csv"
        )

        uploaded_file = st.file_uploader(f"Upload {import_type} CSV file:", type=["csv"])

        if uploaded_file is not None:
            # Preview dataframe
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.markdown(f"**Previewing {len(preview_df)} record(s) from uploaded file:**")
                st.dataframe(preview_df.head(10), use_container_width=True)

                skip_dupes = st.checkbox("Safely skip records with duplicate IDs that already exist in database", value=True)

                if st.button(f"Validate & Execute Import for {import_type}", type="primary"):
                    uploaded_file.seek(0)
                    with st.spinner("Validating rows and applying database operations..."):
                        if import_type == "Students":
                            result = ImportExportService.import_students_csv(uploaded_file, skip_duplicates=skip_dupes, db=db)
                        elif import_type == "Assessments":
                            result = ImportExportService.import_assessments_csv(uploaded_file, skip_duplicates=skip_dupes, db=db)
                        else:
                            result = ImportExportService.import_attendance_csv(uploaded_file, skip_duplicates=skip_dupes, db=db)

                    # Show summary
                    if result["inserted_count"] > 0:
                        st.success(f"✅ Successfully inserted {result['inserted_count']} valid record(s) into MongoDB.")

                    if result["error_count"] > 0:
                        st.error(f"⚠️ Encountered {result['error_count']} invalid row(s). These rows were rejected to maintain data integrity.")
                        error_rows = []
                        for err in result["errors"]:
                            error_rows.append({
                                "Row #": err["row"],
                                "Errors": "; ".join(err["errors"]),
                                "Raw Data": str(err["data"])
                            })
                        st.dataframe(pd.DataFrame(error_rows), use_container_width=True)
                    elif result["inserted_count"] == 0:
                        st.info("No new records inserted (all rows may have been skipped as duplicates or empty).")

            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")

    # -------------------------------------------------------------------------
    # TAB 2: CSV DATA EXPORT
    # -------------------------------------------------------------------------
    with tab_export:
        st.subheader("Export Clean Data & Analytical Reports to CSV")
        st.markdown("Download active database collections or aggregated summary tables directly in CSV format.")

        export_target = st.selectbox(
            "Select Data to Export:",
            options=[
                "Students Collection",
                "Subjects Collection",
                "Assessments Collection",
                "Attendance Collection"
            ]
        )

        collection_map = {
            "Students Collection": config.COLLECTION_STUDENTS,
            "Subjects Collection": config.COLLECTION_SUBJECTS,
            "Assessments Collection": config.COLLECTION_ASSESSMENTS,
            "Attendance Collection": config.COLLECTION_ATTENDANCE
        }

        col_name = collection_map[export_target]
        doc_count = db[col_name].count_documents({})
        st.write(f"Active documents in `{col_name}`: **{doc_count}**")

        if doc_count == 0:
            st.warning("Selected collection is empty.")
        else:
            csv_data = ImportExportService.export_collection_to_csv(col_name, db=db)
            st.download_button(
                label=f"⬇️ Download {export_target} (CSV)",
                data=csv_data,
                file_name=f"intellitrack_{col_name}.csv",
                mime="text/csv",
                type="primary"
            )

    # -------------------------------------------------------------------------
    # TAB 3: SEEDER & RESET
    # -------------------------------------------------------------------------
    with tab_seed:
        st.subheader("Reproducible Fictional Dataset Generator")
        st.markdown(
            "Generate academic records using the built-in deterministic seeder script. "
            "Generates 8 subjects, up to 150 students, ~1,500 assessments, and ~6,600 attendance logs."
        )

        c1, c2 = st.columns(2)
        with c1:
            dataset_mode = st.radio("Dataset Size Mode:", options=["Standard Full Dataset (150 students)", "Demo Dataset (30 students)"])
            seed_num = st.number_input("Random Seed (for reproducibility):", min_value=1, max_value=99999, value=42, step=1)

        with c2:
            st.markdown("**Reset Confirmation**")
            reset_confirm = st.checkbox("Clear existing collections before seeding (Wipe and Reset)", value=False)

        is_demo = ("Demo" in dataset_mode)
        stu_cnt = 30 if is_demo else 150

        if st.button("Generate & Seed Database Now", type="primary"):
            with st.spinner("Seeding database with reproducible fictional data..."):
                try:
                    seed_database(student_count=stu_cnt, reset=reset_confirm, demo=is_demo, seed_value=int(seed_num))
                    st.success("🎉 Database successfully seeded! Head over to the Dashboard or Analytics pages to explore.")
                    st.rerun()
                except Exception as err:
                    st.error(f"Error seeding database: {str(err)}")
