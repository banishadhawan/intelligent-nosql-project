"""
Page F: Academic Analytics
Interactive visual dashboard powered by 12 genuine MongoDB aggregation pipelines.
Includes interactive Plotly charts, cohort comparisons, and granular tables.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.analytics_service import AnalyticsService
from database.connection import get_database


def render_analytics_page(pass_threshold: float, low_perf_threshold: float, low_att_threshold: float, late_weight: float):
    st.markdown("## 📈 Academic Analytics & Aggregation Pipelines")
    st.markdown("Genuine multi-stage MongoDB aggregation pipelines executing live on student collections.")

    db = get_database()

    tab_overview, tab_leaderboards, tab_pass_rates, tab_attendance, tab_watchlists = st.tabs([
        "📊 Subject & Class Analytics",
        "🏆 Top Students & Trends",
        "🎯 Pass Rates & Type Breakdown",
        "⏱️ Attendance Analytics",
        "⚠️ Academic Support Watchlists"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SUBJECT & CLASS PERFORMANCE (Pipelines 1, 2, 12)
    # -------------------------------------------------------------------------
    with tab_overview:
        st.subheader("Subject-Wise Academic Performance (Pipeline 1)")
        sub_perf = AnalyticsService.get_average_marks_by_subject(db=db)
        if sub_perf:
            df_sub = pd.DataFrame(sub_perf)
            c1, c2 = st.columns([3, 2])
            with c1:
                fig1 = px.bar(
                    df_sub,
                    x="subject_code",
                    y="avg_percentage",
                    color="avg_percentage",
                    color_continuous_scale="Viridis",
                    text="avg_percentage",
                    hover_data=["subject_name", "assessment_count"],
                    labels={"subject_code": "Course Code", "avg_percentage": "Avg Score (%)"},
                    title="Average Marks % by Subject"
                )
                fig1.update_traces(texttemplate="%{text}%", textposition="outside")
                fig1.add_hline(y=pass_threshold, line_dash="dash", line_color="red", annotation_text=f"Pass Threshold ({pass_threshold}%)")
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                st.dataframe(df_sub, use_container_width=True, hide_index=True)
        else:
            st.info("No assessment data available.")

        st.markdown("---")
        st.subheader("Class-Level Comparative Analysis (Pipelines 2 & 12)")
        class_comp = AnalyticsService.get_class_level_performance_comparison(pass_threshold=pass_threshold, db=db)
        if class_comp:
            df_cls = pd.DataFrame(class_comp)
            fig_cls = go.Figure()
            fig_cls.add_trace(go.Bar(x=df_cls["class_name"], y=df_cls["avg_marks"], name="Marks Average (%)", marker_color="#3498DB"))
            fig_cls.add_trace(go.Bar(x=df_cls["class_name"], y=df_cls["avg_attendance"], name="Attendance Rate (%)", marker_color="#2ECC71"))
            fig_cls.add_trace(go.Bar(x=df_cls["class_name"], y=df_cls["pass_rate"], name="Pass Rate (%)", marker_color="#9B59B6"))
            fig_cls.update_layout(barmode="group", title="Class Performance, Attendance & Pass Rates", height=400)
            st.plotly_chart(fig_cls, use_container_width=True)
            st.dataframe(df_cls, use_container_width=True, hide_index=True)
        else:
            st.info("No class data available.")

    # -------------------------------------------------------------------------
    # TAB 2: TOP STUDENTS & TRENDS (Pipelines 3, 6, 11)
    # -------------------------------------------------------------------------
    with tab_leaderboards:
        st.subheader("Top 10 Students by Overall Average (Pipeline 3)")
        top_students = AnalyticsService.get_top_students(limit=10, db=db)
        if top_students:
            df_top = pd.DataFrame(top_students)
            fig_top = px.bar(
                df_top,
                x="name",
                y="overall_average",
                color="overall_average",
                color_continuous_scale="Purples",
                text="overall_average",
                hover_data=["student_id", "class_name", "assessment_count"],
                labels={"name": "Student", "overall_average": "Mean Marks (%)"},
                title="Dean's List / Top 10 Performers"
            )
            fig_top.update_traces(texttemplate="%{text}%", textposition="outside")
            st.plotly_chart(fig_top, use_container_width=True)
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No student scores available.")

        st.markdown("---")
        st.subheader("Longitudinal Monthly Performance Trends (Pipeline 6)")
        monthly = AnalyticsService.get_monthly_performance_trends(db=db)
        if monthly:
            df_month = pd.DataFrame(monthly)
            fig_month = px.line(
                df_month,
                x="month",
                y="avg_percentage",
                markers=True,
                labels={"month": "Month", "avg_percentage": "Average Marks (%)"},
                title="Mean Performance Across Calendar Months"
            )
            fig_month.update_traces(line_color="#E67E22", line_width=4, marker=dict(size=10))
            st.plotly_chart(fig_month, use_container_width=True)
            st.dataframe(df_month, use_container_width=True, hide_index=True)
        else:
            st.info("No chronological trend data found.")

    # -------------------------------------------------------------------------
    # TAB 3: PASS RATES & BREAKDOWN (Pipelines 4 & 5)
    # -------------------------------------------------------------------------
    with tab_pass_rates:
        st.subheader(f"Subject Pass Rates (Threshold >= {pass_threshold}%) (Pipeline 4)")
        pass_data = AnalyticsService.get_pass_rate_by_subject(pass_threshold=pass_threshold, db=db)
        if pass_data:
            df_pass = pd.DataFrame(pass_data)
            fig_pass = px.bar(
                df_pass,
                x="subject_code",
                y="pass_rate",
                color="pass_rate",
                color_continuous_scale="Teal",
                text="pass_rate",
                hover_data=["subject_name", "passed_count", "failed_count", "total_assessments"],
                labels={"subject_code": "Course", "pass_rate": "Pass Rate (%)"},
                title="Subject Pass Rate %"
            )
            fig_pass.update_traces(texttemplate="%{text}%", textposition="outside")
            st.plotly_chart(fig_pass, use_container_width=True)
            st.dataframe(df_pass, use_container_width=True, hide_index=True)
        else:
            st.info("No pass rate analytics available.")

        st.markdown("---")
        st.subheader("Assessment Type & Volume Breakdown by Subject (Pipeline 5)")
        breakdown = AnalyticsService.get_assessment_count_and_avg_by_subject(db=db)
        if breakdown:
            df_bk = pd.DataFrame(breakdown)
            fig_bk = px.bar(
                df_bk,
                x="subject_code",
                y="count",
                color="assessment_type",
                barmode="stack",
                hover_data=["avg_percentage"],
                labels={"subject_code": "Subject", "count": "Submissions Count", "assessment_type": "Type"},
                title="Assessment Counts Grouped by Subject & Category"
            )
            st.plotly_chart(fig_bk, use_container_width=True)
            st.dataframe(df_bk, use_container_width=True, hide_index=True)
        else:
            st.info("No breakdown data available.")

    # -------------------------------------------------------------------------
    # TAB 4: ATTENDANCE ANALYTICS (Pipelines 7 & 8)
    # -------------------------------------------------------------------------
    with tab_attendance:
        st.subheader("Attendance Status Breakdown (Pipeline 8)")
        att_dist = AnalyticsService.get_attendance_distribution_by_status(db=db)
        if att_dist:
            df_ad = pd.DataFrame(att_dist)
            c1, c2 = st.columns([1, 1])
            with c1:
                fig_ad = px.pie(
                    df_ad,
                    names="status",
                    values="count",
                    hole=0.4,
                    color="status",
                    color_discrete_map={"Present": "#2ECC71", "Late": "#F39C12", "Absent": "#E74C3C"},
                    title="Campus Attendance Distribution"
                )
                st.plotly_chart(fig_ad, use_container_width=True)
            with c2:
                st.dataframe(df_ad, use_container_width=True, hide_index=True)
        else:
            st.info("No attendance distribution logs.")

        st.markdown("---")
        st.subheader(f"Student-Wise Attendance Percentages (Late Weight: {late_weight}) (Pipeline 7)")
        att_students = AnalyticsService.get_attendance_percentage_per_student(late_weight=late_weight, db=db)
        if att_students:
            df_as = pd.DataFrame(att_students)
            st.caption(f"Showing attendance rates for {len(df_as)} students.")
            st.dataframe(df_as, use_container_width=True, hide_index=True)
        else:
            st.info("No student attendance data found.")

    # -------------------------------------------------------------------------
    # TAB 5: UNDERPERFORMING WATCHLISTS (Pipelines 9, 10, 11)
    # -------------------------------------------------------------------------
    with tab_watchlists:
        st.subheader(f"Students with Low Marks (< {low_perf_threshold}%) (Pipeline 9)")
        low_marks = AnalyticsService.get_students_with_low_marks(threshold=low_perf_threshold, db=db)
        if low_marks:
            df_lm = pd.DataFrame(low_marks)
            st.dataframe(df_lm, use_container_width=True, hide_index=True)
        else:
            st.success(f"No students have an average below {low_perf_threshold}%.")

        st.markdown("---")
        st.subheader(f"Students with Low Attendance (< {low_att_threshold}%) (Pipeline 10)")
        low_att = AnalyticsService.get_students_with_low_attendance(threshold=low_att_threshold, late_weight=late_weight, db=db)
        if low_att:
            df_la = pd.DataFrame(low_att)
            st.dataframe(df_la, use_container_width=True, hide_index=True)
        else:
            st.success(f"No students have attendance below {low_att_threshold}%.")

        st.markdown("---")
        st.subheader("Students with Declining Chronological Scores (Pipeline 11)")
        declining = AnalyticsService.get_declining_students(min_assessments=3, decline_threshold=-5.0, db=db)
        if declining:
            df_dec = pd.DataFrame(declining)
            st.dataframe(df_dec, use_container_width=True, hide_index=True)
        else:
            st.success("No declining performance trajectories detected.")
