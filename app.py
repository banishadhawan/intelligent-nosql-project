"""
IntelliTrack: Intelligent Student Performance & Learning Analytics System
Primary Streamlit Application Entrypoint.
Coordinates database connectivity, sidebar navigation, dynamic thresholds, and page routing.
"""

import streamlit as st
from config import config
from database.connection import check_connection

# Page configuration
st.set_page_config(
    page_title=f"{config.APP_NAME} — Student Performance & Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, academic styling
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #1F2937;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.90rem !important;
        font-weight: 600 !important;
        color: #4B5563;
    }
    /* Tab Styling */
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    /* Sidebar header */
    .sidebar-header {
        text-align: center;
        padding-bottom: 12px;
        border-bottom: 1px solid #E5E7EB;
        margin-bottom: 16px;
    }
    .status-badge-connected {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-disconnected {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Database Health Verification
    is_connected, conn_msg = check_connection()

    # Sidebar Navigation & Settings
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-header">
                <h2 style="margin-bottom: 2px;">🎓 {config.APP_NAME}</h2>
                <p style="font-size: 0.85rem; color: #6B7280; margin-top: 0;">{config.APP_SUBTITLE}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Connection status badge
        if is_connected:
            st.markdown(f'<div class="status-badge-connected">● {conn_msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-badge-disconnected">● MongoDB Offline</div>', unsafe_allow_html=True)

        st.write("")

        # Page Selection
        nav_options = [
            "📊 Home Dashboard",
            "👨‍🎓 Student Management",
            "📚 Subject Management",
            "📝 Assessment & Marks",
            "⏱️ Attendance Tracking",
            "📈 Academic Analytics",
            "🧠 Intelligent Learning Insights",
            "💾 Dataset & Import/Export"
        ]

        selected_page = st.radio("Navigation Menu", options=nav_options, label_visibility="collapsed")

        st.markdown("---")
        st.subheader("⚙️ Configurable Academic Thresholds")
        st.caption("Adjust policy thresholds applied across analytics, dashboards, and at-risk diagnostics.")

        pass_threshold = st.slider(
            "Passing Marks Threshold (%)",
            min_value=30.0,
            max_value=60.0,
            value=config.PASS_MARKS_PERCENTAGE,
            step=1.0,
            help="Minimum percentage required to clear an assessment or subject."
        )

        low_perf_threshold = st.slider(
            "Low Performance Warning (%)",
            min_value=35.0,
            max_value=70.0,
            value=config.LOW_PERFORMANCE_THRESHOLD,
            step=1.0,
            help="Students with overall score below this are flagged for academic remediation."
        )

        low_att_threshold = st.slider(
            "Low Attendance Warning (%)",
            min_value=50.0,
            max_value=85.0,
            value=config.LOW_ATTENDANCE_THRESHOLD,
            step=1.0,
            help="Students with attendance below this percentage are flagged for attendance shortage."
        )

        late_weight = st.slider(
            "Late Attendance Credit Weight",
            min_value=0.0,
            max_value=1.0,
            value=config.LATE_ATTENDANCE_WEIGHT,
            step=0.1,
            help="Credit awarded for 'Late' lecture attendance (e.g. 0.5 = half session credit)."
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size: 0.78rem; color: #6B7280;">
                <b>System:</b> MongoDB 8.x + PyMongo<br>
                <b>UI:</b> Streamlit & Plotly<br>
                <b>Project:</b> Individual College Submission
            </div>
            """,
            unsafe_allow_html=True
        )

    # If database is offline, render friendly diagnostic instructions
    if not is_connected:
        st.error(f"❌ **Database Connection Error**: {conn_msg}")
        st.info(
            "**Troubleshooting Instructions for Windows:**\n\n"
            "1. Verify that MongoDB Community Server is installed.\n"
            "2. Open PowerShell or Command Prompt as Administrator and run:\n"
            "   ```cmd\n"
            "   net start MongoDB\n"
            "   ```\n"
            "3. If using MongoDB Atlas, update your `MONGODB_URI` inside `.env`."
        )
        return

    # Route to selected page
    if selected_page == "📊 Home Dashboard":
        from pages.dashboard import render_dashboard
        render_dashboard(
            pass_threshold=pass_threshold,
            low_perf_threshold=low_perf_threshold,
            low_att_threshold=low_att_threshold
        )

    elif selected_page == "👨‍🎓 Student Management":
        from pages.students import render_students_page
        render_students_page()

    elif selected_page == "📚 Subject Management":
        from pages.subjects import render_subjects_page
        render_subjects_page()

    elif selected_page == "📝 Assessment & Marks":
        from pages.assessments import render_assessments_page
        render_assessments_page()

    elif selected_page == "⏱️ Attendance Tracking":
        from pages.attendance import render_attendance_page
        render_attendance_page(late_weight=late_weight)

    elif selected_page == "📈 Academic Analytics":
        from pages.analytics import render_analytics_page
        render_analytics_page(
            pass_threshold=pass_threshold,
            low_perf_threshold=low_perf_threshold,
            low_att_threshold=low_att_threshold,
            late_weight=late_weight
        )

    elif selected_page == "🧠 Intelligent Learning Insights":
        from pages.insights import render_insights_page
        render_insights_page(
            pass_threshold=pass_threshold,
            low_perf_threshold=low_perf_threshold,
            low_att_threshold=low_att_threshold
        )

    elif selected_page == "💾 Dataset & Import/Export":
        from pages.data_management import render_data_management_page
        render_data_management_page()


if __name__ == "__main__":
    main()
