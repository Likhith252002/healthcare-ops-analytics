import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

from utils.db_connection import get_connection

# Page configuration
st.set_page_config(
    page_title="Healthcare Operations Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def show_home_page():
    """Display home page with overview metrics"""

    # Header
    st.markdown('<h1 class="main-header">🏥 Healthcare Operations Analytics</h1>', unsafe_allow_html=True)
    st.markdown("### Real-time insights into hospital operations")
    st.markdown("---")

    # Fetch summary metrics
    conn = get_connection()

    # Total patients
    df_patients = pd.read_sql("SELECT COUNT(*) as count FROM dim_patients WHERE is_current = TRUE", conn)
    total_patients = df_patients['count'].iloc[0]

    # Total encounters
    df_encounters = pd.read_sql("SELECT COUNT(*) as count FROM fact_encounters", conn)
    total_encounters = df_encounters['count'].iloc[0]

    # Departments
    df_departments = pd.read_sql("SELECT COUNT(*) as count FROM dim_departments", conn)
    total_departments = df_departments['count'].iloc[0]

    # Bed events tracked
    df_beds = pd.read_sql("""
        SELECT COUNT(DISTINCT bed_number) as count
        FROM fact_bed_events
        WHERE event_type = 'bed_assigned'
    """, conn)
    active_beds = df_beds['count'].iloc[0]

    conn.close()

    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Patients",
            value=f"{total_patients:,}",
            delta="Active records"
        )

    with col2:
        st.metric(
            label="Total Encounters",
            value=f"{total_encounters:,}",
            delta="All time"
        )

    with col3:
        st.metric(
            label="Departments",
            value=f"{total_departments}",
            delta="Active"
        )

    with col4:
        st.metric(
            label="Bed Events",
            value=f"{active_beds:,}",
            delta="Tracked"
        )

    st.markdown("---")

    # Quick stats section
    st.subheader("📊 Quick Statistics")

    col1, col2 = st.columns(2)

    with col1:
        # Recent admissions chart
        conn = get_connection()
        df_daily = pd.read_sql("""
            SELECT
                DATE(admission_date) as date,
                COUNT(*) as admissions
            FROM fact_encounters
            WHERE admission_date > CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(admission_date)
            ORDER BY date
        """, conn)
        conn.close()

        if not df_daily.empty:
            fig = px.line(
                df_daily,
                x='date',
                y='admissions',
                title='Daily Admissions (Last 30 Days)',
                labels={'date': 'Date', 'admissions': 'Admissions'}
            )
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Admission type distribution
        conn = get_connection()
        df_types = pd.read_sql("""
            SELECT
                admission_type,
                COUNT(*) as count
            FROM fact_encounters
            GROUP BY admission_type
            ORDER BY count DESC
        """, conn)
        conn.close()

        if not df_types.empty:
            fig = px.pie(
                df_types,
                values='count',
                names='admission_type',
                title='Admission Types',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Feature highlights
    st.subheader("✨ Dashboard Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        **📊 Operations Dashboard**
        - Real-time KPIs
        - Department metrics
        - Bed utilization
        - Wait times
        """)

    with col2:
        st.success("""
        **👥 Patient Analytics**
        - Demographics
        - Visit patterns
        - Readmission tracking
        - Length of stay
        """)

    with col3:
        st.warning("""
        **🔮 Predictions**
        - Readmission risk
        - LOS forecasting
        - Capacity planning
        - Trend analysis
        """)


# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=🏥", width=150)
    st.title("Healthcare Operations")
    st.markdown("---")

    page = st.selectbox(
        "Navigation",
        ["🏠 Home", "📊 Dashboard", "👥 Patients", "🏥 Departments", "📈 Analytics", "🔮 Predictions"]
    )

    st.markdown("---")
    st.markdown("### Data Freshness")

    # Get last update time
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(created_at) FROM fact_encounters")
    last_update = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    if last_update:
        st.info(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M')}")

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    Healthcare Operations Analytics Platform

    **Features:**
    - Real-time metrics
    - Patient analytics
    - Department performance
    - Predictive models
    """)

# Main content based on page selection
if page == "🏠 Home":
    show_home_page()
elif page == "📊 Dashboard":
    from pages.operations import show_operations_dashboard
    show_operations_dashboard()
elif page == "👥 Patients":
    st.title("👥 Patient Analytics")
    st.info("Coming soon!")
elif page == "🏥 Departments":
    st.title("🏥 Department Performance")
    st.info("Coming soon!")
elif page == "📈 Analytics":
    st.title("📈 Advanced Analytics")
    st.info("Coming soon!")
elif page == "🔮 Predictions":
    st.title("🔮 Predictive Models")
    st.info("Coming soon!")
