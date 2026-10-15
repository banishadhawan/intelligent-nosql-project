"""
Page G: Intelligent Learning Insights
Explainable, rule-based educational analytics and student diagnostics:
- Multi-factor At-Risk Student Identification
- Empirical Evidence & Transparent Justifications
- Individual Student Diagnostic & Chronological Trajectory
- Tailored Actionable Recommendations
- Classroom Vulnerabilities and Curriculum Strengths
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from services.insights_service import InsightsService
from services.student_service import StudentService
from database.connection import get_database


def render_insights_page(pass_threshold: float, low_perf_threshold: float, low_att_threshold: float):
    st.markdown("## 🧠 Intelligent Learning Insights & Diagnostics")
    st.markdown(
        "Deterministic, explainable educational indicators synthesized from live MongoDB records. "
        "Provides actionable recommendations backed by transparent empirical evidence."
    )

    st.info(
        "ℹ️ **Explainability Notice**: IntelliTrack uses deterministic, rule-based heuristics based on academic "
        "pedagogy, not black-box probabilistic ML predictions. Every recommendation clearly identifies the exact "
        "underlying marks, dates, or attendance statistics that triggered it."
    )

    db = get_database()

    tab_at_risk, tab_diagnostic, tab_classroom = st.tabs([
        "🚨 At-Risk Student Identification",
        "🔬 Individual Student Diagnostic",
        "🏫 Classroom & Curriculum Insights"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: AT-RISK STUDENT IDENTIFICATION
    # -------------------------------------------------------------------------
    with tab_at_risk:
        st.subheader("At-Risk Student Triage")
        st.markdown(
            f"Students are screened against three criteria: "
            f"**Low Marks (< {low_perf_threshold}%)**, **Low Attendance (< {low_att_threshold}%)**, "
            f"and **Declining Score Trajectory (>= 5% drop)**."
        )

        at_risk_list = InsightsService.get_at_risk_students(
            low_perf_threshold=low_perf_threshold,
            low_att_threshold=low_att_threshold,
            db=db
        )

        if not at_risk_list:
            st.success("🎉 No students currently flagged as at-risk under the active thresholds.")
        else:
            crit_count = sum(1 for s in at_risk_list if s["risk_tier"] == "Critical Risk")
            mod_count = sum(1 for s in at_risk_list if s["risk_tier"] == "Moderate Risk")
            warn_count = sum(1 for s in at_risk_list if s["risk_tier"] == "Early Warning")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Flagged", len(at_risk_list))
            m2.metric("Critical Risk", crit_count)
            m3.metric("Moderate Risk", mod_count)
            m4.metric("Early Warning", warn_count)

            st.write("")
            st.markdown("### Flagged Students & Empirical Justifications")

            for item in at_risk_list:
                tier = item["risk_tier"]
                header_icon = "🔴" if tier == "Critical Risk" else ("🟠" if tier == "Moderate Risk" else "🔵")
                title = f"{header_icon} **{item['name']}** (`{item['student_id']}`) — {item['class_name']} [{tier}]"

                with st.expander(title, expanded=(tier == "Critical Risk")):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("**Underlying Metrics:**")
                        m_val = f"{item['marks_avg']}%" if item['marks_avg'] is not None else "N/A"
                        a_val = f"{item['attendance_pct']}%" if item['attendance_pct'] is not None else "N/A"
                        d_val = f"-{item['score_drop']}%" if item['score_drop'] is not None else "N/A"
                        st.write(f"- Marks Average: **{m_val}** (Target: {low_perf_threshold}%)")
                        st.write(f"- Attendance Rate: **{a_val}** (Target: {low_att_threshold}%)")
                        st.write(f"- Trajectory Score Drop: **{d_val}**")

                    with c2:
                        st.markdown("**Identified Concerns:**")
                        for r in item["reasons"]:
                            st.markdown(f"- ⚠️ {r}")

    # -------------------------------------------------------------------------
    # TAB 2: INDIVIDUAL STUDENT DIAGNOSTIC
    # -------------------------------------------------------------------------
    with tab_diagnostic:
        st.subheader("Deep-Dive Student Diagnostic")
        students = StudentService.list_students(limit=1000, db=db)
        if not students:
            st.warning("No students available in the system.")
        else:
            student_dict = {f"{s['student_id']} - {s['name']} ({s['class_name']})": s["student_id"] for s in students}
            selected_student_label = st.selectbox("Select a student to generate diagnostic dossier:", options=list(student_dict.keys()))
            selected_student_id = student_dict[selected_student_label]

            diagnostic = InsightsService.get_student_diagnostic(
                student_id=selected_student_id,
                pass_threshold=pass_threshold,
                low_perf_threshold=low_perf_threshold,
                low_att_threshold=low_att_threshold,
                db=db
            )

            if "error" in diagnostic:
                st.error(diagnostic["error"])
            else:
                # Top summary cards
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Overall Average", f"{diagnostic['overall_average']}%")
                c2.metric("Attendance Rate", f"{diagnostic['attendance_stats']['percentage']}%")
                c3.metric("Weak Subjects", len(diagnostic["weak_subjects"]))
                c4.metric("Chronological Trend", diagnostic["trend_status"])

                st.write("")

                # Subject-wise bar chart
                if diagnostic["subject_breakdown"]:
                    st.subheader("Subject-Wise Performance Breakdown")
                    df_sub = pd.DataFrame(diagnostic["subject_breakdown"])
                    fig_sub = px.bar(
                        df_sub,
                        x="subject_name",
                        y="avg_percentage",
                        color="avg_percentage",
                        color_continuous_scale="RdYlGn",
                        text="avg_percentage",
                        labels={"subject_name": "Subject Title", "avg_percentage": "Student Mean (%)"},
                        range_y=[0, 105],
                        height=350
                    )
                    fig_sub.update_traces(texttemplate="%{text}%", textposition="outside")
                    fig_sub.add_hline(y=pass_threshold, line_dash="dash", line_color="red", annotation_text=f"Pass ({pass_threshold}%)")
                    fig_sub.add_hline(y=low_perf_threshold, line_dash="dot", line_color="orange", annotation_text=f"Threshold ({low_perf_threshold}%)")
                    st.plotly_chart(fig_sub, use_container_width=True)

                # Chronological score progression chart
                if diagnostic["chronological_assessments"]:
                    st.subheader("Chronological Assessment Trajectory")
                    df_chrono = pd.DataFrame(diagnostic["chronological_assessments"])
                    fig_chrono = px.line(
                        df_chrono,
                        x="assessment_date",
                        y="percentage",
                        markers=True,
                        hover_data=["assessment_name", "subject_code"],
                        labels={"assessment_date": "Date", "percentage": "Score (%)"},
                        title=f"Assessment Scores Over Time — Status: {diagnostic['trend_status']}",
                        height=320
                    )
                    fig_chrono.update_traces(line_color="#2980B9", line_width=3, marker=dict(size=8))
                    st.plotly_chart(fig_chrono, use_container_width=True)

                # Actionable Recommendations
                st.subheader("📋 Tailored Learning Recommendations")
                for rec in diagnostic["recommendations"]:
                    sev = rec["severity"]
                    if sev == "High":
                        st.error(f"**[{rec['category']}]**: {rec['message']}")
                    elif sev == "Medium":
                        st.warning(f"**[{rec['category']}]**: {rec['message']}")
                    else:
                        st.success(f"**[{rec['category']}]**: {rec['message']}")

    # -------------------------------------------------------------------------
    # TAB 3: CLASSROOM & CURRICULUM INSIGHTS
    # -------------------------------------------------------------------------
    with tab_classroom:
        st.subheader("Classroom Vulnerabilities & Curriculum Strengths")
        classes = ["All Classes"] + StudentService.get_classes_list(db=db)
        chosen_class = st.selectbox("Select Class / Cohort:", options=classes)

        class_insights = InsightsService.get_classroom_insights(
            class_name=chosen_class,
            pass_threshold=pass_threshold,
            db=db
        )

        lowest = class_insights["lowest_performing_subjects"]
        highest = class_insights["highest_performing_subjects"]

        c_low, c_high = st.columns(2)

        with c_low:
            st.markdown("### ⚠️ Subjects with Lowest Class Averages")
            if lowest:
                for idx, item in enumerate(lowest, 1):
                    st.error(
                        f"**{idx}. {item['subject_name']} (`{item['subject_code']}`)**\n\n"
                        f"- Class Average: **{item['avg_percentage']}%**\n\n"
                        f"- Pass Rate: **{item['pass_rate']}%** ({item['total_assessments']} assessments conducted)\n\n"
                        f"*Pedagogical suggestion: Review mid-semester syllabus pacing and organize remedial lab sessions.*"
                    )
            else:
                st.info("No assessment metrics available.")

        with c_high:
            st.markdown("### 🌟 Subjects with Strongest Class Performance")
            if highest:
                for idx, item in enumerate(highest, 1):
                    st.success(
                        f"**{idx}. {item['subject_name']} (`{item['subject_code']}`)**\n\n"
                        f"- Class Average: **{item['avg_percentage']}%**\n\n"
                        f"- Pass Rate: **{item['pass_rate']}%** ({item['total_assessments']} assessments conducted)\n\n"
                        f"*Pedagogical suggestion: Introduce advanced capstone challenges or competitive problem sets.*"
                    )
            else:
                st.info("No assessment metrics available.")
