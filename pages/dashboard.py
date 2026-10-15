"""
Page A: Home Dashboard
Displays executive academic metrics, dynamic Plotly charts, top-performing students,
and alert indicators computed directly from live MongoDB collections.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.analytics_service import AnalyticsService
from services.assessment_service import AssessmentService
from database.connection import get_database


def render_dashboard(pass_threshold: float, low_perf_threshold: float, low_att_threshold: float):
    st.markdown("## 📊 Executive Academic Dashboard")
    st.markdown("Live academic performance, attendance metrics, and learning indicators derived from MongoDB collections.")

    db = get_database()

    # 1. Fetch live system KPIs
    kpis = AnalyticsService.get_system_kpis(
        pass_threshold=pass_threshold,
        low_perf_threshold=low_perf_threshold,
        low_att_threshold=low_att_threshold,
        db=db
    )

    if kpis["total_students"] == 0:
        st.warning("⚠️ No student records detected in MongoDB. Please visit the **Dataset & System Management** page or run the seed script to populate data.")
        return

    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Registered Students", value=kpis["total_students"])
    with c2:
        st.metric(label="Enrolled Subjects", value=kpis["total_subjects"])
    with c3:
        st.metric(label="Logged Assessments", value=kpis["total_assessments"])
    with c4:
        st.metric(label="Attendance Logs", value=kpis["total_attendance"])

    st.write("")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric(label="Overall Marks Average", value=f"{kpis['overall_marks_avg']}%")
    with c6:
        st.metric(label="Overall Attendance", value=f"{kpis['overall_attendance_pct']}%")
    with c7:
        st.metric(label="Exam Pass Rate", value=f"{kpis['pass_rate']}%")
    with c8:
        st.metric(
            label="Support Required (At-Risk)",
            value=kpis["at_risk_count"],
            delta=f"Thresholds: <{low_perf_threshold}% marks, <{low_att_threshold}% att",
            delta_color="inverse"
        )

    st.markdown("---")

    # 2. Charts Row 1: Subject Performance & Attendance Distribution
    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.subheader("📚 Subject Performance Comparison")
        subject_perf = AnalyticsService.get_average_marks_by_subject(db=db)
        if subject_perf:
            df_sub = pd.DataFrame(subject_perf)
            fig_sub = px.bar(
                df_sub,
                x="subject_code",
                y="avg_percentage",
                color="avg_percentage",
                color_continuous_scale="Blues",
                text="avg_percentage",
                hover_data=["subject_name", "assessment_count"],
                labels={"subject_code": "Subject Code", "avg_percentage": "Avg Marks (%)"},
                height=350
            )
            fig_sub.update_traces(texttemplate="%{text}%", textposition="outside")
            fig_sub.add_hline(y=pass_threshold, line_dash="dot", line_color="red", annotation_text=f"Pass ({pass_threshold}%)")
            fig_sub.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_sub, use_container_width=True)
        else:
            st.info("No assessment records available to plot.")

    with col_chart2:
        st.subheader("⏱️ Overall Attendance Distribution")
        att_dist = AnalyticsService.get_attendance_distribution_by_status(db=db)
        if att_dist:
            df_att = pd.DataFrame(att_dist)
            color_map = {"Present": "#2ECC71", "Late": "#F39C12", "Absent": "#E74C3C"}
            fig_att = px.pie(
                df_att,
                names="status",
                values="count",
                color="status",
                color_discrete_map=color_map,
                hole=0.45,
                height=350
            )
            fig_att.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_att, use_container_width=True)
        else:
            st.info("No attendance records logged.")

    # 3. Charts Row 2: Monthly Trends & Class Comparison
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("📈 Monthly Performance Trends")
        trends = AnalyticsService.get_monthly_performance_trends(db=db)
        if trends:
            df_trends = pd.DataFrame(trends)
            fig_trend = px.line(
                df_trends,
                x="month",
                y="avg_percentage",
                markers=True,
                labels={"month": "Academic Month", "avg_percentage": "Average Marks (%)"},
                height=320
            )
            fig_trend.update_traces(line_color="#2980B9", line_width=3, marker=dict(size=8))
            fig_trend.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Insufficient longitudinal data for monthly trends.")

    with col_chart4:
        st.subheader("🏫 Class Performance & Attendance")
        class_comp = AnalyticsService.get_class_level_performance_comparison(pass_threshold=pass_threshold, db=db)
        if class_comp:
            df_class = pd.DataFrame(class_comp)
            fig_cls = go.Figure()
            fig_cls.add_trace(go.Bar(
                x=df_class["class_name"],
                y=df_class["avg_marks"],
                name="Avg Marks (%)",
                marker_color="#3498DB"
            ))
            fig_cls.add_trace(go.Bar(
                x=df_class["class_name"],
                y=df_class["avg_attendance"],
                name="Avg Attendance (%)",
                marker_color="#2ECC71"
            ))
            fig_cls.update_layout(
                barmode="group",
                height=320,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_cls, use_container_width=True)
        else:
            st.info("No class comparative metrics available.")

    st.markdown("---")

    # 4. Tables Row: Top Performers & Declining Performance Alerts
    col_top, col_alerts = st.columns(2)

    with col_top:
        st.subheader("🏆 Top Performing Students")
        top_students = AnalyticsService.get_top_students(limit=5, db=db)
        if top_students:
            df_top = pd.DataFrame(top_students)[["student_id", "name", "class_name", "overall_average", "assessment_count"]]
            df_top.rename(columns={
                "student_id": "Student ID",
                "name": "Full Name",
                "class_name": "Class",
                "overall_average": "Mean Score (%)",
                "assessment_count": "Assessments"
            }, inplace=True)
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No student assessments available.")

    with col_alerts:
        st.subheader("⚠️ Students with Declining Trajectory")
        declining = AnalyticsService.get_declining_students(min_assessments=3, decline_threshold=-5.0, db=db)
        if declining:
            df_dec = pd.DataFrame(declining[:5])[["student_id", "name", "class_name", "initial_average", "recent_average", "score_drop"]]
            df_dec.rename(columns={
                "student_id": "Student ID",
                "name": "Full Name",
                "class_name": "Class",
                "initial_average": "Baseline (%)",
                "recent_average": "Recent (%)",
                "score_drop": "Score Drop (%)"
            }, inplace=True)
            st.dataframe(df_dec, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No severe downward trajectories identified across active cohorts.")

    st.markdown("---")

    # 5. Recent Assessment Activity
    st.subheader("🕒 Recent Assessment Activity")
    recent_assessments = AssessmentService.list_assessments(limit=8, db=db)
    if recent_assessments:
        df_recent = pd.DataFrame(recent_assessments)[["assessment_id", "student_id", "subject_code", "assessment_name", "marks", "max_marks", "percentage", "assessment_date"]]
        df_recent.rename(columns={
            "assessment_id": "Assessment ID",
            "student_id": "Student ID",
            "subject_code": "Subject",
            "assessment_name": "Title",
            "marks": "Marks",
            "max_marks": "Max",
            "percentage": "Score (%)",
            "assessment_date": "Date"
        }, inplace=True)
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("No recent assessment submissions recorded.")
